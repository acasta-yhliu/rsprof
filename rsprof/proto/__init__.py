from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from rsprof.traceutil import StackFrame, StackTrace


class ToJson:
    def to_json(self, *args):
        pass


T = TypeVar("T", bound=ToJson)


class UniqueTable(Generic[T]):
    def __init__(self) -> None:
        self.alloca_table: Dict[T, int] = {}
        self.elemen_table: List[T] = []

    def update(self, element: T) -> int:
        if element in self.alloca_table:
            return self.alloca_table[element]
        else:
            element_id = len(self.elemen_table) + 1
            self.alloca_table[element] = element_id
            self.elemen_table.append(element)
            return element_id

    @property
    def elements(self):
        return self.elemen_table

    def to_json(self, *args):
        l = []
        for id, element in enumerate(self.elements):
            l.append(element.to_json(id + 1, *args))
        return l


class StringTable:
    def __init__(self) -> None:
        self.alloca_table: Dict[str, int] = {}
        self.elemen_table: List[str] = []

    def update(self, element: str) -> int:
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
    filename: str
    location_path: str
    type: int

    def to_json(self, id: int, string_table: StringTable):
        return {
            "id": id,
            "filename": string_table.update(self.filename),
            "location_path": string_table.update(self.location_path),
            "type": self.type,
        }


@dataclass
class Function(ToJson):
    name: str
    system_name: str
    source_file: SourceFile
    start_line: int

    def to_json(
        self, id: int, string_table: StringTable, source_table: UniqueTable[SourceFile]
    ):
        return {
            "id": id,
            "name": string_table.update(self.name),
            "system_name": string_table.update(self.system_name),
            "source_file_id": source_table.update(self.source_file),
            "start_line": self.start_line,
        }


@dataclass
class Location(ToJson):
    function_id: Function
    line: int

    def to_json(self, id: int, function_table: UniqueTable[Function]):
        return {
            "id": id,
            "line": [
                {
                    "function_id": function_table.update(self.function_id),
                    "line": self.line,
                }
            ],
        }


@dataclass
class Event:
    stacktrace: StackTrace
    value_type: int
    values: List[Union[int, str]]


@dataclass
class Context(ToJson):
    location: Location
    parent: Optional["Context"]
    children: List["Context"]

    def to_json(
        self,
        id: int,
        location_table: UniqueTable[Location],
        context_table: UniqueTable["Context"],
    ):
        return {
            "id": id,
            "location_id": location_table.update(self.location),
            "parent_id": 0
            if self.parent is None
            else context_table.update(self.parent),
            "children_id": list(map(lambda x: context_table.update(x), self.children)),
        }


def stackframe_to_context(frame: StackFrame, children: List["Context"]):
    source_file = SourceFile(frame.file, frame.path, 0)
    function = Function(frame.name, frame.system_name, source_file, frame.line)
    location = Location(function, frame.line)
    this_context = Context(location, None, children)
    for child in children:
        child.parent = this_context
    return this_context


def update_context_table(context_table: UniqueTable[Context], context: Context):
    c = context
    while c is not None:
        context_table.update(c)
        c = c.parent


def event_to_sample(event: Event, context_table: UniqueTable[Context]):
    current_stackframe = event.stacktrace.frames[0]
    current_context = stackframe_to_context(current_stackframe, [])

    for i in range(1, len(event.stacktrace.frames)):
        stackframe_to_context(event.stacktrace.frames[i], [current_context])

    update_context_table(context_table, current_context)

    sample = Sample(current_context, event.value_type)
    sample.metric = event.values

    return sample


class MetricDesc:
    INT_VALUE = 0
    UINT_VALUE = 1
    STR_VALUE = 2

    def __init__(self, value_type: int, unit: str, desc: str) -> None:
        self.value_type = value_type
        self.unit = unit
        self.desc = desc

    def to_json(self, string_table: StringTable):
        return {
            "value_type": self.value_type,
            "unit": string_table.update(self.unit),
            "desc": string_table.update(self.desc),
        }


class Sample:
    def __init__(self, context: Context, value_type: int) -> None:
        self.context = context
        self.value_type = value_type
        self.metric: List[Union[int, str]] = []

    def add_metric(self, metric: Union[int, str]):
        self.metric.append(metric)

    def to_json(self, string_table: StringTable, context_table: UniqueTable[Context]):
        if self.value_type == 0:

            to_json_metric = lambda value: {
                "int_value": value,
                "uint_value": 0,
                "str_value": 0,
            }

        elif self.value_type == 2:

            to_json_metric = lambda value: {
                "int_value": 0,
                "uint_value": value,
                "str_value": 0,
            }
        else:
            to_json_metric = lambda value: {
                "int_value": 0,
                "uint_value": 0,
                "str_value": string_table.update(value),
            }

        return {
            "context_id": context_table.update(self.context),
            "metric": list(map(to_json_metric, self.metric)),
        }


class ProfileBuilder:
    def __init__(self, metric_descs: List[MetricDesc]) -> None:
        # description of different metrices
        self.metric_type = metric_descs

        # internal string table for serialization
        self.string_table = StringTable()
        self.string_table.update("")

        self.samples: List[Sample] = []

        self.context_table = UniqueTable[Context]()

        self.location_table = UniqueTable[Location]()
        self.function_table = UniqueTable[Function]()
        self.source_table = UniqueTable[SourceFile]()

    def add_sample(self, sample: Sample):
        self.samples.append(sample)

    def to_json(self):
        return {
            "metric_type": list(
                map(lambda x: x.to_json(self.string_table), self.metric_type)
            ),
            "sample": list(
                map(
                    lambda x: x.to_json(self.string_table, self.context_table),
                    self.samples,
                )
            ),
            "context": self.context_table.to_json(),
            "location": self.location_table.to_json(self.function_table),
            "function": self.function_table.to_json(
                self.string_table, self.source_table
            ),
            "source_file": self.source_table.to_json(self.string_table),
            "string_table": self.string_table.strings,
        }
