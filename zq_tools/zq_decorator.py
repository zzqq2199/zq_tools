import time
import sys
import functools
import inspect
from typing import Any, Callable, TypeVar, cast
from zq_tools.zq_logger import default_logger as logger

# Used for annotating the decorator usage of 'no_grad' and 'enable_grad'.
# See https://mypy.readthedocs.io/en/latest/generics.html#declaring-decorators
FuncType = Callable[..., Any]
F = TypeVar('F', bound=FuncType)


class _DecoratorContextManager:
    """Allow a context manager to be used as a decorator"""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    def __call__(self, func: F) -> F:
        if inspect.isgeneratorfunction(func):
            return self._wrap_generator(func)

        @functools.wraps(func)
        def decorate_context(*args, **kwargs):
            with self.clone():
                return func(*args, **kwargs)
        return cast(F, decorate_context)

    def _wrap_generator(self, func):
        """Wrap each generator invocation with the context manager"""
        @functools.wraps(func)
        def generator_context(*args, **kwargs):
            gen = func(*args, **kwargs)

            # Generators are suspended and unsuspended at `yield`, hence we
            # make sure the grad mode is properly set every time the execution
            # flow returns into the wrapped generator and restored when it
            # returns through our `yield` to our caller (see PR #49017).
            try:
                # Issuing `None` to a generator fires it up
                with self.clone():
                    response = gen.send(None)

                while True:
                    try:
                        # Forward the response to our caller and get its next request
                        request = yield response

                    except GeneratorExit:
                        # Inform the still active generator about its imminent closure
                        with self.clone():
                            gen.close()
                        raise

                    except BaseException:
                        # Propagate the exception thrown at us by the caller
                        with self.clone():
                            response = gen.throw(*sys.exc_info())

                    else:
                        # Pass the last request to the generator and get its response
                        with self.clone():
                            response = gen.send(request)

            # We let the exceptions raised above by the generator's `.throw` or
            # `.send` methods bubble up to our caller, except for StopIteration
            except StopIteration as e:
                # The generator informed us that it is done: take whatever its
                # returned value (if any) was and indicate that we're done too
                # by returning it (see docs for python's return-statement).
                return e.value

        return generator_context

    def __enter__(self) -> None:
        raise NotImplementedError

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        raise NotImplementedError

    def clone(self):
        # override this method if your children class takes __init__ parameters
        return self.__class__(*self.args, **self.kwargs)

def do_nothing(*args, **kwargs): 
    pass

def pass_it(func): # decorator
    return do_nothing

class time_it(_DecoratorContextManager):
    def __init__(self, 
                 keyword="", 
                 print_it=print, 
                 sync_func=do_nothing):
        super().__init__(keyword=keyword, print_it=print_it, sync_func=sync_func)
        self.print_it = print_it
        self.sync_func = sync_func
        self.keyword = keyword if keyword=="" else f"[{keyword}] "
    def __enter__(self):
        self.sync_func()
        self.start_time = time.time()
    def __exit__(self, exc_type: Any, exc_value: Any, traceback:Any):
        self.sync_func
        self.stop_time = time.time()
        self.print_it(f"{self.keyword}time_it: {self.stop_time-self.start_time}s")

    
if __name__ == '__main__':
    @pass_it
    def test():
        print("hello in test")
    test()
    
    @time_it(keyword="time it as wrapper")
    def test():
        print("hello in decorator")
    test()
    
    with time_it(keyword="time it as context manager"):
        print("hello in `with`")

    from zq_tools.zq_logger import default_logger as logger
    with time_it(keyword="time it as context manager", print_it=logger.info):
        print("hello in `with`, print with logger")
    
    
    