import threading
from contextlib import contextmanager

@contextmanager
def suppress_thread_exceptions():
    """
    Context manager which causes exceptions in threads not to
    be printed. See https://stackoverflow.com/questions/63206653/ .
    """
    try:
        orig = threading.excepthook
        threading.excepthook = lambda a: None
        try:
            yield
        finally:
            threading.excepthook = orig
    except AttributeError:

        # Python 3.6 doesn't have threading.excepthook,
        # but everything else in kepi works. So if it's
        # missing, we work around that.

        print("""Warning:
        You are running a version of Python without threading.excepthook.
        You will see spurious error messages during testing.
        """)

        try:
            yield
        finally:
            pass
