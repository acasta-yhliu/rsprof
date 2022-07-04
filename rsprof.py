from rsprof_impl.utility import install_lldb_command
from rsprof_impl.breakpoint import AT_ENTRANCE, breakpoint_callback, BreakpointManager
from rsprof_impl.information import RSPROF_DESC, RSPROF_WARN, RSPROF_VERSION

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import logging
import shlex
from lldb import SBDebugger, SBTarget

ARG_PARSER: ArgumentParser


@breakpoint_callback("__rust_alloc", AT_ENTRANCE)
def allocation_callback(frame, location, extra_args, internal_dict):
    print("breakpoint hit")


class Nested:
    @staticmethod
    @breakpoint_callback("__rust_dealloc", AT_ENTRANCE)
    def deallocation_callback(frame, location, extra_args, internal_dict):
        print("deallocation hit")


def rsprof(debugger: SBDebugger, command: str, result, internal_dict):
    # setting async to false, also remember to save the old state
    old_async = debugger.GetAsync()
    debugger.SetAsync(False)

    args = ARG_PARSER.parse_args(shlex.split(command))

    # print version information, would override other things
    if args.version:
        print(RSPROF_VERSION, file=result)
        return

    # validate there's target to profile
    target: SBTarget = debugger.GetSelectedTarget()
    if not target.IsValid():
        logging.error("unable to select valid target for rsprof.")
        return

    with BreakpointManager(debugger, target):
        debugger.HandleCommand("r")

    # recover old state
    debugger.SetAsync(old_async)


def __lldb_init_module(debugger: SBDebugger, internal_dict):
    # install the root command rsprof to context
    install_lldb_command(debugger, rsprof)

    # config logging utility
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s :: %(message)s ",
        datefmt="%y-%m-%d %H:%M:%S",
    )

    # config argument parser
    global ARG_PARSER
    ARG_PARSER = ArgumentParser(
        prog=__name__,
        formatter_class=RawDescriptionHelpFormatter,
        description=RSPROF_DESC,
        epilog=RSPROF_WARN,
    )

    ARG_PARSER.add_argument(
        "-a",
        "--args",
        default="",
        nargs="?",
        type=str,
        help="arguments provided to the selected target",
    )

    ARG_PARSER.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="display version information of rsprof",
    )

    subparsers = ARG_PARSER.add_subparsers(help="tools configurations for rsprof")


if __name__ == "__main__":
    # if this file is executed stand alone, then print error message
    print("TODO: launch lldb and perform following things")
