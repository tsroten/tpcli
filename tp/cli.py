# -*- coding: utf-8 -*-
"""The Click-based, command-line interface for tp."""

import imp
import logging
import os

import click

from ._version import __version__ as VERSION


class TpGroup(click.Group):
    """The tp CLI commands.

    This class dynamically loads tp-defined and user-defined subcommands.
    Any Python module it finds with the prefix "cmd_", that defines the
    function main(), will be added to the command-line interface.
    """

    tp_dir = os.path.dirname(os.path.abspath(__file__))

    cmd_dirs = (
        os.path.join(tp_dir, 'commands'),
        os.path.join(os.path.expanduser('~'), '.tp', 'commands'),
    )

    def __init__(self, *args, **kwargs):
        """Load commands from tp.commands and any user extensions."""
        self._logger = logging.getLogger(__name__)
        self._logger.debug('Loading tp CLI commands.')
        commands = self.get_commands()
        self._logger.debug('Finished loading tp CLI commands.')
        return super(TpGroup, self).__init__(*args, commands=commands,
                                             **kwargs)

    def get_commands(self):
        """Get a dictionary of all command names mapped to their callables."""
        commands = {name: self.get_command_callable(name, filename) for
                    name, filename in self.get_command_files()}
        return commands

    def get_command_callable(self, name, filename, function='main'):
        """Get a command's callable object.

        :param str name: The name of the command.
        :param str filename: The full path to the command file.
        :param str function: The entry point for the command. E.g., a
            function named 'main'.
        """

        self._logger.debug("Loading module '{0}'.".format(filename))
        module = imp.load_source(name, filename)
        try:
            return getattr(module, function)
        except AttributeError:
            self._logger.error("Command '{0}' does not have a function named "
                               "'{1}'. Unable to register command in file "
                               "'{2}'.".format(name, function, filename))
            return None

    def get_command_files(self):
        """Get a list of all command names and paths.

        :returns: a list of tuples (name, filename).
        """

        cmds = []
        for _dir in self.cmd_dirs:
            self._logger.debug("Looking for commands in '{0}'.".format(_dir))
            try:
                for fname in os.listdir(_dir):
                    if (fname.endswith('.py') and
                            fname.startswith('cmd_')):
                        self._logger.debug("Found command file '{0}'."
                                           .format(fname))
                        cmds.append((fname[4:-3], os.path.join(_dir, fname)))
            except OSError:
                continue
        return cmds


@click.command(cls=TpGroup, help='A usable UI for Targetprocess',
               context_settings=dict(help_option_names=['-h', '--help']),
               options_metavar='[<options>]',
               subcommand_metavar='<command> [<args>]')
@click.version_option(VERSION, message='%(prog)s %(version)s')
def main():
    """The entry point for the tp CLI."""
    pass
