from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    onMessage = Signal(object)

signalBus = SignalBus()
