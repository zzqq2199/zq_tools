import logging
import colorlog

__all__ = ["get_file_handler", "get_stream_handler", "get_logger"]

console_color_config = {
    'DEBUG': 'white',  # cyan white
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

fmt = '[%(asctime)s.%(msecs)03d] "%(pathname)s", line %(lineno)d [%(levelname)s] : %(message)s'
color_fmt = f'%(log_color)s{fmt}'
date_fmt = "%Y-%m-%d %H:%M:%S"


def get_file_handler(log_path = "./log.txt")->logging.FileHandler :
    file_formatter = logging.Formatter(
        fmt = fmt,
        datefmt = date_fmt
    )
    handler = logging.FileHandler(log_path)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(file_formatter)
    return handler
    
    
def get_stream_handler()->logging.StreamHandler:
    console_formatter = colorlog.ColoredFormatter(
        fmt = color_fmt,
        datefmt = date_fmt,
        log_colors = console_color_config
    )
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(console_formatter)
    return handler

default_logger = logging.getLogger("zq_logger")
default_logger.setLevel(logging.DEBUG)
default_logger.addHandler(get_file_handler("./zq_logger.log"))
default_logger.addHandler(get_stream_handler())

def get_logger(logger_name="zq_logger",
               log_path = "./zq_logger.log",
               enable_file = True,
               enable_console = True):
    if logger_name=="zq_logger": return default_logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        if enable_file:
            logger.addHandler(get_file_handler(log_path))
        if enable_console:
            logger.addHandler(get_stream_handler())
    return logger


if __name__ == '__main__':
    # show colors
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG) # 第一层过滤
    logger.addHandler(get_file_handler())
    stream_handler = get_stream_handler()
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)
    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")
    print()


    # test functions
    logger = get_logger()
    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")