def do_nothing(func):
    def inner(*args, **kwargs):
        return
    return inner
    
if __name__ == '__main__':
    @do_nothing
    def test():
        print("hello in test")
    test()