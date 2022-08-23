from dataclasses import dataclass
from inspect import isfunction
from re import Pattern
import re
from typing import Any, Callable, List, Literal, Optional, Tuple, Union
from lldb import (
    SBDebugger,
    SBTarget,
    SBFrame,
    SBBreakpointLocation,
    SBBreakpoint,
    SBValue,
    SBModule,
    SBSymbol
)

from rsprof.logutil import fail, info, warn


def import_lldb_command(lldb_debugger: SBDebugger, item):
    if isfunction(item):
        mod_n, cmd_n = item.__module__, item.__qualname__
        info(f"import command '{mod_n}.{cmd_n}'")
        lldb_debugger.HandleCommand(
            f"command script add -f {mod_n}.{cmd_n} {cmd_n}")
    else:
        for path in item.__path__:
            info(f"import module '{path}'")
            lldb_debugger.HandleCommand(f"command script import {path}")


@dataclass
class SrcLoc:
    file:  str
    line: int

    def __str__(self) -> str:
        return f"{self.file}:{self.line}"


def _not_none(s: Optional[str]):
    return "" if s is None else s


class BrType:
    SYSNAME = 0
    SYSREGEX = 1
    NAME = 2
    REGEX = 3
    SRCLOC = 4


@dataclass
class BrRegistration:
    pattern: Union[str, Pattern, SrcLoc]
    regtype: int
    callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]

    def match(self, symbol: SBSymbol):
        name = _not_none(symbol.GetName())
        sysname = symbol.GetMangledName()
        sysname = name if sysname is None else sysname

        if self.regtype == 0:
            return self.pattern == sysname
        elif self.regtype == 1:
            return self.pattern.match(sysname) is not None
        elif self.regtype == 2:
            return self.pattern == name
        elif self.regtype == 3:
            return self.pattern.match(name) is not None
        return False

    def __str__(self) -> str:
        return self.pattern.__str__()


@dataclass
class BrRecord:
    target: SBTarget
    brs: List[int]


class BreakpointManager:
    DUPLICATE_TARGET = 0
    HAS_UNRESOLVED = 1
    NO_UNRESOLVED = 2

    def __init__(self) -> None:
        self.br_registra: List[BrRegistration] = []
        self.reg_brs: List[BrRecord] = []

    def br_sysregex(
        self,
        regex: str,
        callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None],
    ):
        self.br_registra.append(BrRegistration(
            re.compile(regex), BrType.SYSREGEX, callback))

    def br_sysname(
        self,
        name: str,
        callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None],
    ):
        self.br_registra.append(BrRegistration(name, BrType.SYSNAME, callback))

    def br_srcloc(
        self,
        file: str,
        line: int,
        callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None],
    ):
        self.br_registra.append(BrRegistration(
            SrcLoc(file, line), BrType.SRCLOC, callback))

    def br_name(self, name: str, callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
        self.br_registra.append(BrRegistration(name, BrType.NAME, callback))

    def br_regex(self, regex: str, callback: Callable[[SBFrame, SBBreakpointLocation, Any, Any], None]):
        self.br_registra.append(BrRegistration(
            re.compile(regex), BrType.REGEX, callback))

    def update(self, debugger: SBDebugger):
        self.reg_brs = list(
            filter(
                lambda x: debugger.GetIndexOfTarget(x.target) != 4294967295,
                self.reg_brs,
            )
        )

    def _enumerate_symbols(self, target: SBTarget):
        for i in range(0, target.GetNumModules()):
            module: SBModule = target.GetModuleAtIndex(i)
            for si in range(0, module.GetNumSymbols()):
                symbol: SBSymbol = module.GetSymbolAtIndex(si)
                yield symbol

    def _set_bp(self, bp: SBBreakpoint, pattern: BrRegistration):
        bp.SetAutoContinue(True)
        bp.SetScriptCallbackFunction(
            f"{pattern.callback.__module__}.{pattern.callback.__qualname__}")
        if bp.GetNumLocations() == 0:
            # show a warning if there's no location for that pattern
            warn(f"breakpoint {pattern} has 0 location")
            return False
        return True

    def set(self, target: SBTarget):
        for reg in self.reg_brs:
            if reg.target == target:
                return BreakpointManager.DUPLICATE_TARGET

        # newly created breakpoints
        new_brs = []
        unresolved = False

        # register breakpoints based on location
        for registration in self.br_registra:
            if registration.regtype == BrType.SRCLOC:
                bp: SBBreakpoint = target.BreakpointCreateByLocation(
                    registration.pattern.file, registration.pattern.line)
                if not self._set_bp(bp, registration):
                    unresolved = True
                new_brs.append(bp.id)

        # now handle all symbols, filter them and set breakpoints for demangled name
        for symbol in self._enumerate_symbols(target):
            for registration in self.br_registra:
                if registration.regtype != BrType.SRCLOC and registration.match(symbol):
                    bp: SBBreakpoint = target.BreakpointCreateBySBAddress(
                        symbol.GetStartAddress())
                    if not self._set_bp(bp, registration):
                        unresolved = True
                    new_brs.append(bp.id)

        self.reg_brs.append(BrRecord(target, new_brs))
        info(f"totally {len(new_brs)} breakpoints set")

        if unresolved:
            return BreakpointManager.HAS_UNRESOLVED
        else:
            return BreakpointManager.NO_UNRESOLVED

    def unset(self, target: SBTarget):
        for index, rec in enumerate(self.reg_brs):
            if rec.target == target:
                for id in rec.brs:
                    target.BreakpointDelete(id)
                self.reg_brs.pop(index)
                return True
        return False


def evaluate_expression_unsigned(frame: SBFrame, expression: str) -> int:
    return frame.EvaluateExpression(expression).GetValueAsUnsigned()


def get_function_parameter(frame: SBFrame, nargs: Tuple[Literal["s", "u"], ...]):
    ret_value: List[int] = []
    for id, s in enumerate(nargs):
        arg_value: SBValue = frame.EvaluateExpression(f"$arg{id + 1}")
        ret_value.append(
            arg_value.GetValueAsUnsigned() if s == "u" else arg_value.GetValueAsSigned()
        )
    return tuple(ret_value)
