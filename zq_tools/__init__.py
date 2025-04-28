name = "zq_tools"
from . import zq_tracing
from . import zq_cycle
from . import zq_files
from . import zq_decorator
from . import zq_bogger

from .zq_bogger import default_bogger as bogger
zq_logger = zq_bogger

# check if has logger in global
if not hasattr(globals(), "logger"):
    zq_logger = zq_bogger
    logger = bogger # for backward compatibility
