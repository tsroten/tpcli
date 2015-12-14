# -*- coding: utf-8 -*-
"""List entity command for tp."""

from json import dumps

import click
from tabulate import tabulate, TableFormat, Line, DataRow

from tp.api import ApiError
from tp.app import TpApp
from tp.formatter import Formatter

tp_tablefmt = TableFormat(
    lineabove=Line("", "─", "  ", ""),
    linebelowheader=Line("", u"─", "  ", ""),
    linebetweenrows=None,
    linebelow=Line("", u"─", "  ", ""),
    headerrow=DataRow("", "  ", ""),
    datarow=DataRow("", "  ", ""),
    padding=0,
    with_header_hide=["lineabove", "linebelow"]
)


@click.option('-j', '--json', is_flag=True, default=False,
              help='Output the response in JSON.')
@click.option('-t', '--table', metavar='<table_name>',
              help='Table style to use for output.')
@click.option('-p', '--pager', is_flag=True, default=None,
              help='Output results via a pager.')
@click.option('-r', '--reverse', is_flag=True, default=None,
              help='Sort results in reverse order.')
@click.option('-s', '--sort', metavar='<field>',
              help='Field to sort results by.')
@click.option('-o', '--offset', type=click.IntRange(0, None),
              metavar='<int>', help='Number to offset results by.')
@click.argument('filters', nargs=-1, required=False,
                metavar=('[<number>] [<entity>...<entity>] '
                         '[<field><operator><value>]'))
@click.command('ls', options_metavar='[<options>]',
               help='List Targetprocess entities.')
def main(filters, pager, table, json, **data):
    """Command-line entry point for the list command."""

    app = TpApp(__name__)

    # Search Tp for entities matching user's filters.
    try:
        results = app.list(filters, **data)
    except ApiError as e:
        click.secho('{0}: {1}'.format(e.status, e.message), fg='red')
        exit(1)

    if json is True:
        indent_step = app.config.get_from_template('indent', cast='int')
        click.echo(dumps(results, indent=indent_step))
        exit(0)

    if pager is None:
        pager = app.config.get_from_template('pager', cast='bool')
    if table is None:
        table = app.config.get_from_template('table')
    if table == 'tp_table':
        table = tp_tablefmt

    # Get the output format.
    _fields = app.config.get_from_template('fields', cast='list')
    fields = app.format_fields_for_output(_fields)
    headers = app.config.get_from_template('headers', cast='list')
    if len(headers) != len(fields):
        click.secho('Warning: The number of headings and fields do not match.',
                    fg='yellow')

    # Generate the output data for each entity.
    Formatter.date_format = app.config.get_from_template('date')
    output_data = []
    for entity in results:
        row = [field.format(**Formatter(entity)) for field in fields]
        output_data.append(row)

    # Add a line between the command and table output.
    click.echo()

    option_echo = click.echo_via_pager if pager is True else click.echo
    out = tabulate(output_data, headers=headers, tablefmt=table)
    option_echo(out)

    # Provide a little space at the end of the list.
    click.echo()
