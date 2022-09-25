import os
from typing import Generator

def yield_files(path:str, recursive=False)-> Generator[None, None, str]:
    if recursive==False:
        for v in os.listdir(path):
            yield os.path.join(path, v)
    else:
        for v in os.listdir(path):
            pv = os.path.join(path, v)
            if os.path.isdir(pv):
                yield from yield_files(pv, recursive)
            else:
                yield pv

if __name__ == '__main__':
    for v in yield_files("..", recursive=True):
        print(v)