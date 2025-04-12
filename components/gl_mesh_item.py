import pyqtgraph.opengl as gl
from PySide6.QtGui import QColor

class VMeshItem(gl.GLMeshItem):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def setEdgeColor(self, color: QColor | tuple[float, float, float, float]) -> None:
        c = color
        if isinstance(color, QColor):
            c = color.getRgbF()
        self.opts.update({"edgeColor": c})
        self.update()
