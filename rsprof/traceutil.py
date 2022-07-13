from typing import List
from lldb import SBFrame, SBLineEntry, SBFileSpec, SBThread


class StackFrame:
    def __init__(
        self,
        function: str,
        file: str,
        line: int,
    ) -> None:
        self.function = function
        self.file = file
        self.line = line

    def resolve(self):
        # resolve function name, perform demangling
        pass

    def __str__(self) -> str:
        return f"{self.function} at {self.file}:{self.line}"


def stackframe_from_sbframe(frame: SBFrame):
    line_entry: SBLineEntry = frame.GetLineEntry()

    # fetch the file information
    file_spec: SBFileSpec = line_entry.GetFileSpec()
    file = file_spec.GetFilename()

    # fetch the line information
    line = line_entry.GetLine()

    # fetch the function information
    function = frame.GetFunctionName()

    return StackFrame(function, file, line)


class StackTrace:
    def __init__(self, threadid: int, stacktrace: List[StackFrame]) -> None:
        self.stacktrace = stacktrace
        self.threadid = threadid

    def __str__(self) -> str:
        return f"{self.threadid} {self.stacktrace}"


def stacktrace_from_sbframe(frame: SBFrame):
    stacktrace = []
    while frame.IsValid():
        stacktrace.append(stackframe_from_sbframe(frame))
        frame = frame.get_parent_frame()
    thread: SBThread = frame.GetThread()
    return StackTrace(thread.id, stacktrace)
