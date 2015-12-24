# -*- coding: utf-8 -*-
"""A parser for entity filters."""

import re


class FilterParser(object):
    """A parser for the filter statements used in tp."""

    #: Regular expression for matching a condition.
    #: E.g., "name:foo" (name contains 'foo').
    condition_re = '([a-z\.\-]+)\s*?([<>:=!][=]?)\s*?(.+)'

    #: These are convenience mappings for the various operators used to filter
    #: TP entities.
    operator_map = {
        '>': 'gt',
        '<': 'lt',
        '>=': 'gte',
        '<=': 'lte',
        ':': 'contains',
        '~=': 'contains',
        '=': 'eq',
        '==': 'eq',
        '!=': 'ne'
    }

    #: These are convenience mappings for the various fields used when
    #: filtering TP entities.
    field_map = {
        'assigned': {str: 'assigneduser.login'},
        'created': {str: 'createdate'},
        'email': {str: 'owner.email'},
        'iteration': {int: 'iteration.id', str: 'iteration.name'},
        'lastcommented': {str: 'lastcommentdate'},
        'login': {str: 'owner.login'},
        'modified': {str: 'modifydate'},
        'owner': {str: 'owner.login'},
        'priority': {int: 'priority.id', str: 'priority.name'},
        'process': {int: 'project.process.id', str: 'project.process.name'},
        'project': {int: 'project.id', str: 'project.name'},
        'release': {int: 'release.id', str: 'release.name'},
        'state': {int: 'entitystate.id', str: 'entitystate.name'},
        'tag': {str: 'tags'},
    }

    def __init__(self, templates=None):
        """Store the names of any possible templates.

        :arg list templates: A list of possible template names."""

        self.templates = templates or []

    def _parse_conditional(self, condition):
        """Parse a filter conditional.

        :arg str condition: The condition to parse.
        :returns: The condition formatted for the TP API or False if
            the condition wasn't valid.
        """

        condition = condition.lower()

        m = re.match(self.condition_re, condition, re.I)

        if m is None:
            return False

        condition_name = m.group(1)
        operator = self.operator_map.get(m.group(2), m.group(2))
        value = m.group(3)

        if condition_name in self.field_map:
            value_type = int if value.isdigit() else str
            condition_name = self.field_map[condition_name][value_type]

        # Manually handle the operator when "null" is the value.
        if value == 'null' and operator in ('eq', 'ne'):
            operator = 'is' if operator == 'eq' else 'is not'

        # Surround non-null values in quotes.
        if value != 'null':
            value = "'{0}'".format(value)

        return "({0} {1} {2})".format(condition_name, operator, value)

    def parse_filter(self, filters):
        """Parse a tp filter.

        :param list filter: A list of the filter items.
        :returns: A dict of the parsed filter.
        """

        values = {
            'entity': [],
            'number': [],
            'template': [],
            'where': [],
        }

        for filter_text in filters:
            # Rewrite tags as TP entity field queries.
            if filter_text.startswith('+'):
                filter_text = 'tagobjects.name:{0}'.format(filter_text[1:])

            _filter = self._parse_conditional(filter_text)

            # If the filter was a conditional, add to the 'where' list.
            if _filter is not False:
                values['where'].append(_filter)
                continue

            if filter_text in self.templates:
                values['template'].append(filter_text)
                continue

            # Try to convert the filter to a number and fallback to using it
            # as a TP entity.
            try:
                values['number'].append(int(filter_text))
            except ValueError:
                values['entity'].append(filter_text)

        return values
