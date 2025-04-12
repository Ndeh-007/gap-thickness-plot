import pyqtgraph.opengl as gl
from pyqtgraph import Vector
from PySide6.QtCore import Qt


class VBaseGLViewWidget(gl.GLViewWidget):
    def __init__(self):
        super().__init__()
        self.__panSensitivity = 10
        self.__pan_active = True
        self.last_pos = None
        self.setBackgroundColor("#ffffff")

    # region setters
    def setPanSensitivity(self, value: int):
        self.__panSensitivity = value

    # endregion
    # region getters
    def panSensitivity(self):
        return self.__panSensitivity

    # endregion

    # region override

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.RightButton:
            self.__pan_active = True
            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.__pan_active = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.__pan_active and self.last_pos is not None:
            delta = event.pos() - self.last_pos
            self.pan(delta.x(), delta.y(), 0, relative="view")
            self.last_pos = event.pos()
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        # Check if the key event is a directional key (Up, Down, Left, or Right)
        if event.key() == Qt.Key.Key_Up:
            self.__panView(0, 0, self.__panSensitivity)
        elif event.key() == Qt.Key.Key_Down:
            self.__panView(0, 0, -self.__panSensitivity)
        elif event.key() == Qt.Key.Key_Left:
            self.__panView(self.__panSensitivity, 0, 0)
        elif event.key() == Qt.Key.Key_Right:
            self.__panView(-self.__panSensitivity, 0, 0)

    # endregion

    # region items
    def __panView(self, dx, dy, dz):
        self.pan(dx, dy, dz, "view")

    # endregion

    # region workers
    def rePositionView(self):
        self.reset()
        self.setCameraPosition(
            pos=Vector(0, 0, 0),
            distance=100,
        )

    # endregion
