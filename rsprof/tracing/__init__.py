from importlib import import_module
from typing import Any, Callable, List, Literal
from lldb import SBDebugger, SBTarget, SBFrame, SBBreakpointLocation

from rsprof.lldbutil import BreakpointManager
from rsprof.logutil import fail, info, panic, warn


class TracingModule:
    def __init__(self, module_name: str) -> None:
        self.breakpoints = BreakpointManager()
        self.module_name = module_name

    def on_load(self, debugger: SBDebugger):
        self.breakpoints.update(debugger)
        return self

    def callback_regex(self, regex: str, loc: Literal["in", "out"]):
        def aux(callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
            self.breakpoints.register_callback_regex(regex, loc, callback)
            return callback

        return aux

    def callback_name(self, name: str, loc: Literal["in", "out"]):
        def aux(callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
            self.breakpoints.register_callback_name(name, loc, callback)
            return callback

        return aux

    def enable(self, target: SBTarget):
        succ_enabled, unresolved = self.breakpoints.set(target)
        if not succ_enabled:
            warn(f"tracing module '{self.module_name}' is already enabled")
        else:
            if unresolved is not None:
                fail(
                    f"tracing module '{self.module_name}' failed to enable due to unresolved symbol '{unresolved}'"
                )
            else:
                info(f"tracing module '{self.module_name}' is enabled")

    def disable(self, target: SBTarget):
        if not self.breakpoints.unset(target):
            warn(f"tracing module '{self.module_name}' is not enabled")
        else:
            info(f"tracing module '{self.module_name}' is disabled")

    def report(self, target: SBTarget):
        if self.is_enabled(target):
            report()

    def is_enabled(self, target: SBTarget):
        for t, _ in self.breakpoints.registered_breakpoints:
            if target == t:
                return True
        return False


REGISTED_MODULES = {"memory"}


def load_tracing_modules(debugger: SBDebugger, modules: List[str]):
    if len(modules) == 0:
        modules = list(REGISTED_MODULES)

    for module_name in modules:
        if module_name not in REGISTED_MODULES:
            panic(f"tracing module '{module_name}' does not exist")

    return map(
        lambda x: import_module(f"rsprof.tracing.{x}").MODULE.on_load(debugger), modules
    )
