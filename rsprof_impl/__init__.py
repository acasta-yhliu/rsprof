from rsprof_impl.breakpoint import AT_ENTRANCE, breakpoint_callback


@breakpoint_callback("main", AT_ENTRANCE)
def entrance_callback(a, b, c, d):
    print("main hit")