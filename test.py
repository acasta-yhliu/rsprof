from rsprof.proto import ProfileBuilder, MetricDesc

memory_desc = MetricDesc(
    MetricDesc.STR_VALUE, "byte", "memory allocation and deallocation"
)

builder = ProfileBuilder([memory_desc])

builder.write_file("out.prof")
