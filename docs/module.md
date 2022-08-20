# Tracing Module

To implement your own tracing module with events and data, you need to do this by creating a file under `rsprof/tracing`. For example, we are going to create an module that names `sample`.

1. Create tracing module by creating the file `rsprof/tracing/sample.py`

2. Register your module at `rsprof/tracing/__init__.py`, you could find the variable `REGISTED_MODULES`, add `sample` to the set so that it could recognize your module as a valid one.

3. Write your module inside `sample.py`. First, you need an initialization of the Module by adding the line of code:

```python
MODULE = TracingModule("sample")
```

Note that this is a must and the variable must be named by `MODULE` so that it could be loaded correctly.

4. Create event and function breakpoint callback. By inheriting the base class `TracingEvent`, you could write your own event to be recorded. By using the decorator `@MODULE.callback_name` or `@MODULE.callback_regex` on a python function with the signature: `(SBFrame, SBBreakpointLocation, Any, Any) -> None`, you could register a breakpoint callback to record events.

5. Create report function with decorator `@MODULE.callback_report`. The python function accepts a `Optional[str]` as an optional prefix of the output file. You could use the `ProfileBuilder` to serialize your data and events into `Drcctprof` format to pass it to the viewer.