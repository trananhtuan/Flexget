from __future__ import unicode_literals, division, absolute_import
from builtins import *  # noqa pylint: disable=unused-import, redefined-builtin

import pathlib
import sys

import flexget
from flexget import options
from flexget.event import event
from flexget.terminal import console
from flexget.utils.tools import io_encoding


def print_debug_info(manager, options):
    install_location = pathlib.Path(__file__).absolute().parent.parent.parent
    console('FlexGet Version: {}'.format(flexget.__version__))
    console('Install location: {}'.format(install_location))
    console('Config location: {}'.format(manager.config_path))
    console('Python version: {}.{}.{}'.format(*sys.version_info[:3]))
    console('Detected IO encoding: {}'.format(io_encoding))


@event('options.register')
def register_parser_arguments():
    options.register_command('debug-info', print_debug_info, help='display useful info for debugging')