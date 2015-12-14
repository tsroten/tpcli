# -*- coding: utf-8 -*-
"""Config parser class for tp."""

from __future__ import print_function
try:
    import configparser
    ConfigParser = configparser.ConfigParser
except ImportError:
    import ConfigParser as configparser
    ConfigParser = configparser.RawConfigParser
    ConfigParser.read_file = ConfigParser.readfp
    configparser.DEFAULTSECT = 'default'
import logging
import os
import sys

is_python3 = True if sys.version_info[0] == 3 else False

try:
    basestring
except NameError:
    basestring = str

_UNSET = object()


class TpConfig(ConfigParser):
    """A customized config parser for tp."""

    pkg_dir = os.path.dirname(os.path.realpath(__file__))
    tp_dir = os.path.join(os.path.expanduser('~'), '.tp')
    default_conf = os.path.join(pkg_dir, 'defaults.conf')
    system_confs = (
        '/etc/tp.conf',
        '/etc/tp/tp.conf',
        '/usr/local/etc/tp.conf',
        '/usr/local/etc/tp/tp.conf',
    )
    user_confs = (
        os.path.join(os.path.expanduser('~'), '.config/tp/tp.conf'),
        os.path.join(os.path.expanduser('~'), '.config/tp.conf'),
        os.path.join(os.path.expanduser('~'), '.tp.conf'),
        os.path.join(tp_dir, 'tp.conf')
    )

    def __init__(self, *args, **kwargs):
        """Read the tp config files.

        :param str template: The template (config section) to use. This
            is a period-delmited hierarchical template name. E.g.: foo.bar
        """

        self._logger = logging.getLogger(__name__)

        template = kwargs.pop('template', None)

        # Configure ConfigParser keyword arguments.
        kwargs['allow_no_value'] = True
        if is_python3 is True:
            kwargs['interpolation'] = None
            kwargs['default_section'] = 'default'

        ConfigParser.__init__(self, *args, **kwargs)

        self.template = template

        try:
            self.log('info', 'Reading default configuration file.')
            self.read_file(open(self.default_conf))
        except configparser.Error:
            self.log('warning', 'Unable to read default configuration file.')
        try:
            self.log('info', 'Reading system configuration files.')
            self.read_system_confs = self.read(self.system_confs)
        except configparser.Error:
            self.log('warning', 'Unable to read system configuration files.')
        try:
            self.log('info', 'Reading user configuration files.')
            self.read_user_confs = self.read(self.user_confs)
        except configparser.Error:
            self.log('warning', 'Unable to read user configuration files.')

    def log(self, level, message):
        """Log a message using the logger or stderr.

        If no parent logger exists and the level is not 'info' or 'debug',
        then the message is written to stderr.

        If a parent logger exists, then the message is logged using the logger.

        :param str level: The logging level for the message, e.g. 'debug' or
            'warning'.
        :param str message: The message to log.
        """

        if self._logger.parent.name == 'root':
            if level.lower() not in ('info', 'debug'):
                print(message, file=sys.stderr)
            return

        level = getattr(logging, level.upper())
        self._logger.log(level, message)

    def get(self, section, option, vars=None, fallback=_UNSET):
        """Get an option's value from the config parser.

        If *vars* is provided, it is checked for *option* first.

        If the option isn't found in *vars* or in the config parser, then
        *fallback* is returned if it is provided.

        :param str section: The section to look in.
        :param str option: The option to look up.
        :param dict vars: A dictionary to check first for *option*.
        :param fallback: The value to return if option isn't found.
        """

        if vars is not None and option in vars:
            return vars[option]

        try:
            return ConfigParser.get(self, section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not _UNSET:
                return fallback
            else:
                raise

    def _get_conv(self, section, option, conv, vars=None, fallback=_UNSET):
        """Get an option's value and convert the value."""
        try:
            return conv(self.get(section, option, vars=vars))
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is _UNSET:
                raise
            return fallback

    if is_python3 is False:
        BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                          '0': False, 'no': False, 'false': False,
                          'off': False}

        def _convert_to_boolean(self, value):
            """Convert *value* to a boolean value."""

            if value.lower() not in self.BOOLEAN_STATES:
                raise ValueError('Not a boolean: %s' % value)
            return self.BOOLEAN_STATES[value.lower()]

    def getint(self, section, option, vars=None, fallback=_UNSET):
        """Get an option's value and cast it as an integer."""
        return self._get_conv(section, option, int, vars=vars,
                              fallback=fallback)

    def getfloat(self, section, option, vars=None, fallback=_UNSET):
        """Get an option's value and cast it as a float."""
        return self._get_conv(section, option, float, vars=vars,
                              fallback=fallback)

    def getboolean(self, section, option, vars=None, fallback=_UNSET):
        """Get an option's value and cast it as a boolean."""
        return self._get_conv(section, option, self._convert_to_boolean,
                              vars=vars, fallback=fallback)

    def get_from_template(self, option, cast=_UNSET, vars=None,
                          fallback=_UNSET):
        """Get an option from the config's assigned template.

        :param str option: The option to look up.
        :param cast: The type to cast the option as.
        :param dict vars: A dictionary to check first for *option*.
        :param fallback: The return value if the option is not found.

        :returns: The value converted according to *cast*.
        """

        self.log('debug', 'Getting from template:\n'
                          '\ttemplate: {0}\n'
                          '\toption: {1}\n'
                          '\tcast: {2}'
                          .format(self.template, option, cast))

        if cast == 'bool':
            get = self.getboolean
        elif cast == 'int':
            get = self.getint
        elif cast == 'float':
            get = self.getfloat
        elif cast == 'list':
            get = self.getlist
        elif cast == 'str' or cast is _UNSET:
            get = self.get
        else:
            raise ValueError('Unexpected value for cast: {0}'.format(cast))

        # Get the option's value starting with the child template and
        # then chekcing any parent templates until it is found.
        sections = self.template.split('.')
        for n in range(len(sections), 0, -1):
            section = '.'.join(sections[:n])
            try:
                return get(section, option, vars=vars)
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass

        try:
            return get('default', option, vars=vars)
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass

        if fallback is not _UNSET:
            return fallback

        # Raise the most appropriate error message.
        get(self.template, option)

    def getlist(self, section, option, vars=None, fallback=_UNSET):
        """Get a value and cast it as a list.

        :param str section: The section to look in.
        :param str option: The option name to look up.
        :param vars: Dictionary to look for option in first.
        :param fallback: The return value if the option is not found.

        :returns: The value cast as a list.
        """

        value = self.get_from_template(option, vars=vars, fallback=_UNSET)
        if isinstance(value, list):
            return value
        elif not isinstance(value, basestring):
            raise TypeError('Value cannot be converted to a list.')
        return [v.strip() for v in value.split(',')]
