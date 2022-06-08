
from zq_tools.zq_logger import *

def main():
    import logging
    # show colors
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG) # filter level
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
    get_logger().debug("debug")
    get_logger().info("info")
    get_logger().warning("warning")
    get_logger().error("error")
    get_logger().critical("critical")
    
if __name__ == '__main__':
    main()