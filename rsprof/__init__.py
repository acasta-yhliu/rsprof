from contextlib import redirect_stdout
import json
from lldb import SBDebugger, SBTarget

from rsprof import tracing
from rsprof.cmdutil import parse_command
from rsprof.lldbutil import import_lldb_command
from rsprof.logutil import fail, panic

__version__ = "0.0.1"


def rsprof(lldb_debugger: SBDebugger, command: str, result, options):
    with redirect_stdout(result):
        origin_async = lldb_debugger.GetAsync()
        lldb_debugger.SetAsync(False)

        argv = parse_command(command)

        if argv.version:
            print(__version__)
            return

        # check the current target of debugger and validate it
        target: SBTarget = lldb_debugger.GetSelectedTarget()
        if not target.IsValid():
            panic("unable to select valid target for rsprof")

        loaded_modules = tracing.load_tracing_modules(lldb_debugger, argv.module)

        if argv.action == "enable":
            for module in loaded_modules:
                module.enable(target)
        elif argv.action == "disable":
            for module in loaded_modules:
                module.disable(target)
        elif argv.action == "report":
            if argv.output is None:
                output_postfix = ""
            else:
                output_postfix = argv.output
            for module in loaded_modules:
                module.report(target, output_postfix)
        elif argv.action == "list":
            print("enabled modules:")
            for module in loaded_modules:
                if module.is_enabled(target):
                    print("  ", module.module_name)

        lldb_debugger.SetAsync(origin_async)


def __lldb_init_module(debugger: SBDebugger, _):

    import_lldb_command(debugger, tracing)

    import_lldb_command(debugger, rsprof)
