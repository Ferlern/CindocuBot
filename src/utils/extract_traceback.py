import traceback
from types import TracebackType
from typing import Optional


def extract_traceback(traceback_type: Optional[TracebackType]) -> str:
    stack_summary = traceback.extract_tb(traceback_type, limit=20)
    traceback_list = traceback.format_list(stack_summary)
    return ''.join(traceback_list)
