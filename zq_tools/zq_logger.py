import logging
import colorful as cf

__all__ = ["get_logger"]
allocated_loggers = {}

class ZQ_Logger(logging.Logger):
    def __init__(self, name):
        super(ZQ_Logger, self).__init__(name)
        self.tag = ""
        self.print_thread = False
        self.print_level = True
        
    def generate_fmt(self)->logging.StreamHandler:
        thread_fmt = "" if not self.print_thread else "[%(threadName)s] "
        level_fmt = "" if not self.print_level else " [%(levelname)s]"
        basic_fmt = f'{self.tag}[%(asctime)s.%(msecs)03d] {thread_fmt}"%(pathname)s", line %(lineno)d{level_fmt}: %(message)s'
        date_fmt = "%Y-%m-%d %H:%M:%S"
        fmt = logging.Formatter(
            fmt = basic_fmt,
            datefmt = date_fmt
        )
        return fmt
        
    def reset_format(self):
        formatter = self.generate_fmt()
        for handler in self.handlers: 
            handler.setFormatter(formatter)
        return self
            
    def set_tag(self, tag:str):
        self.tag = tag
        self.reset_format()
        return self

    def set_print_thread(self, print_thread:bool=True):
        self.print_thread = print_thread
        self.reset_format()
        return self
    
    def color(self, msg:str, color:str='white',*args, **kwargs):
        color = getattr(cf, color)
        self._log(999, color(msg), args, **kwargs)
    def debug(self, msg:str, *args, **kwargs):
        self._log(logging.DEBUG, msg, args, kwargs)
    def info(self, msg:str, *args, **kwargs):
        self._log(logging.INFO, cf.green(msg), args, kwargs)
    def warn(self, msg:str, *args, **kwargs):
        self._log(logging.WARN, cf.yellow(msg), args, kwargs)
    def error(self, msg:str, *args, **kwargs):
        self._log(logging.ERROR, cf.red(msg), args, kwargs)
    def fatal(self, msg:str, *args, **kwargs):
        self._log(logging.FATAL, cf.bold_red(msg), args, kwargs)
        
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
    logger1.set_tag("[TAG]")
    logger2 = get_logger()
    logger3 = get_logger("another logger")
    logger2.debug("debug")
    logger2.info("info")
    logger2.warning("warning")
    logger2.error("error")
    logger2.critical("critical")
    logger2.fatal("fatal")
    logger3.color("msg", "italic_red")
    