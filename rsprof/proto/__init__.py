from dataclasses import dataclass
import json
from typing import List
from rsprof.proto import profile_pb2 as pb2
from google.protobuf import json_format


@dataclass
class Profile:
    metric_type: List["MetricType"]
    sample: List["Sample"]
    context: List["Context"]
    location: List["Location"]
    function: List["Function"]
    source_file: List["SourceFile"]
    string_table: List[str]

    def to_json(self):
        return {
            "metric_type": self.metric_type,
            "sample": self.sample,
            "context": self.context,
            "location": self.location,
            "function": self.function,
            "source_file": self.source_file,
            "string_table": self.string_table,
        }

    def to_proto(self):
        return json_format.Parse(json.dumps(self.to_json()), pb2.Profile())


class StringTable:
    def __init__(self) -> None:
        self.string_table = [""]

    def new_string(self, string: str):
        self.string_table.append(string)
        return len(self.string_table) - 1


def _to_json_list(l, string_table: StringTable):
    return list(map(lambda x: x.to_json(string_table), l))


@dataclass
class Sample:
    context_id: int
    metric: List["Metric"]

    def to_json(self, string_table: StringTable):
        return {
            "context_id": self.context_id,
            "metric": _to_json_list(self.metric, string_table),
        }


@dataclass
class Metric:
    int_value: int
    uint_value: int
    str_value: str

    def to_json(self, string_table: StringTable):
        return {
            "int_value": self.int_value,
            "uint_value": self.uint_value,
            "str_value": string_table.new_string(self.str_value),
        }


@dataclass
class MetricType:
    value_type: int
    unit: str
    des: str

    def to_json(self, string_table: StringTable):
        return {
            "value_type": self.value_type,
            "unit": string_table.new_string(self.unit),
            "des": string_table.new_string(self.des),
        }


@dataclass
class Context:
    id: int
    location_id: int
    parent_id: int
    children_id: List[int]

    def to_json(self, string_table: StringTable):
        return {
            "id": self.id,
            "location_id": self.location_id,
            "parent_id": self.parent_id,
            "children_id": self.children_id,
        }


@dataclass
class Location:
    id: int
    line: List["Line"]

    def to_json(self, string_table: StringTable):
        return {"id": self.id, "line": _to_json_list(self.line, string_table)}


@dataclass
class Line:
    function_id: int
    line: int

    def to_json(self, string_table: StringTable):
        return {"function_id": self.function_id, "line": self.line}


@dataclass
class Function:
    id: int
    name: str
    system_name: str
    source_file_id: int
    start_line: int

    def to_json(self, string_table: StringTable):
        return {
            "id": self.id,
            "name": string_table.new_string(self.name),
            "system_name": string_table.new_string(self.system_name),
            "source_file_id": self.source_file_id,
            "start_line": self.start_line,
        }


@dataclass
class SourceFile:
    id: int
    filename: str
    location_path: str
    type: int

    def to_json(self, string_table: StringTable):
        return {
            "id": self.id,
            "filename": string_table.new_string(self.filename),
            "location_path": string_table.new_string(self.location_path),
            "type": self.type,
        }
