Log Config
==========

The user can specify a logging configuration to the command-line shell utility ```cloudbackup-shell```.
This is a standard Python Logging INI configuration. Below is a basic example:

[loggers]
keys=root,shell

[formatters]
keys = standard

[handlers]
keys=rotatelogfile

[logger_root]
level = DEBUG
handlers = rotatelogfile

[logger_shell]
level = DEBUG
handlers = rotatelogfile
qualname=shell_logger

[logger_py.warnings]
handlers = rotatelogfile

[handler_console]
level = DEBUG
class = logging.StreamHandler
formatter = standard

[handler_logfile]
level = DEBUG
class = logging.FileHandler
formatter = standard
filename = .python-cloudbackup-sdk.log

[handler_syslog]
level = DEBUG
class = logging.handlers.SysLogHandler
formatter = standard
address = /dev/log

[handler_rotatelogfile]
level = DEBUG
class = logging.handlers.RotatingFileHandler
formatter = standard
args=('.python-cloudbackup-sdk.log', 400000000, 2)

[formatter_standard]
format = %(asctime)s %(levelname)-5.5s [%(name)s_%(lineno)d][%(threadName)s] : %(message)s
