from argparse import ArgumentParser, RawDescriptionHelpFormatter
from shlex import split

EPILOG_WARNING = r"""
warnings: 
  1. rsprof would disable other breakpoints and watchpoints, thus do not
     use it when you are debugging your program
  2. rsprof requires existing valid lldb target to run"""


def comma_strlist(string: str):
    return string.split(",")


ARG_PARSER = ArgumentParser(
    prog="rsprof", formatter_class=RawDescriptionHelpFormatter, epilog=EPILOG_WARNING
)

ARG_PARSER.add_argument(
    "-v", "--version", action="store_true", help="show version information"
)
ARG_PARSER.add_argument(
    "action",
    choices=["enable", "disable", "report", "list"],
    help="action on tracing modules, default to all if no module provided",
)
ARG_PARSER.add_argument(
    "-m", "--module", type=comma_strlist, default=list(), help="provide tracing modules"
)
ARG_PARSER.add_argument("-p", "--program", type=str,
                        default=None, help="module name of the program")
ARG_PARSER.add_argument("-o", "--output", type=str, help="output report file")


def parse_command(command: str):
    return ARG_PARSER.parse_args(split(command))
