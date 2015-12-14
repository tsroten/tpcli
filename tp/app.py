# -*- coding: utf-8 -*-
"""The tp command-line app class."""

import logging
from os.path import expanduser
import re

import click

from tp import api
from tp.config import TpConfig
from tp.parser import FilterParser


class TpApp(object):

    def __init__(self, cmd, **configs):
        """Set up the tp app object.

        :param str cmd: The calling tp command, e.g. 'ls'.
        :param str subdomain: The TP subdomain to use.
        :param str token: The authentication token to use.
        :param str username: The username to use.
        :param str password: The password to use.
        :param str user_id: The user's ID.
        """

        # Read the default, system, and user config files.
        self.config = TpConfig(template=cmd)

        # Get the app's root logger.
        log_file = expanduser(self.config.get('app', 'log_file'))
        log_format = self.config.get('app', 'log_format')
        log_date_format = self.config.get('app', 'log_date_format',
                                          fallback=None)
        log_level = self.config.get('app', 'log_level').upper()
        self._logger = logging.getLogger('tp')
        self._formatter = logging.Formatter(fmt=log_format,
                                            datefmt=log_date_format)
        self._handler = logging.FileHandler(log_file)
        self._handler.setFormatter(self._formatter)
        self._logger.addHandler(self._handler)
        self._logger.setLevel(getattr(logging, log_level))

        # Get the authentication details.
        subdomain = self.config.get('auth', 'subdomain', vars=configs)
        token = self.config.get('auth', 'token', vars=configs, fallback=None)
        username = self.config.get('auth', 'username', vars=configs,
                                   fallback=None)
        password = self.config.get('auth', 'password', vars=configs,
                                   fallback=None)
        user_id = self.config.get('auth', 'user_id', vars=configs,
                                  fallback=None)

        # Prompt for any missing authentication details.
        if subdomain is None:
            subdomain = click.prompt('What is the TargetProcess subdomain your'
                                     ' organization uses?', prompt_suffix=' ')
        if username is None:
            username = click.prompt('What is your TargetProcess user name?',
                                    prompt_suffix=' ')
        if password is None and token is None:
            password = click.prompt('What is your TargetProcess password?',
                                    hide_input=True, prompt_suffix=' ')

        # Create a TP API interface.
        self.api = api.TpApi(subdomain, token=token, username=username,
                             password=password, user_id=user_id)

        # Store the calling command's name.
        self.cmd = cmd

    def get_url(self, id):
        """Get the URL for entity *id*."""
        entity = api.General(api=self.api, Id=id)
        return entity.get_url()

    def show(self, id, raw=False, **options):
        """Get TP entity by ID.

        :param id: The ID of the entity to lookup.
        :param bool raw: Whether or not to return the raw JSON response.
        """

        data = self._options_to_api_data(**options)
        where = 'Id eq {0}'.format(id)
        assignables = api.fetch(self.api, api.Assignable, raw=raw,
                                where=where, **data)
        if raw is True:
            return assignables.json()

        if len(assignables) == 0:
            click.secho("Uh oh! That ID doesn't seem to match anything.",
                        fg='red')
            exit(1)
        elif len(assignables) > 1:
            click.secho('Hmm. That ID matches more than one result. '
                        "Let's use the first one.", fg='yellow')

        assignable = assignables[0]

        return assignable

    def _parse_filter(self, filters):
        """Parse the filter statements.

        :param list filters: The filters to parse.
        """

        possible_templates = self.get_templates()
        parser = FilterParser(possible_templates)
        values = parser.parse_filter(filters)

        # Format the where statement correctly.
        if values['where']:
            values['where'] = ' and '.join(values['where'])

        # Get the absolute template names.
        for index, template in enumerate(values['template']):
            abs_template = self.get_template_name(template)
            values['template'][index] = abs_template

        # Store the template.
        if len(values['template']) > 1:
            click.secho('Error: More than one template found in the filter '
                        'query.', fg='red')
            exit(1)
        elif values['template']:
            values['template'] = values['template'].pop()
        else:
            values['template'] = self.cmd

        # Store the number.
        if len(values['number']) > 1:
            click.secho('Error: More than one integer found in filter '
                        'query.', fg='red')
            exit(1)
        elif values['number']:
            values['number'] = values['number'].pop()

        return values

    def list(self, filters, raw=False, **options):
        """Get TP entities based on a filter.

        :param list filters: A list of filters to apply to the search.
        :param bool raw: Whether or not to return the raw JSON response.
        :param int number: The number of results to return.
        :param int offset: The number to offset the results by.
        :param str sort: The field to sort the results by.
        :param bool reverse: Whether or not to reverse the sort order.

        :returns: A list of matching entities.
        :rtype: tp.api.Assignable
        """

        # Parse the filters.
        self._logger.debug('Parsing filter.')
        filter_values = self._parse_filter(filters)

        # Store the template.
        self.config.template = filter_values['template']

        # Store the parsed values.
        entities = filter_values['entity']
        if filter_values['where']:
            options['where'] = filter_values['where']
        if filter_values['number']:
            options['number'] = filter_values['number']

        # Read filters from the config file if none were provided.
        if 'where' not in options or not options['where']:
            self._logger.debug('Parsing template filter.')
            template_filters = self.config.get_from_template('filter', 'list',
                                                             fallback=[])
            template_filter_values = self._parse_filter(template_filters)
            if template_filter_values['where']:
                options['where'] = template_filter_values['where']

        # Read the entities from the config file if none were provided.
        if not entities:
            entities = self.config.getlist(self.config.template, 'entities')
        entities = ','.join(["'{0}'".format(entity) for entity in entities])
        _where = '(EntityType.Name in ({0}))'.format(entities)
        if 'where' in options:
            options['where'] = '{0} and {1}'.format(_where, options['where'])
        else:
            options['where'] = _where

        # Get default options if none were provided.
        opts = (('number', 'int'), ('offset', 'int'), ('sort', 'str'),
                ('reverse', 'bool'))
        for option, cast in opts:
            if options.get(option) is None:
                options[option] = self.config.get_from_template(option,
                                                                cast=cast)

        # Generate fields to include from fields that will be displayed.
        fields = self.config.get_from_template('fields')
        options['include'] = self._fields_to_attrs(fields)

        # Convert the tp options to TP API options.
        data = self._options_to_api_data(**options)

        assignables = api.fetch(self.api, api.Assignable, raw=raw, **data)

        if raw is True:
            return assignables.json()

        return assignables

    def _fields_to_attrs(self, fields):
        """Format *fields* as a list of attributes.

        For example, if fields = '{Id}, {Owner.FirstName} {Owner.LastName}'
        The return value is ['Id', 'Owner.FirstName', 'Owner.LastName']
        """

        return re.findall('\{([a-z\.]+)\}', fields, re.I)

    def _options_to_api_data(self, **options):
        """Convert a tp options dict to a TP API dict.

        Option names are converted to their TP API equivalents.

        :param dict options: A dict of tp options.
        :returns: The TP API options for use in an API request.
        :rtype: dict
        """

        data = {}
        for option, value in options.items():
            if option == 'sort':
                reverse = options['reverse']
                option = 'orderBy' + ('' if reverse is False else 'Desc')
                data[option] = value
            elif option == 'number':
                data['take'] = value
            elif option == 'offset':
                data['skip'] = value
            elif option in ('include', 'exclude'):
                if options[option] is None:
                    continue
                attrs = self._attributes_to_dict(options[option])
                rattrs = self._format_attributes_for_request(attrs)
                data[option] = rattrs
            elif option in ('reverse', ):
                continue
            else:
                data[option] = value
        return data

    def _attributes_to_dict(self, attributes):
        """Convert a list of attributes to a hierarchical dict.

        For example: ['Foo', 'Bar', 'Foo.Bar', 'Foo.Foobar', 'Foo.Bar.Foo']
        becomes: {'Bar': {}, 'Foo': {'Foobar': {}, 'Bar': {'Foo': {}}}}

        This is used with _format_attributes_for_request() to get a list
        of attributes ready for a TP API request.

        :param dict attributes: A list of attributes.
        :returns: A dict of the attributes.
        """

        d = {}
        for attr in attributes:
            _attributes = attr.split('.')
            _d = d
            for _attr in _attributes:
                if _attr not in _d:
                    _d[_attr] = {}
                _d = _d[_attr]
        return d

    def _format_attributes_for_request(self, attributes, basename=''):
        """Format a dict of attributes in TP API style for a request.

        *attributes* should be the output of _attributes_to_dict().

        :param dict attributes: The attributes to format.
        :param str basename: The basename for the attributes, if any.
        :returns: A string of attributes.
        """

        fields = []
        for key, value in attributes.items():
            if bool(attributes[key]) is True:
                f = self._format_attributes_for_request(attributes[key], key)
                fields.append(f)
            else:
                fields.append(key)
        return '{0}[{1}]'.format(basename, ','.join(fields))

    def get_templates(self):
        """Get a list of possible template names for the current command."""
        template_base = '{0}.'.format(self.cmd)
        templates = []
        for section in self.config.sections():
            if section.startswith(template_base):
                templates.append(section[len(template_base):])
        return templates

    def get_template_name(self, template):
        """Get the full template name for a given template.

        For example, if the 'list' command is run and 'foo' is passed to this
        method, then 'list.foo' will be returned.

        :param str template: A period-delimited template hierarchy, e.g.
            foo.bar
        :returns: The full template name.
        :rtype: str
        """

        return '{0}.{1}'.format(self.cmd, template)

    def format_fields_for_output(self, fields):
        """Convert attribute-style fields to dict-style.

        For example, ['Foo.Bar', 'Foo'] will be returned as
        ['Foo[Bar]', 'Foo'].

        :param list fields: The list of fields to format.
        :returns: The formatted fields.
        :rtype: list
        """

        for index, field in enumerate(fields):
            ffield = re.sub('(?<=[a-zA-Z])\.([a-zA-Z_\-]+)', '[\g<1>]', field)
            fields[index] = ffield
        return fields
