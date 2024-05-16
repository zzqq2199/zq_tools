import json
import time
import os
import threading
from typing import Union

# json format: https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/

__all__ = [
    "get_pid", "get_tid",
    "record_timestamp",
    "record_begin",
    "record_end",
    "record_duration",
    "record_thread_name",
    "record_process_name",
    "record_process_sort_index",
    "record_thread_sort_index",
    "record_dump",
    "record_init",
    "record_append",
    "record_begin_async",
    "record_end_async",
    "set_start_timestamp",
    "enable_trace",
    "disable_trace"
]


contents = []
START_TIMESTAMP = 0

TRACING_SWITCH=True

TRACING_STASH=True
TRACING_LOGGER=None

def enable_trace():
    global TRACING_SWITCH
    TRACING_SWITCH=True
def disable_trace():
    global TRACING_SWITCH
    TRACING_SWITCH=False

def should_trace(func):
    def inner(*args, **kwargs):
        global TRACING_SWITCH
        if TRACING_SWITCH:
            return func(*args, **kwargs)
        else:
            return
    return inner

def set_tracing_stash(tracing_stash=True, trace_file:str="trace.json", init_trace_file=True):
    import logging
    global TRACING_STASH, TRACING_LOGGER
    TRACING_STASH = tracing_stash
    if TRACING_STASH==False:
        # init TRACING_LOGGER
        TRACING_LOGGER = logging.getLogger("zq_tracing")
        TRACING_LOGGER.setLevel(logging.FATAL)
        file_handler = logging.FileHandler(trace_file)
        TRACING_LOGGER.addHandler(file_handler)
        if init_trace_file:
            with open(trace_file, 'w') as f:
                f.write("[\n")

    
def record_update(j:dict):
    if TRACING_STASH:
        contents.append(json.dumps(j))
    else:
        TRACING_LOGGER.fatal(json.dumps(j)+",")


def set_start_timestamp():
    global START_TIMESTAMP
    START_TIMESTAMP = time.time()


def get_pid():
    return os.getpid()

def get_tid():
    tid = threading.get_ident()
    if not tid: tid = 0
    return tid

@should_trace
def record_timestamp(name:str,
                 cat:str,
                 tid:int,
                 pid:int,
                 **kwargs) -> None:
    global START_TIMESTAMP
    j = {
        "name":name,
        "cat":cat,
        "ts": (time.time()-START_TIMESTAMP)*1000000,
        "pid": get_pid() if pid<0 else pid,
        "tid": get_tid() if tid<0 else tid
    }
    if kwargs:
        j["args"] = kwargs
    return j

@should_trace
def record_begin(name:str,
                 cat:str="",
                 tid=-1,
                 pid=-1,
                 **kwargs):
    j = record_timestamp(name, cat, tid, pid, **kwargs)
    j['ph'] = "B"
    record_update(j)

@should_trace
def record_end(name:str,
               cat:str="",
               tid=-1,
               pid=-1,
               **kwargs):
    j = record_timestamp(name, cat, tid, pid, **kwargs)
    j['ph'] = "E"
    record_update(j)
    
@should_trace
def record_begin_async(name:str,
                       id:Union[str,int],
                       cat:str="",
                       tid=-1,
                       pid=-1,
                       **kwargs
                       ):
    j = record_timestamp(name, cat, tid, pid, **kwargs)
    j['ph'] = 'b'
    j['id'] = id
    record_update(j)
    
@should_trace
def record_end_async(name:str,
                       id:Union[str,int],
                       cat:str="",
                       tid=-1,
                       pid=-1,
                       **kwargs
                       ):
    j = record_timestamp(name, cat, tid, pid, **kwargs)
    j['ph'] = 'e'
    j['id'] = id
    record_update(j)

@should_trace
def record_duration(name:str,
                    cat:str="",
                    tid=-1,
                    pid=-1,
                    dur:float=0,
                    **kwargs):
    j = record_timestamp(name, cat, tid, pid, **kwargs)
    j['ph'] = "X"
    j['dur'] = dur  
    record_update(j)
    
@should_trace
def record_thread_name(name:str, tid=-1, pid=-1, **kwargs):
    j = {
        "name": "thread_name",
        "ph": "M",
        "pid": get_pid() if pid<0 else pid,
        "tid": get_tid() if tid<0 else tid,
    }
    kwargs['name'] = name
    j['args'] = kwargs
    record_update(j)

@should_trace
def record_process_name(name:str, pid=-1, **kwargs):
    j = {
        "name": "process_name",
        'ph': 'M',
        'pid': get_pid() if pid<0 else pid,
    }
    kwargs['name'] = name
    j['args'] = kwargs
    record_update(j)
    
@should_trace
def record_process_sort_index(index:int, pid=-1, **kwargs):
    j = {
        'name': 'process_sort_index',
        'ph': 'M',
        'pid': get_pid() if pid<0 else pid,
    }
    kwargs['sort_index'] = index
    j['args'] = kwargs
    record_update(j)

@should_trace
def record_thread_sort_index(index:int, tid=-1, pid=-1, **kwargs):
    j = {
        'name': 'thread_sort_index',
        'ph': 'M',
        'pid': get_pid() if pid<0 else pid,
        'tid': get_tid() if tid<0 else tid,
    }
    kwargs['sort_index'] = index
    j['args'] = kwargs
    record_update(j)

@should_trace
def record_dump(filename:str):
    with open(filename, 'w') as f:
        f.write("[\n")
        f.write(",\n".join(contents))
        f.write("\n]\n")

@should_trace
def record_init(filename:str):
    with open(filename, 'w') as f:
        f.write("[\n")

@should_trace
def record_append(filename:str):
    with open(filename, 'a') as f:
        for content in contents:
            f.write(f"{content},\n")

        
         
        
if __name__ == '__main__':
    # disable_trace()
    def demo1():
        for i in range(2):
            print(f"{i}")
            record_begin(name=f"name_{i}", cat="")
            time.sleep(1)
            record_end(name=f"name_{i}", cat="")
            time.sleep(0.5)
        record_thread_name(name="thread")
        record_process_name(name="process")
        record_dump("./test.json")
    
    def demo2():
        set_tracing_stash(False, trace_file="demo2.json", init_trace_file=True)
        # with open("demo2.json", 'w') as f: f.write("[\n")
        for i in range(2):
            print(f"{i}")
            record_begin(name=f"name_{i}", cat="")
            time.sleep(1)
            record_end(name=f"name_{i}", cat="")
            time.sleep(0.5)
        record_thread_name(name="thread")
        record_process_name(name="process")
    
    demo2()