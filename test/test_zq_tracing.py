import sys
sys.path.append("../")
from zq_tools.zq_tracing import *
import time
        
if __name__ == '__main__':
    for i in range(4):
        record_begin(name=f"name_{i}", cat="seq")
        time.sleep(0.1)
        record_end(name=f"name_{i}", cat="seq")
        time.sleep(0.1)

    # for i in range(4):
    #     record_begin(name=f"name_{i}", cat="nested")
    #     time.sleep(0.1)
    # for i in range(3,-1,-1):
    #     record_end(name=f"name_{i}", cat="nested")
    #     time.sleep(0.1)
    

    for i in range(4):
        record_begin_async(name=f"1name_{i}", id=i, tag=1)
        time.sleep(0.1)
    for i in range(4):
        record_end_async(name=f"1name_{i}", id=i, tag=1)
        time.sleep(0.1)
    
    for i in range(4):
        record_begin_async(name=f"1name_{i}", id=i, tag=2)
        time.sleep(0.1)
    for i in range(4):
        record_end_async(name=f"1name_{i}", id=i, tag=2)
        time.sleep(0.1)
    
    record_thread_name(name="thread")
    record_process_name(name="process")
    record_dump("./test.json")
    