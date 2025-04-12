from .signal_bus import signalBus
import traceback


def errorhandler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            msg = f"{func.__name__}: {str(e)} \n {tb}"
            signalBus.onError.emit({"text": msg, "type": "error"})
            print(msg)

    return wrapper
