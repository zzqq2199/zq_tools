from zq_tools.zq_tracing import *
import time
        
        
if __name__ == '__main__':
    for i in range(2):
        print(f"{i}")
        record_begin(name=f"name_{i}", cat="")
        time.sleep(1)
        record_end(name=f"name_{i}", cat="")
        time.sleep(0.5)
    record_thread_name(name="thread")
    record_process_name(name="process")
    record_dump("./test.json")