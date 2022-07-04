from lldb import SBDebugger


def install_lldb_command(debugger: SBDebugger, command_func):
    # fetch the name of the command and current module
    module_name = command_func.__module__
    command_name = command_func.__name__

    debugger.HandleCommand(
        f"command script add -f {module_name}.{command_name} {command_name}"
    )


