# zq_logger
generates a logger, preformatted with the file name, line number information, differrent levels of color, and can be output in the console and written to a file at the same time.

![](https://raw.githubusercontent.com/zzqq2199/pic_for_public/master/img/20220608140039.png)

# zq_tracing
help generate json file used in `chrome://tracing`

![](https://raw.githubusercontent.com/zzqq2199/pic_for_public/master/img/20220608134508.png)


# Release Notes
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