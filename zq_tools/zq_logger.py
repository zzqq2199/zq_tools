import logging
import colorful as cf

__all__ = ["get_logger"]
allocated_loggers = {}

class ZQ_Logger(logging.Logger):
    def default_color(self, x): return x
    color_to_rank = [
        cf.red,
        cf.yellow,
        cf.blue,
        cf.cyan,
        cf.green,
        cf.magenta,
        cf.orange,
        cf.purple
    ]
    def __init__(self, name):
        super(ZQ_Logger, self).__init__(name)
        self.tag = ""
        self.print_thread = False
        self.print_level = True
        self.rank = 0
        
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
    
    def print(self, msg:str, color:str='',*args, **kwargs):
        if not self.isEnabledFor(logging.DEBUG): return
        color = getattr(cf, color) if color else self.default_color
        self._log(999, color(msg), args, **kwargs)
    def print_root(self, msg:str, color:str='', root=0, *args, **kwargs):
        if self.rank != root: return
        color = getattr(cf, color) if color else self.default_color
        self._log(999, color(msg), args, **kwargs)
    def debug(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(logging.DEBUG): self._log(logging.DEBUG, msg, args, kwargs)
    def info(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(logging.INFO): self._log(logging.INFO, cf.green(msg), args, kwargs)
    def warn(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(logging.WARN): self._log(logging.WARN, cf.yellow(msg), args, kwargs)
    def error(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(logging.ERROR): self._log(logging.ERROR, cf.red(msg), args, kwargs)
    def fatal(self, msg:str, *args, **kwargs):
        if self.isEnabledFor(logging.FATAL): self._log(logging.FATAL, cf.bold_red(msg), args, kwargs)
        
    warning = warn
    critical = fatal

def get_logger(logger_name="zq_logger",
               log_path = "",
               enable_console = True)->ZQ_Logger:
    if logger_name in allocated_loggers: return allocated_loggers[logger_name]
    logger = ZQ_Logger(logger_name)
    logger.setLevel(logging.DEBUG)
    if log_path:
        logger.addHandler(logging.FileHandler(log_path))
    if enable_console:
        logger.addHandler(logging.StreamHandler())
    logger.reset_format()
    allocated_loggers[logger_name] = logger
    return logger

if __name__ == '__main__':
    # test functions
    logger1 = get_logger()
    logger1.set_print_thread()
    # logger1._set_tag("[TAG]")
    logger1.print_root("this msg can be printed", root=0)
    logger1.set_rank(1)
    logger2 = get_logger()
    logger3 = get_logger("another logger")
    logger2.debug("debug")
    logger2.info("info")
    logger2.warning("warning")
    logger2.error("error")
    logger2.critical("critical")
    logger2.fatal("fatal")
    logger3.print("msg", "italic_red")
    logger1.print("msg", "bold_yellow")
    logger1.print_root("this msg cannot be printed", "italic_yellow")
    logger1.print_root("this msg can be printed", "italic_bold_blue", root=1)
    logger1.print_root("this msg can be printed", root=1)
    
    