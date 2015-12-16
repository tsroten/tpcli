# -*- coding: utf-8 -*-
"""Show entity command for tp."""

from collections import OrderedDict
from json import dumps
from textwrap import fill

import click
import click.utils
import pyperclip

from tp.api import ApiError
from tp.app import TpApp
from tp.formatter import Formatter


def format_output(s, current_indent):
    """Format the specified string for output.

    :param str s: The string to format.
    :param int current_indent: The current indent level.

    :returns: The formatted string.
    """

    indent = ' ' * current_indent

    # Calculate the output width.
    w = click.get_terminal_size()[0]
    size = min(max(w - 20, min(80, w)) - current_indent, 130)

    # Wrap the paragraphs so lines are not longer than the calculated width.
    s = '\n'.join([fill(paragraph, size) for paragraph in s.split('\n')])

    # Indent each newline.
    s = indent + s.replace('\n', '\n' + indent)

    return s


def get_parent_comment(child_map, parent_id):
    """Get the parent comment's OrderedDict.

    :param OrderedDict child_map: The parent-child relationship mapping.
    :param str parent_id: The parent comment's ID.

    :returns: The parent comment's mapping.
    :rtype: OrderedDict
    """

    for child in child_map.values():
        if child[0] == parent_id:
            return child[1]
        parent = get_parent_comment(child[1], parent_id)
        if parent is not None:
            return parent


def print_comments(comments, child_map, base_indent, indent_step):
    """Print a list of comments.

    :param list comments: The comments to print.
    :param OrderedDict child_map: A mapping of parent-child relationships.
    :param int base_indent: The base comment indent level.
    :param int indent_step: The value to increment the indent by.
    """

    for index, comment in child_map.items():
        indent = base_indent
        print_comment(comments[index], indent, indent_step)
        indent += indent_step
        print_comments(comments, comment[1], indent, indent_step)


def print_comment(comment, indent, indent_step):
    """Print a comment to stdout.

    :param dict comment: A TP comment.
    :param int indent: The desired base indent level.
    :param int indent_step: The value to increment the indent by.
    """

    # Output the comment's header.
    header_indent = format_output('', indent)
    click.echo(header_indent, nl=False)
    fcomment = Formatter(comment)
    header = '{0} on {1}'.format(
        fcomment['Owner']['Name'],
        fcomment.get('CreateDate'))
    header_out = format_output(header, 0)
    click.secho(header_out, bold=True, underline=True)

    # Output the comment's description.
    indent += indent_step
    data = fcomment['Description']
    data_out = format_output(data, indent)
    click.echo(data_out)


@click.option('-j', '--json', is_flag=True, default=False,
              help='Output the response in JSON.')
@click.option('--no-comments', is_flag=True, help="Don't output comments.",
              default=None)
@click.option('--comments', is_flag=True, help="Output comments.",
              default=None)
@click.option('-b', '--browser', is_flag=True, default=None,
              help='Open the entity in your web browser.')
@click.option('-c', '--copy', is_flag=True, default=None,
              help="Copy the entity's URL to the clipboard.")
@click.argument('id', metavar='<id>')
@click.command(options_metavar='[<options>]',
               help='Show a Targetprocess entity.')
def main(id, copy, browser, comments, no_comments, json):
    """Command-line entry point for the show command."""

    app = TpApp(__name__)

    indent_step = app.config.get_from_template('indent', cast='int')

    # Decide whether or not to display comments.
    if no_comments is None and comments is None:
        display_comments = app.config.get_from_template('comments',
                                                        cast='bool')
    elif comments is None:
        display_comments = not no_comments
    else:
        display_comments = comments

    # Handle the various URL options.
    if browser is True or copy is True:
        url = app.get_url(id)
        if browser is True:
            exit(click.launch(url))
        if copy is True:
            pyperclip.copy(url)
            click.echo('URL copied to clipboard.')
            exit(0)

    # Define the fields to be included in the API response.
    include = (
        'Comments[CreateDate,Description,Id,Owner,ParentId]',
        'CreateDate',
        'Description',
        'EntityState[Name]',
        'EntityType[Name]',
        'Id',
        'LastStateChangeDate',
        'Name',
        'Owner[Firstname,LastName]',
    )

    # Get the requested entity and display any errors.
    try:
        entity = app.show(id, raw=json, include=include)
    except ApiError as e:
        click.echo('{0}: {1}'.format(e.status, e.message))
        exit(1)

    if json is True:
        click.echo(dumps(entity, indent=indent_step))
        exit(0)

    # Configure the Formatter class and wrap the entity.
    Formatter.date_format = app.config.get_from_template('date')
    fentity = Formatter(entity)
    current_indent = 0

    click.echo()

    # Output the entity title.
    name_out = format_output(fentity['Name'], current_indent)
    click.secho(name_out, bold=True, underline=True)

    # Output the entity details.
    byline = '{0} #{1} by {2} on {3}'.format(
        fentity['EntityType']['Name'],
        fentity['Id'],
        fentity['Owner']['Name'],
        fentity.get('CreateDate'))
    byline_out = format_output(byline, current_indent)
    click.echo(byline_out)
    state_out = format_output(fentity['EntityState']['Name'], current_indent)
    click.secho(state_out, nl=False, bold=True)
    state_date = ' as of {0}'.format(fentity.get('LastStateChangeDate'))
    state_date_out = format_output(state_date, current_indent)
    click.echo(state_date_out)

    click.echo()

    # Output the entity description.
    current_indent += indent_step
    description_out = format_output(fentity['Description'], current_indent)
    click.echo(description_out)

    # Only display comments if the user requested it.
    if display_comments is True:
        current_indent += indent_step
        comments = fentity.get('Comments.Items', sort_by='CreateDate')

        # Map comment parent-child relationships.
        child_map = OrderedDict()
        for index, comment in enumerate(comments):
            if comment['ParentId'] is None:
                child_map[index] = (comment['Id'], OrderedDict())
            else:
                parent = get_parent_comment(child_map, comment['ParentId'])
                if parent is None:
                    parent = child_map
                parent[index] = (comment['Id'], OrderedDict())

        print_comments(comments, child_map, current_indent, indent_step)
