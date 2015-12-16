# -*- coding: utf-8 -*-
"""An output formatter for a Tp API entity's data."""

from datetime import datetime, timedelta
import re

import html2text

try:
    basestring
except NameError:
    basestring = str


class Formatter(dict):
    """A output formatter class for Tp API entities.

    Tp entity objects can be passed to this class to create a formatter object
    that automatically transforms certain fields.

    For example:

        > entity = api.fetch(....)
        > formatter = Formatter(entity)
        > print(formatter['Description'])
        ... [prints a Markdown-formatted description]
    """

    # A sane, default date format. This can be overridden on the class-level by
    # client code if needed.
    date_format = '%Y-%m-%d %H:%M:%S'

    def __init__(self, entity, default=''):
        """Store the Tp entity.

        :param TpEntity entity: The Tp entity this formatter should wrap.
        :param default: A default, fallback value to be returned when a key is
            not found. Defaults to a blank string so that it can easily be
            combined with other string when outputted.
        """

        self.default_value = default
        super(Formatter, self).__init__(entity)

    def _override_key(self, key):
        """Override a key if it wasn't found.

        This is used to provide shortcuts, e.g., key 'name' for first and
        last name.

        :param str key: The requested key.
        :returns: The value for the new key.
        :raises KeyError: The key was not found.
        """

        if (key.lower() == 'name' and
                'FirstName' in self and
                'LastName' in self):
            value = '{0} {1}'.format(self['FirstName'], self['LastName'])
        else:
            raise KeyError("'{0}'".format(key))

        return value

    def _format_date(self, date, format):
        """Format a TP-provided *date* to match *format* codes.

        See the Python documentation on the various date format codes:
        https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        """

        date_match = re.match('/Date\((\d+)-(\d{2})\d{2}\)/', date)
        td = timedelta(hours=-int(date_match.group(2)),
                       milliseconds=int(date_match.group(1)))
        dt = datetime(1970, 1, 1)
        fdate = (dt + td).strftime(format)
        return fdate

    def _transform_value(self, key, value, fmt_option):
        """Transform the given value.

        :param str key: The corresponding key.
        :param value: The value to transform.
        :param fmt_option: A format option to be used in the transformation,
            e.g., a date format string.
        :returns: The transformed value.
        """

        if isinstance(value, dict):
            return Formatter(value)
        elif not isinstance(value, basestring):
            return value
        elif value.startswith('/Date('):
            return self._format_date(value, fmt_option or self.date_format)

        if key.lower() == 'description' and 'data-mention' in value:
            value = re.sub('<span data-mention="[\w@.]+">([\w\s]+)</span>',
                           '@\g<1>', value)
        if key.lower() == 'description':
            # Remove the divs that TP uses for line breaks.
            value = re.sub('<div>[\s\xa0]*</div>', '', value, re.UNICODE)
            value = html2text.html2text(value, bodywidth=0)

        return value

    def __getitem__(self, key, raw=False, fmt_option=None):
        """Get a value from the entity with key/value transformations.

        :param str key: The key to lookup.
        :param bool raw: Whether or not to transform the value.
        :param str fmt_option: A format option to be passed to the transformer.
        :returns: The value.
        """

        try:
            value = super(Formatter, self).__getitem__(key)
        except KeyError:
            try:
                value = self._override_key(key)
            except KeyError:
                return self.default_value

        if raw is False:
            value = self._transform_value(key, value, fmt_option)
        return value

    def get(self, key, default=None, raw=False, sort_by=None, fmt_option=None):
        """Get *key* with correct formatting.

        :param str key: The key to look up. *key* can be a period-delimited
            string of multiple, nested keys.
        :param default: The default value to return if *key* is not found.
        :param bool raw: Whether or not to return the raw value.
        :param str sort_by: The field to sort by (if the return value is an
            iterable.
        :param fmt_option: A format option that is passed to the value
            transformer.
        :returns: The value assigned to *key*.
        """

        keys = key.split('.')
        try:
            value = self
            for k in keys:
                value = value.__getitem__(k, raw=raw, fmt_option=fmt_option)
        except KeyError:
            value = default

        if sort_by is not None:
            try:
                value = sorted(value, key=lambda item: item[sort_by])
            except TypeError:
                pass

        return value
