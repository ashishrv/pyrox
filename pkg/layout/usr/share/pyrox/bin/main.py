import os
import sys
import argparse

from pyrox.log import get_logger
import pyrox.server as server

from pyrox.filtering import HttpFilterPipeline

_LOG = get_logger(__name__)

args_parser = argparse.ArgumentParser(
    prog='proxy',
    description='Pyrox, the fast Python HTTP middleware server.')
args_parser.add_argument(
    '-c',
    nargs='?',
    dest='cfg_location',
    default=None,
    help="""
        Sets the configuration file to load on startup. If unset this
        option defaults to /etc/pyrox/pyrox.conf""")
args_parser.add_argument(
    '-p',
    nargs='?',
    dest='plugin_paths',
    default=None,
    help=('"{0}" character separated string of paths to '
          'import from when loading plugins.'.format(os.sep)))
args_parser.add_argument(
    'start',
    default=False,
    help='Starts the daemon.')


def start(args):
    server.start_pyrox(cfg_location=args.cfg_location)


if len(sys.argv) > 1:
    args = args_parser.parse_args()
    if args.start:
        start(args)
else:
    args_parser.print_help()
