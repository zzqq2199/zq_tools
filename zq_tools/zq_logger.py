import logging
import colorful as cf
import os

__all__ = ["get_logger", "default_logger"]
allocated_loggers = {}

class ZQ_Logger(logging.Logger):
    DEBUG=logging.DEBUG
    INFO=logging.INFO
    WARN=logging.WARN
    WARNING=logging.WARNING
    FATAL=logging.FATAL
    CRITICAL=logging.CRITICAL
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
        super(ZQ_Logger, self).__init__(name)
        self.tag = ""
        self.print_thread = False
        self.print_level = True
        self.rank = 0
        self.log_files = dict()
        
    def add_log_file(self, log_file:str):
        # file handler follows same level control behavior as console handler
        if log_file in self.log_files: return
        handler = logging.FileHandler(log_file)
        self.log_files[log_file] = handler
        self.addHandler(handler)
        self.reset_format()
        
        
    def generate_fmt(self)->logging.StreamHandler:
        thread_fmt = "" if not self.print_thread else "[%(threadName)s] "
        level_fmt = "" if not self.print_level else " [%(levelname)s]"
        basic_fmt = f'[%(asctime)s.%(msecs)03d] {thread_fmt}"%(pathname)s", line %(lineno)d{level_fmt}:{self.tag} %(message)s'
        date_fmt = "%Y-%m-%d %H:%M:%S"
        fmt = logging.Formatter(
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
        self._log(self.PRANK, color(msg), args, **kwargs)
    def debug(self, msg:str, color:str='',*args, **kwargs):
        '''print with rank. If color is not specified, use the color format corresponding to the rank'''
        if not self.isEnabledFor(self.DEBUG): return
        color = getattr(cf, color) if color else self.default_color
        self._log(self.DEBUG, color(msg), args, **kwargs)
    def info(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(logging.INFO): self._log(logging.INFO, cf.green(msg), args, kwargs)
    def warn(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(logging.WARN): self._log(logging.WARN, cf.yellow(msg), args, kwargs)
    def error(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR): self._log(logging.ERROR, cf.red(msg), args, kwargs)
    def fatal(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(logging.FATAL): self._log(logging.FATAL, cf.bold_red(msg), args, kwargs)

    def prank_root(self, msg:str, color:str='', root=0, *args, **kwargs):
        '''print with rank. If color is not specified, use the color format corresponding to the rank'''
        if self.rank != root: return
        if not self.isEnabledFor(self.PRANK): return
        color = getattr(cf, color) if color else self.default_color
        self._log(self.PRANK, color(msg), args, **kwargs)
    def debug_root(self, msg:str, color:str='', root=0, *args, **kwargs):
        '''print with rank. If color is not specified, use the color format corresponding to the rank'''
        if self.rank != root: return
        if not self.isEnabledFor(self.DEBUG): return
        color = getattr(cf, color) if color else self.default_color
        self._log(self.DEBUG, color(msg), args, **kwargs)
    def info_root(self, msg:str, root=0, *args, **kwargs):
        if self.rank != root: return
        if self.isEnabledFor(logging.INFO): self._log(logging.INFO, cf.green(msg), args, kwargs)
    def warn_root(self, msg:str, root=0, *args, **kwargs):
        if self.rank != root: return
        if self.isEnabledFor(logging.WARN): self._log(logging.WARN, cf.yellow(msg), args, kwargs)
    def error_root(self, msg:str, root=0, *args, **kwargs):
        if self.rank != root: return
        if self.isEnabledFor(logging.ERROR): self._log(logging.ERROR, cf.red(msg), args, kwargs)
    def fatal_root(self, msg:str, root=0, *args, **kwargs):
        if self.rank != root: return
        if self.isEnabledFor(logging.FATAL): self._log(logging.FATAL, cf.bold_red(msg), args, kwargs)
        
    warning = warn
    critical = fatal
    warning_root = warn_root
    critical_root = fatal_root
    
def get_level_from_env(logger_name:str, default_level="info"):
    level = default_level if logger_name not in os.environ else os.environ[logger_name]
    level2num = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARN,
        "warning": logging.WARN,
        "error": logging.ERROR,
        "fatal": logging.FATAL,
        "critical": logging.FATAL,
    }
    if level in level2num: return level2num[level]
    print(f"Unknown level {level} for logger {logger_name}, use default level {default_level}")
    return level2num[default_level]

    
    

def get_logger(logger_name="Z_LEVEL",
               enable_console = True)->ZQ_Logger:
    if logger_name in allocated_loggers: return allocated_loggers[logger_name]
    # why need to call `setLoggerClass` twice? refer to the issue: https://bugs.python.org/issue37258
    logging.setLoggerClass(ZQ_Logger)
    logger = logging.getLogger(logger_name)
    logging.setLoggerClass(logging.Logger)
    # Initilize level from environment. If not specified, use INFO
    logger.setLevel(get_level_from_env(logger_name))
    if enable_console:
        logger.addHandler(logging.StreamHandler())
    logger.reset_format()
    allocated_loggers[logger_name] = logger
    return logger

default_logger = get_logger()


if __name__ == '__main__':
    def test_environ():
        print(f'{"="*20} test environ {"="*20}')
        logger1 = get_logger("logger1")
        logger1.debug("this message should not be printed due to default initilizing level is INFO")
        logger1.setLevel(logger1.DEBUG)
        logger1.debug("this message should be printed due to call `setLevel`")
        os.environ['logger2'] = "debug"
        logger2 = get_logger("logger2")
        logger2.debug("this message should be printed due to env `logger` is set to `debug`")
    
    def test_log_file():
        print(f'{"="*20} test log file {"="*20}')
        # recommend to use `ANSI Color` extention to view log file in VSCode
        logger = get_logger("test_log_file")
        logger.add_log_file("demo.log")
        logger.info(f"this message should be printed to both console and file {logger.log_files}")
        
    def test_ranks():
        print(f'{"="*20} test ranks {"="*20}')
        logger=get_logger("test_ranks")
        logger.setLevel(logger.DEBUG)
        logger.debug_root("printed due to default rank is 0 and default style is plain")
        logger.debug_root("NOT printed due to default rank is 0", root=2)
        for rank in range(8):
            logger.set_rank(rank)
            logger.debug(f"style of rank {rank}")

    def test_styles():
        print(f'{"="*20} test styles {"="*20}')
        logger=get_logger("test_styles")
        logger.info("style of info msg (green)")
        logger.warn("style of warn msg (yellow)")
        logger.error("style of error msg (red) ")
        logger.fatal("style of fatal msg (bold red)")
    
    def test_threads():
        print(f'{"="*20} test threads {"="*20}')
        logger = get_logger("test_threads")
        logger.set_print_thread(print_thread=True)
        logger.info(f"this message should be printed with thread id")
        

    test_environ()
    test_log_file()
    test_ranks()
    test_styles()
    test_threads()
    
    