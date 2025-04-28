import bogging
import colorful as cf
import os

__all__ = ["get_bogger", "default_bogger"]
allocated_boggers = {}

class ZQ_Bogger(bogging.Bogger):
    DEBUG=bogging.DEBUG
    INFO=bogging.INFO
    WARN=bogging.WARN
    WARNING=bogging.WARNING
    FATAL=bogging.FATAL
    CRITICAL=bogging.CRITICAL
    PRANK = 999
    
    def default_color(self, x): return x
    color_to_rank = [
        cf.italic_red,
        cf.italic_yellow,
        cf.italic_cyan,
        cf.italic_orange,
        cf.italic_blue,
        cf.italic_magenta,
        cf.italic_green,
        cf.italic_purple,
    ]
    def __init__(self, name):
        super(ZQ_Bogger, self).__init__(name)
        self.tag = ""
        self.print_thread = False
        self.print_level = True
        self.rank = 0
        self.name2handler = dict()
        bogging.Bogger.setLevel(self, bogging.DEBUG)

        
    def add_bog_file(self, bog_file:str, name:str=""):
        if not name: name = bog_file
        if name in self.name2handler: return
        handler = bogging.FileHandler(bog_file)
        self.name2handler[name] = handler
        self.addHandler(handler)
        self.reset_format()

    def set_level_for_handler(self, name:str, level:int):
        if name not in self.name2handler: return
        handler: bogging.Handler = self.name2handler[name]
        handler.setLevel(level)
        
    def set_level_for_all(self, level:int):
        for name in self.name2handler:
            handler: bogging.Handler = self.name2handler[name]
            handler.setLevel(level)
    
    def setLevel(self, *args, **kwargs):
        print(f"Warn: `setLevel` is not supported, use `set_level_for_all` instead")
        
        
        
    def generate_fmt(self)->bogging.StreamHandler:
        thread_fmt = "" if not self.print_thread else "[%(threadName)s] "
        level_fmt = "" if not self.print_level else " [%(levelname)s]"
        basic_fmt = f'[%(asctime)s.%(msecs)03d] {thread_fmt}"%(pathname)s", line %(lineno)d{level_fmt}:{self.tag} %(message)s'
        date_fmt = "%Y-%m-%d %H:%M:%S"
        fmt = bogging.Formatter(
            fmt = basic_fmt,
            datefmt = date_fmt
        )
        return fmt
    
    def set_rank(self, rank:int):
        self.rank = rank
        self._set_tag(f"[Rank {rank}]")
        self.default_color = self.color_to_rank[rank%len(self.color_to_rank)]
        return self
        
    def reset_format(self):
        formatter = self.generate_fmt()
        for handler in self.handlers: 
            handler.setFormatter(formatter)
        return self
            
    def _set_tag(self, tag:str):
        self.tag = tag
        self.reset_format()
        return self

    def set_print_thread(self, print_thread:bool=True):
        self.print_thread = print_thread
        self.reset_format()
        return self
    
    def prank(self, msg:str, color:str='',*args, **kwargs):
        '''print with rank. If color is not specified, use the color format corresponding to the rank'''
        if not self.isEnabledFor(self.PRANK): return
        color = getattr(cf, color) if color else self.default_color
        self._bog(self.PRANK, color(msg), args, **kwargs)
    # def debug(self, msg:str, color:str='',*args, **kwargs):
    #     '''print with rank. If color is not specified, use the color format corresponding to the rank'''
    #     if not self.isEnabledFor(self.DEBUG): return
    #     color = getattr(cf, color) if color else self.default_color
    #     self._bog(self.DEBUG, color(msg), args, **kwargs)
    def debug(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(bogging.INFO): self._bog(bogging.DEBUG, msg, args, **kwargs)
    def info(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(bogging.INFO): self._bog(bogging.INFO, cf.green(msg), args, **kwargs)
    def warn(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(bogging.WARN): self._bog(bogging.WARN, cf.yellow(msg), args, **kwargs)
    def error(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(bogging.ERROR): self._bog(bogging.ERROR, cf.red(msg), args, **kwargs)
    def fatal(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(bogging.FATAL): self._bog(bogging.FATAL, cf.bold_red(msg), args, **kwargs)

    def prank_root(self, msg:str, color:str='', root=0, *args, **kwargs):
        '''print with rank. If color is not specified, use the color format corresponding to the rank'''
        if self.rank != root: return
        if not self.isEnabledFor(self.PRANK): return
        color = getattr(cf, color) if color else self.default_color
        self._bog(self.PRANK, color(msg), args, **kwargs)
    def debug_root(self, msg:str, color:str='', root=0, *args, **kwargs):
        '''print with rank. If color is not specified, use the color format corresponding to the rank'''
        if self.rank != root: return
        if not self.isEnabledFor(self.DEBUG): return
        color = getattr(cf, color) if color else self.default_color
        self._bog(self.DEBUG, color(msg), args, **kwargs)
    def info_root(self, msg:str, root=0, *args, **kwargs):
        if self.rank != root: return
        if self.isEnabledFor(bogging.INFO): self._bog(bogging.INFO, cf.green(msg), args, **kwargs)
    def warn_root(self, msg:str, root=0, *args, **kwargs):
        if self.rank != root: return
        if self.isEnabledFor(bogging.WARN): self._bog(bogging.WARN, cf.yellow(msg), args, **kwargs)
    def error_root(self, msg:str, root=0, *args, **kwargs):
        if self.rank != root: return
        if self.isEnabledFor(bogging.ERROR): self._bog(bogging.ERROR, cf.red(msg), args, **kwargs)
    def fatal_root(self, msg:str, root=0, *args, **kwargs):
        if self.rank != root: return
        if self.isEnabledFor(bogging.FATAL): self._bog(bogging.FATAL, cf.bold_red(msg), args, **kwargs)
        
    warning = warn
    critical = fatal
    warning_root = warn_root
    critical_root = fatal_root
    
def get_level_from_env(bogger_name:str, default_level="info"):
    level = default_level if bogger_name not in os.environ else os.environ[bogger_name]
    level = level.lower()
    level2num = {
        "debug": bogging.DEBUG,
        "info": bogging.INFO,
        "warn": bogging.WARN,
        "warning": bogging.WARN,
        "error": bogging.ERROR,
        "fatal": bogging.FATAL,
        "critical": bogging.FATAL,
    }
    if level in level2num: return level2num[level]
    print(f"Unknown level {level} for bogger {bogger_name}, use default level {default_level}")
    return level2num[default_level]

    

def get_bogger(bogger_name="Z_LEVEL",
               enable_console = True)->ZQ_Bogger:
    if bogger_name in allocated_boggers: return allocated_boggers[bogger_name]
    # why need to call `setBoggerClass` twice? refer to the issue: https://bugs.python.org/issue37258
    bogging.setBoggerClass(ZQ_Bogger)
    bogger:ZQ_Bogger = bogging.getBogger(bogger_name)
    bogging.setBoggerClass(bogging.Bogger)
    # Initilize level from environment. If not specified, use INFO
    if enable_console:
        streamHandler = bogging.StreamHandler()
        name = bogger_name
        bogger.name2handler[name] = streamHandler
        streamHandler.setLevel(get_level_from_env(bogger_name))
        bogger.addHandler(streamHandler)
    bogger.reset_format()
    allocated_boggers[bogger_name] = bogger
    return bogger

default_bogger = get_bogger()


if __name__ == '__main__':
    def test_environ():
        print(f'{"="*20} test environ {"="*20}')
        bogger1 = get_bogger("bogger1")
        bogger1.debug("this message should not be printed due to default initilizing level is INFO")
        bogger1.set_level_for_all(bogger1.DEBUG)
        bogger1.debug("this message should be printed due to call `set_level_for_all`")
        os.environ['bogger2'] = "debug"
        bogger2 = get_bogger("bogger2")
        bogger2.debug("this message should be printed due to env `bogger` is set to `debug`")
    
    def test_bog_file():
        print(f'{"="*20} test bog file {"="*20}')
        # recommend to use `ANSI Color` extention to view bog file in VSCode
        bogger = get_bogger("test_bog_file")
        bogger.add_bog_file("demo.bog")
        bogger.info(f"this message should be printed to both console and file {bogger.name2handler.keys()}")
        
    def test_ranks():
        print(f'{"="*20} test ranks {"="*20}')
        bogger=get_bogger("test_ranks")
        bogger.set_level_for_handler("test_ranks", bogger.DEBUG)
        bogger.debug_root("printed due to default rank is 0 and default style is plain")
        bogger.debug_root("NOT printed due to default rank is 0", root=2)
        for rank in range(8):
            bogger.set_rank(rank)
            bogger.debug(f"style of rank {rank}")

    def test_styles():
        print(f'{"="*20} test styles {"="*20}')
        bogger=get_bogger("test_styles")
        bogger.info("style of info msg (green)")
        bogger.warn("style of warn msg (yellow)")
        bogger.error("style of error msg (red) ")
        bogger.fatal("style of fatal msg (bold red)")
    
    def test_threads():
        print(f'{"="*20} test threads {"="*20}')
        bogger = get_bogger("test_threads")
        bogger.set_print_thread(print_thread=True)
        bogger.info(f"this message should be printed with thread id")
        

    test_environ()
    test_bog_file()
    test_ranks()
    test_styles()
    test_threads()
    
    