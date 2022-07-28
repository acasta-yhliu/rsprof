use std::alloc::GlobalAlloc;

pub struct RsprofAllocator<T>
where
    T: GlobalAlloc,
{
    pub allocator: T,
}

// debugger would hook on this function to trace event
#[inline(never)]
#[allow(unused_variables)]
#[no_mangle]
pub extern "C" fn __rsprof_memtrace_event(
    event: usize,
    size: usize,
    align: usize,
    ptr: *mut u8,
) -> *mut u8 {
    return ptr;
}

unsafe impl<T> Sync for RsprofAllocator<T> where T: GlobalAlloc {}

unsafe impl<T> GlobalAlloc for RsprofAllocator<T>
where
    T: GlobalAlloc,
{
    unsafe fn alloc(&self, layout: std::alloc::Layout) -> *mut u8 {
        return __rsprof_memtrace_event(
            0,
            layout.size(),
            layout.align(),
            self.allocator.alloc(layout),
        );
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: std::alloc::Layout) {
        self.allocator.dealloc(
            __rsprof_memtrace_event(1, layout.size(), layout.align(), ptr),
            layout,
        )
    }
}
