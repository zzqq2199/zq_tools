# zq_logger
generates a logger, preformatted with the file name, line number information, differrent levels of color, and can be output in the console and written to a file at the same time.

![](https://raw.githubusercontent.com/zzqq2199/pic_for_public/master/img/20220701162735.png)

If you use vscode to view the output log in the editor, `ANSI Colors` extension is recommended to install.

# zq_tracing
help generate json file used in `chrome://tracing`

![](https://raw.githubusercontent.com/zzqq2199/pic_for_public/master/img/20220608134508.png)


# Release Notes
- 1.1.0: change pattern of logging number of line
- 1.0.9: use bogging, and alias logger to bogger if not defined yet.
- 1.0.8: fix bug: add `bogging` 
- 1.0.7: add `zq_bogger` to prevent logger conflicts
- 1.0.6: support zq_tracing.dump instantly
- 1.0.5: fix bugs of `**kwargs` passing in `zq_logger`
- 1.0.4: fix errors in logger.debug 
- 1.0.3: make logger.debug to print without any color.
- 1.0.2: fine grained control of different handlers
- 0.9.9: add `__repr__` for zq_cycle
- 0.9.8: support `from zq_tools import logger` as well as `from zq_tools.zq_logger import default_logger as logger` for shorter code
- 0.9.7: fix `setLevel` bug in zq_logger; use env value to initilize ZQ_Logger's controlling level
- 0.9.6: increase version due to keep failing on uploading
- 0.9.4: fix bug: `zq_decorator.time_it(sync)`
- 0.9.3: update `zq_decorator:: do_nothing, pass_it, time_it(support sync and self-defined print)`
- 0.9.2: fix bug: `.zq_logger` to `zq_tools.zq_logger`
- 0.9.1: use `default_logger` instead of `print`
- 0.9.0: add decorator and manager: `zq_decorator.timeit`
- 0.8.8: add decorator: `zq_decorator.do_nothing`
- 0.8.7: add api: `zq_tracing.enable_trace`, `zq_tracing.disable_trace`
- 0.8.6: add api: `zq_tracing.record_init`, `zq_tracing.record_append`
- 0.8.5: add api: `zq_tracing.set_start_timestamp`
- 0.8.4: fix bug, add `colorful` to dependency
- 0.8.3: add `zq_files`
- 0.8.2: support `from zq_tools.zq_logger import default_logger as logger`
- 0.8.0: use `add_log_file` to add a log file to the logger.
- 0.7.0: re-think the color print logic
- 0.6.0: rename function: logger.print* --> logger.prank*
- 0.5.9: set level of print bewteen DEBUG and INFO, add `*_root` functions
- 0.5.8: implement `__len__` and `__iter__` for zq_cycle
- 0.5.6: add colors for different rank. add filter for zq_logger
- 0.5.5: disable color by default for `print` and `print_all`
- 0.5.3: zq_logger supports `print`, `print_all`, `set_rank`
- 0.5.1: move tag to ahead of msg
- 0.5.0: zq_logger supports color API, add tag
- 0.4.1: fix bug of zq_cycle
- 0.4.0: add zq_cycle
- 0.3.6: default unit of timestamp: us
- 0.3.5: support manually specifiying tid/pid when calling `zq_tracing.record_*`
- 0.3.4: fix bug
- 0.3.3: add default logger, call `zq_logger.get_logger()`, return a pre-defined logger
- 0.3.2: add async record, support nested and ordered tracing events
- 0.3.1: add install dependencies
- 0.3.0: output `pathname` instead of `filename`, better support for IDE's jumping function


# TODO:
- add setLogPath()