from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    onError = Signal(object)

signalBus = SignalBus()
