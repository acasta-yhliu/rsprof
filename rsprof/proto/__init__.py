from dataclasses import dataclass
import json
from typing import Dict, Generic, List, Optional, Tuple, TypeVar, Union
from rsprof.traceutil import StackFrame, StackTrace
from google.protobuf import json_format
from rsprof.proto.profile_pb2 import Profile


class ToJson:
    def to_json(self):
        pass


T = TypeVar("T", bound=ToJson)


class Table(Generic[T]):
    def __init__(self) -> None:
        self.elemen_table: List[T] = []

    def update(self, element: T) -> int:
        self.elemen_table.append(element)
        return len(self.elemen_table)

    def to_json(self):
        l = []
        for id, element in enumerate(self.elemen_table):
            d = {"id": id + 1}
            d.update(element.to_json())
            l.append(d)
        return l


class StringTable:
    def __init__(self) -> None:
        self.alloca_table: Dict[str, int] = {}
        self.elemen_table: List[str] = []
        self.update("")

    def update(self, element: str) -> int:
        if element is None:
            return 0
        if element in self.alloca_table:
            return self.alloca_table[element]
        else:
            element_id = len(self.elemen_table)
            self.alloca_table[element] = element_id
            self.elemen_table.append(element)
            return element_id

    @property
    def strings(self):
        return self.elemen_table


@dataclass
class SourceFile(ToJson):
    filename: int
    location_path: int
    type: int

    def to_json(self):
        return {
            "filename": self.filename,
            "location_path": self.location_path,
            "type": self.type,
        }


@dataclass
class Function(ToJson):
    name: int
    system_name: int
    source_file_id: int
    start_line: int

    def to_json(self):
        return {
            "name": self.name,
            "system_name": self.system_name,
            "source_file_id": self.source_file_id,
            "start_line": self.start_line,
        }


@dataclass
class Location(ToJson):
    function_id: int
    line: int

    def to_json(self):
        return {
            "line": [
                {
                    "function_id": self.function_id,
                    "line": self.line,
                }
            ],
        }


@dataclass
class Context(ToJson):
    location_id: int
    parent_id: int
    children_id: int

    def to_json(self):
        return {
            "location_id": self.location_id,
            "parent_id": self.parent_id,
            "children_id": [self.children_id],
        }


@dataclass
class Event:
    stacktrace: StackTrace
    values: List[int]


class ProfileBuilder:
    def __init__(self, *metric_type: Tuple[str, str]) -> None:
        # internal string table for serialization
        self.strings = StringTable()

        # description of different metrices
        self.metric_type = list(
            map(
                lambda x: {
                    "value_type": 0,
                    "unit": self.strings.update(x[0]),
                    "des": self.strings.update(x[1]),
                },
                metric_type,
            )
        )

        self.samples = []

        self.contexts = Table[Context]()
        self.locations = Table[Location]()
        self.functions = Table[Function]()
        self.source_files = Table[SourceFile]()

    def make_context(self, location_id: int):
        context = Context(location_id, 0, 0)
        return context, self.contexts.update(context)

    def make_location(self, stackframe: StackFrame):
        source_file_id = self.source_files.update(
            SourceFile(
                self.strings.update(stackframe.file),
                self.strings.update(stackframe.path),
                0,
            )
        )

        function_id = self.functions.update(
            Function(
                self.strings.update(stackframe.name),
                self.strings.update(stackframe.system_name),
                source_file_id,
                stackframe.line,
            )
        )
        return self.locations.update(Location(function_id, stackframe.line))

    def add_context_from_stacktrace(self, stacktrace: StackTrace):
        parent_context_id = 0
        parent_context = None
        for frame in reversed(stacktrace.frames):
            location_id = self.make_location(frame)
            context, context_id = self.make_context(location_id)

            # make parent
            context.parent_id = parent_context_id

            # make child
            if parent_context is not None:
                parent_context.children_id = context_id

            # swap
            parent_context_id = context_id
            parent_context = context

        return parent_context_id

    def add_event(self, event: Event):
        metric = list(
            map(
                lambda x: {"int_value": x, "uint_value": 0, "str_value": 0},
                event.values,
            )
        )
        context_id = self.add_context_from_stacktrace(event.stacktrace)
        self.samples.append({"context_id": context_id, "metric": metric})

    def to_json(self):
        return {
            "metric_type": self.metric_type,
            "sample": self.samples,
            # context of samples
            "context": self.contexts.to_json(),
            # location of samples
            "location": self.locations.to_json(),
            "function": self.functions.to_json(),
            "source_file": self.source_files.to_json(),
            "string_table": self.strings.strings,
        }

    def write_file(self, filename: str):
        profile = Profile()
        s = json.dumps(self.to_json())
        with open(filename, "wb") as f:
            f.write(json_format.Parse(s, profile).SerializeToString())
