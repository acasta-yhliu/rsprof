# tool collection for LLDB, inspecting symbols, found symbol by name,
# and other things

import re
import lldb
import rust_demangler
from contextlib import redirect_stdout


def symbols(target: lldb.SBTarget):
    for i in range(0, target.GetNumModules()):
        module: lldb.SBModule = target.GetModuleAtIndex(i)
        for si in range(0, module.GetNumSymbols()):
            symbol: lldb.SBSymbol = module.GetSymbolAtIndex(si)
            yield symbol


def not_none_str(a):
    return "" if a is None else a


@lldb.command("list-names", "list all symbols' name of the current target")
def list_symbols(debugger: lldb.SBDebugger, command: str, result, options):
    with redirect_stdout(result):
        target: lldb.SBTarget = debugger.GetSelectedTarget()
        if target.IsValid():
            for symbol in symbols(target):
                print(not_none_str(symbol.GetName()))


@lldb.command("list-sysnames", "list all symbols' mangled name of the current target")
def list_symbols(debugger: lldb.SBDebugger, command: str, result, options):
    with redirect_stdout(result):
        target: lldb.SBTarget = debugger.GetSelectedTarget()
        if target.IsValid():
            for symbol in symbols(target):
                print(not_none_str(symbol.GetMangledName()))


@lldb.command("find-names", "find name with regex")
def find_names(debugger: lldb.SBDebugger, command: str, result, options):
    with redirect_stdout(result):
        target: lldb.SBTarget = debugger.GetSelectedTarget()
        if target.IsValid():
            pattern = re.compile(command)
            for symbol in symbols(target):
                sym_name = not_none_str(symbol.GetName())
                if pattern.match(sym_name) is not None:
                    print(sym_name)


@lldb.command("find-sysnames", "find mangled name with regex")
def find_sysnames(debugger: lldb.SBDebugger, command: str, result, options):
    with redirect_stdout(result):
        target: lldb.SBTarget = debugger.GetSelectedTarget()
        if target.IsValid():
            pattern = re.compile(command)
            for symbol in symbols(target):
                sym_name = not_none_str(symbol.GetMangledName())
                if pattern.match(sym_name) is not None:
                    print(sym_name)


@lldb.command("find-demangle", "find mangled name with regex")
def find_demangle(debugger: lldb.SBDebugger, command: str, result, options):
    with redirect_stdout(result):
        target: lldb.SBTarget = debugger.GetSelectedTarget()
        if target.IsValid():
            pattern = re.compile(command)
            for symbol in symbols(target):
                sym_name = rust_demangler.demangle(
                    not_none_str(symbol.GetMangledName()))
                if pattern.match(sym_name) is not None:
                    print(sym_name)
