import threading
from contextlib import contextmanager

@contextmanager
def suppress_thread_exceptions():
    """
    Context manager which causes exceptions in threads not to
    be printed. See https://stackoverflow.com/questions/63206653/ .
    """
    orig = threading.excepthook
    threading.excepthook = lambda a: None
    try:
        yield
    finally:
        threading.excepthook = orig
