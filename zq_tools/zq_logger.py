import logging
import colorful as cf

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
        if not self.isEnabledFor(logging.DEBUG): return
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
    
    

def get_logger(logger_name="zq_logger",
               enable_console = True)->ZQ_Logger:
    if logger_name in allocated_loggers: return allocated_loggers[logger_name]
    logger = ZQ_Logger(logger_name)
    logger.setLevel(logging.DEBUG)
    if enable_console:
        logger.addHandler(logging.StreamHandler())
    logger.reset_format()
    allocated_loggers[logger_name] = logger
    return logger

default_logger = get_logger()


if __name__ == '__main__':
    # test functions
    demo_logger = get_logger("My Logger")
    # recommend to use `ANSI Color` in VSCode
    demo_logger.add_log_file("demo.log")
    demo_logger.debug("default style of `debug` msg")
    demo_logger.debug("if rank is not set, `debug` print with no color")
    demo_logger.debug_root("if rank is not set, `debug_root` also print with no color")
    demo_logger.set_rank(1)
    demo_logger.debug("after rank is set, `debug` print with color corresponding to different rank, and the words are italicized")
    demo_logger.debug_root(f"default root is 0, so this message can not be displayed")
    demo_logger.debug_root(f"`debug_root` print if passed param `root` matches `self.rank`", root=1)
    demo_logger.setLevel(demo_logger.FATAL)
    demo_logger.debug("this message cannot be displayed")
    demo_logger.prank(f"`prank` and `prank_root` behaves simalr with `debug` and `debug_root`, but `prank*` have highest priority(999)")

    demo_logger.setLevel(demo_logger.DEBUG)
    for rank in range(8):
        demo_logger.set_rank(rank)
        demo_logger.debug(f"style of rank {rank}")

    demo_logger.info("style of info msg (green)")
    demo_logger.warn("style of warn msg (yellow)")
    demo_logger.error("style of error msg (red) ")
    demo_logger.fatal("style of fatal msg (bold red)")
    
    demo_logger.set_print_thread(print_thread=True)
    demo_logger.info("After `set_print_thread`, the info msg will be printed with thread id")
    
    
    
    