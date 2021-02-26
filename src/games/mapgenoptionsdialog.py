from PyQt5 import QtCore, QtWidgets, QtGui
import util
import config

FormClass, BaseClass = util.THEME.loadUiType("games/mapgen.ui")

class MapGenDialog(FormClass, BaseClass):
	def __init__(self, parent, *args, **kwargs):
		BaseClass.__init__(self, *args, **kwargs)

		self.setupUi(self)

		util.THEME.stylesheets_reloaded.connect(self.load_stylesheet)
		self.load_stylesheet()

		self.parent = parent

		self.generationType.currentIndexChanged.connect(self.generationTypeChanged)
		self.numberOfSpawns.currentIndexChanged.connect(self.numberOfSpawnsChanged)
		self.mapSize.currentIndexChanged.connect(self.mapSizeChanged)
		self.generateMapButton.clicked.connect(self.generateMap)
		self.saveMapGenSettingsButton.clicked.connect(self.saveMapGenPrefs)
		self.resetMapGenSettingsButton.clicked.connect(self.resetMapGenPrefs)

		self.random_buttons = [
			 self.landRandomDensity
			,self.plateausRandomDensity
			,self.mountainsRandomDensity
			,self.rampsRandomDensity
			,self.mexRandomDensity
			,self.reclaimRandomDensity
		]
		self.sliders = [
			 self.landDensity
			,self.plateausDensity
			,self.mountainsDensity
			,self.rampsDensity
			,self.mexDensity
			,self.reclaimDensity
		]

		self.option_frames = [
			 self.landOptions
			,self.plateausOptions
			,self.mountainsOptions
			,self.rampsOptions
			,self.mexOptions
			,self.reclaimOptions
		]

		for random_button in self.random_buttons:
			random_button.setChecked(config.Settings.get("mapGenerator/{}".format(random_button.objectName()), type=bool, default=True))
			random_button.toggled.connect(self.updateVisibilities)

		for slider in self.sliders:
			slider.setValue(config.Settings.get("mapGenerator/{}".format(slider.objectName()), type=int, default=0))
		
		self.generation_type = None
		self.number_of_spawns = None
		self.map_size = None
		self.generationType.setCurrentIndex(config.Settings.get("mapGenerator/generationTypeIndex", type=int, default=0))
		self.numberOfSpawns.setCurrentIndex(config.Settings.get("mapGenerator/numberOfSpawnsIndex", type=int, default=0))
		self.mapSize.setCurrentIndex(config.Settings.get("mapGenerator/mapSizeIndex", type=int, default=0))
		
		self.updateVisibilities()

	def load_stylesheet(self):
		self.setStyleSheet(util.THEME.readstylesheet("client/client.css"))

	@QtCore.pyqtSlot(int)
	def numberOfSpawnsChanged(self, index):
		self.number_of_spawns = 2 * (index + 1)
	
	@QtCore.pyqtSlot(int)
	def mapSizeChanged(self, index):
		if index == -1 or index == 0:
			self.map_size = 256
		elif index == 1:
			self.map_size = 512
		elif index == 2:
			self.map_size = 1024

	@QtCore.pyqtSlot(int)
	def generationTypeChanged(self, index):
		if index == -1 or index == 0:
			self.generation_type = "casual"
		elif index == 1:
			self.generation_type = "tournament"
		elif index == 2:
			self.generation_type = "blind"
		elif index == 3:
			self.generation_type = "unexplored"

		self.updateVisibilities()
	
	@QtCore.pyqtSlot()
	def updateVisibilities(self):
		for random_button in self.random_buttons:
			option_frame = self.option_frames[self.random_buttons.index(random_button)]
			if self.generation_type == "tournament":
				random_button.setEnabled(False)
				random_button.setChecked(True)
				option_frame.setEnabled(False)
			else:
				random_button.setEnabled(True)
				if random_button.isChecked():
					option_frame.setEnabled(False)
				else:
					option_frame.setEnabled(True)
	
	@QtCore.pyqtSlot()
	def saveMapGenPrefs(self):
		config.Settings.set("mapGenerator/generationTypeIndex", self.generationType.currentIndex())
		config.Settings.set("mapGenerator/mapSizeIndex", self.mapSize.currentIndex())
		config.Settings.set("mapGenerator/numberOfSpawnsIndex", self.numberOfSpawns.currentIndex())
		for random_button in self.random_buttons:
			config.Settings.set("mapGenerator/{}".format(random_button.objectName()), random_button.isChecked())
		for slider in self.sliders:
			config.Settings.set("mapGenerator/{}".format(slider.objectName()), slider.value())
		self.done(1)

	@QtCore.pyqtSlot()
	def resetMapGenPrefs(self):
		for random_button in self.random_buttons:
			random_button.setChecked(True)
		for slider in self.sliders:
			slider.setValue(0)

		self.generationType.setCurrentIndex(0)
		self.mapSize.setCurrentIndex(0)
		self.numberOfSpawns.setCurrentIndex(0)

	@QtCore.pyqtSlot()
	def generateMap(self):
		map_ = self.parent.client.map_generator.generateMap(args=self.setArguments())
		if map_:
			self.parent.setupMapList()
			self.parent.set_map(map_)
			self.saveMapGenPrefs()

	def setArguments(self):
		args = []
		args.append("--map-size")
		args.append(str(self.map_size))
		args.append("--spawn-count")
		args.append(str(self.number_of_spawns))

		if self.generation_type == "tournament":
			args.append("--tournament-style")
		elif self.generation_type == "blind":
			args.append("--blind")
		elif self.generation_type == "unexplored":
			args.append("--unexplored")

		slider_args = [
			 ["--land-density", None]
			,["--plateau-density", None]
			,["--mountain-density", None]
			,["--ramp-density", None]
			,["--mex-density", None]
			,["--reclaim-density", None]
		]
		for slider in self.sliders:
			if slider.isEnabled():
				if slider == self.landDensity:
					slider_args[self.sliders.index(slider)][1] = float(1 - (slider.value() / 127))
				else:
					slider_args[self.sliders.index(slider)][1] = float(slider.value() / 127)
		
		for arg_key, arg_value in slider_args:
			if arg_value is not None:
				args.append(arg_key)
				args.append(str(arg_value))

		return args