from PySide6 import QtWidgets, QtCore, QtGui
import pyqtgraph.opengl as gl
import components as comp
import utils as utils


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gap Thickness Plotter")
        self.setGeometry(100, 100, 600, 400)

        # define the ui control toolbar actions
        # clear, add, remove, save, load, export, import
        self.actionClear = QtGui.QAction("Clear", self)
        self.actionAdd = QtGui.QAction("Add", self)
        self.actionRemove = QtGui.QAction("Remove", self)
        self.actionSave = QtGui.QAction("Save", self)
        self.actionLoad = QtGui.QAction("Load", self)
        self.actionExport = QtGui.QAction("Export", self)
        self.actionImport = QtGui.QAction("Import", self)

        self.actionClear.setData("clear")
        self.actionAdd.setData("add")
        self.actionRemove.setData("remove")
        self.actionSave.setData("save")
        self.actionLoad.setData("load")
        self.actionExport.setData("export")
        self.actionImport.setData("import")

        self.console = QtWidgets.QTextEdit()
        self.glView = comp.VBaseGLViewWidget()
        self.controlToolBar = QtWidgets.QToolBar()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.glView)
        layout.addWidget(self.controlToolBar)
        layout.addWidget(self.console)
        layout.setStretch(0, 1)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

        self.__meshItems = {}

        self.__initialize()
        self.__configure()
        self.__connectSignals()

    def __initialize(self):
        # populate the toolbar with actions
        self.controlToolBar.addAction(self.actionLoad)
        self.controlToolBar.addSeparator()
        self.controlToolBar.addAction(self.actionAdd)
        self.controlToolBar.addAction(self.actionSave)
        self.controlToolBar.addSeparator()
        self.controlToolBar.addAction(self.actionClear)
        self.controlToolBar.addAction(self.actionRemove)
        self.controlToolBar.addSeparator()
        self.controlToolBar.addAction(self.actionImport)
        self.controlToolBar.addAction(self.actionExport)

        # make console only read only
        self.console.setReadOnly(True)

        # create a grid item
        grid_item = gl.GLGridItem()
        grid_item.setColor(utils.appColors.medium_rbg)
        self.glView.addItem(grid_item)

        # add an axis item
        axis_item = gl.GLAxisItem()
        self.glView.addItem(axis_item)

    def __configure(self):
        self.controlToolBar.actionTriggered.connect(self.__onToolBarActionTriggered)
        self.controlToolBar.setMovable(False)

    def __connectSignals(self):
        utils.signalBus.onError.connect(self.log)

    # region event handlers
    def __onToolBarActionTriggered(self, action: QtGui.QAction):
        action_type = action.data()
        if action_type == "clear":
            self.__clear()
        elif action_type == "add":
            self.__add()
        elif action_type == "remove":
            self.__remove()
        elif action_type == "save":
            self.__save()
        elif action_type == "load":
            self.__load()
        elif action_type == "export":
            self.__export()
        elif action_type == "import":
            self.__import()
        else:
            self.log(f"Unknown action: {action_type}")

    # endregion

    # region action workers

    def __clear(self):
        for item in self.__meshItems.values():
            self.glView.removeItem(item)

    def __add(self):
        pass

    def __remove(self):
        pass

    def __save(self):
        pass

    @utils.errorhandler
    def __load(self):
        "create a single mesh item and append ot ui"
        meshdata = utils.create_slab_mesh()
        mesh_item = utils.create_mesh_item({"meshdata": meshdata})

        self.glView.addItem(mesh_item)

        self.__meshItems[f"mesh_item_{len(self.__meshItems)}"] = mesh_item

    def __export(self):
        pass

    def __import(self):
        pass

    # endregion

    # region workers

    def __log(self, msg: str, color: str = utils.appColors.dark_rbg):
        self.console.moveCursor(QtGui.QTextCursor.MoveOperation.End)

        cursor = self.console.textCursor()

        charFormat = QtGui.QTextCharFormat()
        charFormat.setForeground(QtGui.QColor(color))

        cursor.setCharFormat(charFormat)
        cursor.insertText("\n")
        cursor.insertText(msg.strip())

        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def log(self, data: str | dict):
        prefix = "[MSG] "
        if isinstance(data, str):
            self.__log(prefix + data)

        if isinstance(data, dict):
            if data.get("type") == "error":
                prefix = "[ERROR] "
                self.__log(prefix + data.get("text"), utils.appColors.danger_rbg)
            elif data.get("type") == "warning":
                prefix = "[WARNING] "
                self.__log(prefix + data.get("text"), utils.appColors.warning_shade_rbg)
            elif data.get("type") == "event":
                prefix = "[INFO] "
                self.__log(
                    prefix + data.get("text"), utils.appColors.tertiary_shade_rbg
                )
            elif data.get("type") == "success":
                prefix = "[SUCCESS] "
                self.__log(prefix + data.get("text"), utils.appColors.success_shade_rbg)
            else:
                self.__log(prefix + data.get("text"))

    def logError(self, msg: str):
        self.log({"text": msg, "type": utils.appColors.danger_rbg})

    def logEvent(self, msg: str):
        self.log({"text": msg, "type": utils.appColors.tertiary_rbg})

    def logWarning(self, msg: str):
        self.log({"text": msg, "type": utils.appColors.warning_rbg})

    # endregion

    # region decorators

    # endregion