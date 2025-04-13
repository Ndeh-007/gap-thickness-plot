from uuid import uuid4
from PySide6 import QtCore
import traceback


class ThreadModel(QtCore.QThread):
    onFinished = QtCore.Signal(str)
    onStarted = QtCore.Signal(str)

    def __init__(self, opts: dict, id: str = None):
        super().__init__()
        self.__id = id
        if id is None:
            self.__id = str(uuid4())
        self.__opts = {
            "task": None,
            "params": None,
            "on_complete": None,
            "on_error": None,
            "on_started": None,
            "results": None,
            "failed": False,
            "error": None,
        }

        # sets the opts
        self.setOpts(opts)

        # reconnect the signals to carry the thread id
        self.started.connect(lambda: self.onStarted.emit(self.__id))
        self.finished.connect(lambda: self.onFinished.emit(self.__id))

    def id(self):
        return self.__id

    def opts(self):
        return self.__opts

    def setOpts(self, opts: dict):
        for k, v in opts.items():
            self.__opts[k] = v

    
    def run(self) -> None:
        try:
            if self.__opts.get("params") is None:
                self.__opts["results"] = self.__opts["task"]()
            else:
                self.__opts["results"] = self.__opts["task"](self.__opts["params"])

            # flag that no error occurred
            self.__opts["failed"] = False
        except Exception as e:
            tb = traceback.format_exc()
            traceback.print_exc()

            # collect the traceback
            self.__opts["error"] = tb

            # flag that an error occurred
            self.__opts["failed"] = True

            
            
