"""Research Corp workers — all specialized agents."""
from .base import BaseWorker
from .researcher import run as researcher_run
from .coder import run as coder_run
from .analyst import run as analyst_run
from .reporter import run as reporter_run
