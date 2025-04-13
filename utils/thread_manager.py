import models as models
from .signal_bus import signalBus

class ThreadManager:
    def __init__(self):
        
        self.__models: dict[str, models.ThreadModel] = {}
        self.__gc = []

    def launchThread(self, model: models.ThreadModel):
        # connect the signals and slots
        model.onFinished.connect(self.__onFinished)
        model.onStarted.connect(self.__onStarted)

        # collect the thread
        self.__models[model.id()] = model

        model.start()

    def __onFinished(self, pid: str):
        m = self.__models.get(pid)
        if m is None:
            return
        
        c_task = m.opts()["on_complete"]
        task_failed: bool = m.opts()["failed"]
        if c_task is None:
            if task_failed:
                signalBus.onMessage.emit(f"Task with id <{pid}> Failed with Error \ {'v' * 20}", )
                signalBus.onMessage.emit(m.opts()["error"], )
            else:
                signalBus.onMessage.emit(f"Task with id <{pid}> Completed", )

        else:
            opts = {
                "failed": task_failed,
                "error": m.opts()["error"],
                "results": m.opts()["results"],
            }
            c_task(opts)

        self.__unstage(pid)

    def __onStarted(self, pid: str):
        
        m = self.__models.get(pid)
        if m is None:
            signalBus.onMessage.emit(f"Cannot start task with id <{pid}> not found")
            return
        
        c_task = m.opts()["on_started"]
        if c_task is None:
            signalBus.onMessage.emit({"text": f"Task with id <{pid}> started", "type":"warning"})
        else:
            c_task()

    def __unstage(self, id: str):
        """
        remove the thread from the active list
        """
        self.__gc.append(self.__models.pop(id))

    def kill(self, id:str):
        m = self.__models.get(id)
        if m is not None:
            m.terminate()

    def purge(self):
        "empty the garbage collector"
        self.__gc.clear()
        