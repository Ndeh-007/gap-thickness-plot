from PySide6 import QtWidgets, QtCore, QtGui
import pyqtgraph.opengl as gl
import components as comp
import utils as utils
import models as models
import os
from pathlib import Path


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gap Thickness Plotter")
        self.setGeometry(100, 100, 1000, 800)

        self.actionClear = QtGui.QAction("Clear", self)
        self.actionDraw = QtGui.QAction("Draw", self)
        self.actionStopAnimation = QtGui.QAction("Stop", self)
        self.actionAnimate = QtGui.QAction("Animate", self)
        self.actionLoad = QtGui.QAction("Load", self)
        self.actionExport = QtGui.QAction("Export", self)
        self.actionImport = QtGui.QAction("Import", self)
        self.thicknessProfileComboBox = QtWidgets.QComboBox(self)
        self.slabPointsInput = QtWidgets.QLineEdit(self)
        self.baseThicknessInput = QtWidgets.QLineEdit(self)
        self.dataFileInput = QtWidgets.QLineEdit(self)
        self.selectBaseFile = QtWidgets.QPushButton("Browse ...", self)
        self.depthDetailLevelComboBox = QtWidgets.QComboBox(self)
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setFixedHeight(5)
        self.progressBar.setRange(0, 0)
        self.progressBar.setStyleSheet(utils.PROGESS_BAR_STYLE)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.drawFacesCheckbox = QtWidgets.QCheckBox("Faces ")
        self.drawEdgesCheckbox = QtWidgets.QCheckBox("Edges ")

        self.actionClear.setData("clear")
        self.actionDraw.setData("draw")
        self.actionStopAnimation.setData("stop")
        self.actionAnimate.setData("animate")
        self.actionLoad.setData("load")
        self.actionExport.setData("export")
        self.actionImport.setData("import")

        self.console = QtWidgets.QTextEdit()
        self.glView = comp.VBaseGLViewWidget()
        self.controlToolBar = QtWidgets.QToolBar()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.progressBar)
        layout.addWidget(self.glView)
        layout.addWidget(self.controlToolBar)
        layout.addWidget(self.slider)
        layout.addWidget(self.console)
        layout.setStretch(1, 1)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

        self.__meshItems = {}
        self.__conf = {
            "frame_index": None,
            "thickness_profile": "CW",
            "z_points": 40,
            "y_points": 20,
            "base_thickness": 0.05,
            "depth_detail_level": 25,
            "tmd": 0.0,
            "bmd": 100.0,
            "images": [],
            "data_file": os.path.join(os.getcwd(), "data", "results", "csave.h5"),
            "draw_edges": False,
            "draw_faces": True,
            "rotations": [],
            # "rotations": (180, 0, 0, 1, False),
        }

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(17)  # 60 fps

        self.manager = utils.ThreadManager()

        self.__initialize()
        self.__configure()
        self.__connectSignals()

    @utils.errorhandler
    def __initialize(self):
        # populate the toolbar with actions
        self.controlToolBar.addAction(self.actionLoad)
        self.controlToolBar.addSeparator()
        self.controlToolBar.addAction(self.actionDraw)
        self.controlToolBar.addAction(self.actionAnimate)
        self.controlToolBar.addAction(self.actionStopAnimation)
        self.controlToolBar.addSeparator()
        self.controlToolBar.addAction(self.actionClear)
        self.controlToolBar.addSeparator()
        self.controlToolBar.addAction(self.actionImport)
        self.controlToolBar.addAction(self.actionExport)
        self.controlToolBar.addSeparator()

        s1 = QtWidgets.QWidget()
        s2 = QtWidgets.QWidget()
        s3 = QtWidgets.QWidget()
        s1.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        s2.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        s3.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        self.controlToolBar.addWidget(s1)
        self.controlToolBar.addWidget(QtWidgets.QLabel("Thickness Profile: "))
        self.controlToolBar.addWidget(self.thicknessProfileComboBox)
        self.controlToolBar.addSeparator()
        self.controlToolBar.addWidget(QtWidgets.QLabel("nz points: "))
        self.controlToolBar.addWidget(self.slabPointsInput)
        self.controlToolBar.addSeparator()
        self.controlToolBar.addWidget(QtWidgets.QLabel("Base Thickness: "))
        self.controlToolBar.addWidget(self.baseThicknessInput)
        self.controlToolBar.addWidget(s2)
        self.controlToolBar.addWidget(QtWidgets.QLabel("h5 File: "))
        self.controlToolBar.addWidget(self.dataFileInput)
        self.controlToolBar.addWidget(self.selectBaseFile)
        self.controlToolBar.addWidget(s3)
        self.controlToolBar.addWidget(self.drawEdgesCheckbox)
        self.controlToolBar.addWidget(self.drawFacesCheckbox)
        self.controlToolBar.addWidget(QtWidgets.QLabel("Depth Detail Level: "))
        self.controlToolBar.addWidget(self.depthDetailLevelComboBox)

        # populate the thickness profile combobox
        self.slabPointsInput.setPlaceholderText("number of points")
        self.slabPointsInput.setText(str(self.__conf["z_points"]))
        self.baseThicknessInput.setText(str(self.__conf["base_thickness"]))
        self.baseThicknessInput.setPlaceholderText("base thickness")
        self.dataFileInput.setText(str(self.__conf["data_file"]))
        self.dataFileInput.setPlaceholderText(".h5 file")
        for k, opts in utils.THICKNESS_PROFILES.items():
            self.thicknessProfileComboBox.addItem(opts["name"], k)
        self.thicknessProfileComboBox.setCurrentIndex(3)

        # populate the depth detail level combobox
        for level in utils.DEPTH_DETAIL_LEVELS:
            self.depthDetailLevelComboBox.addItem(level["name"], level["value"])
        self.depthDetailLevelComboBox.setCurrentIndex(1)

        # make console only read only
        self.console.setReadOnly(True)

        # hide the progress bar
        self.progressBar.hide()

        # process the timer
        self.timer.timeout.connect(self.__updateSlider)

        # populat the checkboxes
        self.drawEdgesCheckbox.setChecked(self.__conf["draw_edges"])
        self.drawFacesCheckbox.setChecked(self.__conf["draw_faces"])

        # draw and axis item
        self.__clear()  # clear the scene

    @utils.errorhandler
    def __configure(self):
        self.controlToolBar.actionTriggered.connect(self.__onToolBarActionTriggered)
        self.controlToolBar.setMovable(False)

        self.slabPointsInput.textChanged.connect(self.__onOptionsChanged)
        self.baseThicknessInput.textChanged.connect(self.__onOptionsChanged)
        self.dataFileInput.textChanged.connect(self.__onOptionsChanged)
        self.selectBaseFile.pressed.connect(self.__onSelectFile)
        self.thicknessProfileComboBox.currentIndexChanged.connect(
            self.__onOptionsChanged
        )
        self.depthDetailLevelComboBox.currentIndexChanged.connect(
            self.__onOptionsChanged
        )

        self.slider.valueChanged.connect(self.__onSliderValueChanged)
        self.drawFacesCheckbox.checkStateChanged.connect(self.__onSceneOptionsChanged)
        self.drawEdgesCheckbox.checkStateChanged.connect(self.__onSceneOptionsChanged)

    @utils.errorhandler
    def __connectSignals(self):
        utils.signalBus.onMessage.connect(self.log)

    # region event handlers
    @utils.errorhandler
    def prime(self):
        self.logEvent("Initialization complete. Drawing the initial mesh item.")
        self.__load()

    @utils.errorhandler
    def __onSliderValueChanged(self, value: int):

        # get the new frame
        if value not in range(len(self.__conf["images"])):
            self.log(
                f"Slider value: <{value}> out of bounds <0, {len(self.__conf['images']) - 1}>"
            )
            return

        self.__conf["frame_index"] = value

        # draw
        self.draw_frame()

    @utils.errorhandler
    def __onSelectFile(self, _=None):

        #  if filter keys are provided
        f = QtWidgets.QFileDialog.getOpenFileName(
            parent=self, filter="HDF5 files (*.h5)"
        )[0]

        # if no file was selected, return nothing
        if len(f) == 0:
            return None
        # set the text
        self.dataFileInput.setText(f.replace("/", "\\"))

    @utils.errorhandler
    def __onSceneOptionsChanged(self, _=None):

        # collec the check boxes
        self.__conf["draw_faces"] = self.drawFacesCheckbox.isChecked()
        self.__conf["draw_edges"] = self.drawEdgesCheckbox.isChecked()

        # redraw the cell
        self.__reDrawCell()

    @utils.errorhandler
    def __onOptionsChanged(self, _=None):
        # update the configuration based on the user input
        self.__conf["thickness_profile"] = self.thicknessProfileComboBox.currentData()
        self.__conf["depth_detail_level"] = self.depthDetailLevelComboBox.currentData()

        # collect the data file
        h5File = self.dataFileInput.text()
        if Path.is_file(Path(h5File)) and h5File.endswith(".h5"):
            self.__conf["data_file"] = h5File
        else:
            self.logError(f"Input File <{h5File}> does not exist or is not a .h5 file")

        # collect the nz points
        try:
            self.__conf["z_points"] = int(self.slabPointsInput.text())
        except ValueError:
            self.logError("Invalid number of points.")
            self.__conf["z_points"] = 40
            self.slabPointsInput.setText(str(self.__conf["z_points"]))

        # collect the base thickness
        try:
            self.__conf["base_thickness"] = float(self.baseThicknessInput.text())
        except ValueError:
            self.logError("Invalid base thickness.")
            self.__conf["base_thickness"] = 0.05
            self.baseThicknessInput.setText(str(self.__conf["base_thickness"]))

        self.logEvent(f"Updated configuration")

        # draw the mesh item based on the new configuration

    @utils.errorhandler
    def __onToolBarActionTriggered(self, action: QtGui.QAction):
        action_type = action.data()
        if action_type == "clear":
            self.__clear()
        elif action_type == "draw":
            self.__draw()
        elif action_type == "stop":
            self.__stopAnimation()
        elif action_type == "animate":
            self.__animate()
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

    @utils.errorhandler
    def __updateSlider(self):
        "when timer fires, shift the slider on step forward"
        if self.__conf["frame_index"] is None:
            return

        self.slider.setValue(self.__conf["frame_index"] + 1)

    @utils.errorhandler
    def __stopAnimation(self):
        # from the loaded images,
        # construct the base meshdata frame objects with the various colors

        self.timer.stop()
        self.__conf["frame_index"] = 0
        self.progressBar.hide()

    @utils.errorhandler
    def __animate(self):
        frames = self.__conf["images"]
        if len(frames) == 0:
            self.logWarning("No images to animate.")
            return
        self.logEvent("Animating images...")

        self.__conf["frame_index"] = 0
        self.timer.start()
        self.progressBar.show()

    def draw_frame(self):
        def task(i: int):
            self.__updateCell(i)
            return i

        def on_complete(res):
            if res["failed"]:
                self.timer.stop()
                self.__conf["frame_index"] = None
                self.logError(res["error"])
            else:
                cur_index = res["results"]
                if cur_index is None:
                    return

                if cur_index + 1 == len(self.__conf["images"]):
                    return self.__stopAnimation()

                # self.__conf['frame_index'] = cur_index + 1

        def on_started():
            self.logEvent(
                f"DRAW_FRAME_{self.__conf['frame_index'] + 1}/{len(self.__conf['images'])}"
            )

        thread = models.ThreadModel(
            {
                "task": task,
                "params": self.__conf["frame_index"],
                "on_complete": on_complete,
                "on_started": on_started,
            },
            f"DRAW_FRAME_{self.__conf['frame_index'] + 1}/{len(self.__conf['images'])}",
        )

        self.manager.launchThread(thread)

    @utils.errorhandler
    def __load(self):
        file_path = self.__conf["data_file"]

        def task(file: str):

            _res_task = utils.load_frames(file)

            profile = utils.THICKNESS_PROFILES[self.__conf["thickness_profile"]][
                "equation"
            ](_res_task["nxi"], self.__conf["base_thickness"])

            props = {
                "thickness_profile": profile,
                "y_points": _res_task["nzeta"],
                "z_points": _res_task["nxi"],
                "tmd": _res_task["tmd"],
                "bmd": _res_task["bmd"],
                "text_positions": utils.create_depth_vertex_array(
                    {
                        "thickness_profile": profile,
                        "plane": "yx",
                        "size": 1,
                        "anchor": "center",
                    }
                ),
                "detail_level": self.__conf["depth_detail_level"] / 100,
                "text_color": utils.appColors.light_rbg,
                "images": _res_task["images"],
            }

            _res_task["meshdata"] = utils.create_slab_mesh(props)["meshdata"]
            mesh_item = utils.create_mesh_item(
                {
                    "meshdata": _res_task["meshdata"][0],
                    "color": utils.appColors.medium_rbg,
                    "rotations": self.__conf["rotations"],
                    "draw_edges": self.__conf["draw_edges"],
                    "draw_faces": self.__conf["draw_faces"],
                }
            )
            text_items = utils.create_text_items(props)

            # collect the items
            _res_task["depth_labels"] = text_items
            _res_task["cell"] = mesh_item

            # resolve task
            return _res_task

        def on_complete(_res_dict):
            if _res_dict["failed"]:
                self.logError(_res_dict["error"])
            else:
                opts = _res_dict["results"]
                self.__conf["images"] = opts["images"]
                self.__conf["y_points"] = opts["nzeta"]
                self.__conf["z_points"] = opts["nxi"]
                self.__conf["tmd"] = opts["tmd"]
                self.__conf["bmd"] = opts["bmd"]
                self.__conf["unit"] = opts["unit"]
                self.__conf["meshdata"] = opts["meshdata"]
                self.__conf["frame_index"] = 0
                self.__meshItems["depth_labels"] = opts["depth_labels"]
                self.__meshItems["cell"] = opts["cell"]

                self.__draw()

                # prime the slide
                self.slider.setMinimum(0)
                self.slider.setMaximum(len(opts["meshdata"]) - 1)
                self.slider.setSingleStep(1)
                self.slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
                self.slider.setTickInterval(5)

                self.logSuccess(f"Loaded {opts['time_step']} images from {file_path}.")
                self.progressBar.hide()

        def on_started():
            self.progressBar.show()
            self.logEvent("Loading data from sources and constructing mesh...")

        thread = models.ThreadModel(
            {
                "params": file_path,
                "on_complete": on_complete,
                "on_started": on_started,
                "task": task,
            },
            id="LOAD_DATA",
        )
        self.manager.launchThread(thread)

    @utils.errorhandler
    def __export(self):
        pass

    @utils.errorhandler
    def __import(self):
        pass

    # endregion

    # region scene workers
    @utils.errorhandler
    def __reDrawCell(self):
        # remove the cell
        # create a new cell with new configurations
        # append the new mesh item to the view
        # update the collector
        # update the frame at index

        self.glView.removeItem(self.__meshItems["cell"])
        mesh_item = utils.create_mesh_item(
            {
                "empty": True,
                "color": utils.appColors.medium_shade_rbg,
                "rotations": self.__conf["rotations"],
                "draw_edges": self.__conf["draw_edges"],
                "draw_faces": self.__conf["draw_faces"],
            }
        )
        self.glView.addItem(mesh_item)
        self.__meshItems["cell"] = mesh_item
        self.__updateCell(self.__conf["frame_index"])

    @utils.errorhandler
    def __draw(self, _=None):
        "create a single mesh item and append to ui"
        # add the them to view
        if "depth_labels" not in self.__meshItems.keys():
            self.logError("Cannot draw depth labels, missing key <depth_labels>")
        else:
            for item in self.__meshItems["depth_labels"]:
                self.glView.addItem(item)

        if "cell" not in self.__meshItems.keys():
            self.logError("Cannot draw mesh, missing key <cell>")
        else:
            self.glView.addItem(self.__meshItems["cell"])

    @utils.errorhandler
    def __updateCell(self, frame_index: int):
        if frame_index < len(self.__conf["meshdata"]):
            cell: gl.GLMeshItem = self.__meshItems["cell"]
            cell.setMeshData(meshdata=self.__conf["meshdata"][frame_index])

    @utils.errorhandler
    def __clear(self):

        # first clear the scene
        self.glView.clear()

        # add the axis item
        axis_item = gl.GLAxisItem()
        self.glView.addItem(axis_item)

        # add the coordinates as text items
        for axis in utils.AXIS_LABELS.values():
            text_item = gl.GLTextItem(
                text=axis["label"], color=QtGui.QColor(axis["color"]), pos=axis["pos"]
            )
            self.glView.addItem(text_item)

        # delete all mesh items
        self.__meshItems.clear()

        self.logEvent("Cleared all mesh items.")

    # endregion

    # region log workers

    @utils.errorhandler
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

    @utils.errorhandler
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

    @utils.errorhandler
    def logError(self, msg: str):
        self.log({"text": msg, "type": "error"})

    @utils.errorhandler
    def logEvent(self, msg: str):
        self.log({"text": msg, "type": "event"})

    @utils.errorhandler
    def logWarning(self, msg: str):
        self.log({"text": msg, "type": "warning"})

    @utils.errorhandler
    def logSuccess(self, msg: str):
        self.log({"text": msg, "type": "success"})

    # endregion
