from typing import List
class Cycle:
    def __init__(self, datas:List):
        self.length = len(datas)
        self.datas = datas
    
    def __getitem__(self, index:int):
        return self.datas[index%self.length]
    
    def __setitem__(self, index:int, value):
        self.datas[index%self.length] = value

    def __delitem__(self, index):
        raise Exception("Cycle not support delete single item")
    
if __name__ == '__main__':
    c = Cycle([1,2,3,4,5,6,7])
    for i in range(-20, 20):
        print(i,c[i])