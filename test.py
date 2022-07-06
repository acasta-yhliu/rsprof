from lldb import SBDebugger, SBTarget


def cmd(debugger: SBDebugger, command: str, result, _):
    target1: SBTarget = debugger.GetSelectedTarget()
    debugger.DeleteTarget(target1)
    print(debugger.GetIndexOfTarget(target1))


def __lldb_init_module(debugger: SBDebugger, _):
    debugger.HandleCommand("command script add -f test.cmd cmd")
