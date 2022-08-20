from dataclasses import dataclass
from typing import List
from lldb import SBFrame, SBLineEntry, SBFileSpec, SBThread, SBFunction
from rust_demangler import demangle


@dataclass
class StackFrame:
    system_name: str
    path: str
    file: str
    line: int

    def resolve(self):
        try:
            self.name = demangle(self.system_name)
        except:
            self.name = self.system_name

    def serialize(self):
        return {
            "system_name": self.system_name,
            "name": self.name,
            "path": self.path,
            "file": self.file,
            "line": self.line,
        }


def stackframe_from_sbframe(frame: SBFrame):
    line_entry: SBLineEntry = frame.GetLineEntry()
    file_spec: SBFileSpec = line_entry.GetFileSpec()

    function_name = frame.GetFunctionName()
    function_name = "" if function_name is None else function_name

    return StackFrame(
        function_name,
        file_spec.GetDirectory(),
        file_spec.GetFilename(),
        line_entry.GetLine(),
    )


@dataclass
class StackTrace:
    thread_id: int
    frames: List[StackFrame]

    def resolve(self):
        for st in self.frames:
            st.resolve()

    def filter_module(self, module_prefix: str):
        self.frames = list(
            filter(lambda x: x.system_name.startswith(module_prefix), self.frames)
        )

    def __getitem__(self, key: int):
        return self.frames[key]

    def __len__(self):
        return len(self.frames)

    def serialize(self):
        return {
            "thread_id": self.thread_id,
            "frames": list(map(lambda x: x.serialize(), self.frames)),
        }


def stacktrace_from_sbframe(frame: SBFrame):
    stacktrace = []
    thread: SBThread = frame.GetThread()
    while frame.IsValid():
        stacktrace.append(stackframe_from_sbframe(frame))
        frame = frame.get_parent_frame()
    return StackTrace(thread.GetThreadID(), stacktrace)
