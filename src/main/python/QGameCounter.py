from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QThreadPool, QFile, QTextStream, QCoreApplication, QSettings, QSize, QPoint
from PyQt5.QtGui import QKeySequence, QIcon, QImage, QPixmap, QKeyEvent, QGuiApplication
from PyQt5.QtWidgets import (
    QMessageBox, QMainWindow, QShortcut,
    QMenu, QAction, qApp,
    QGraphicsScene, QGraphicsView, QGraphicsItem,
    QDockWidget, QWidget, QToolBar, QFileDialog
)

from QImageGrid import QImageGridViewer
from QImagePainter import QImagePainter
from QGameCountTracker import QGameCountTracker
from QWorker import Worker

class QGameCounter(QMainWindow):

    def __init__(self):
        super().__init__()

        self.imageGridViewer = QImageGridViewer()
        self.imagePainter = QImagePainter()
        self.tracker = QGameCountTracker()

        self.setCentralWidget(self.imagePainter)

        self.imageGridDock = QDockWidget('Grid Viewer', self)
        self.imageGridDock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.imageGridDock.setWidget(self.imageGridViewer)
        self.imageGridDock.setTitleBarWidget(QWidget())
        self.addDockWidget(Qt.RightDockWidgetArea, self.imageGridDock)

        self.trackerAddDock = QDockWidget('Add New Animals', self)
        self.trackerAddDock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.trackerAddDock.setWidget(self.tracker.addAnimalForm)
        self.addDockWidget(Qt.RightDockWidgetArea, self.trackerAddDock)

        self.trackerDock = QDockWidget('Animal Tracker', self)
        self.trackerDock.setAllowedAreas(Qt.RightDockWidgetArea) # Qt.RightDockWidgetArea)
        self.trackerDock.setWidget(self.tracker)
        self.addDockWidget(Qt.RightDockWidgetArea, self.trackerDock)

        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)

        # should be overwritten by the fbs run function
        self._appContext = None
        self._version = None
        
        self.stylesheetPath = 'QMainWindowStyle.qss'
        self.readStyleSheet()

        # self.threadpool = QThreadPool()

        self.createConnections()
        self.createActions()
        self.createMenus()
        self.createToolbars()
        self.populateMenus()
        self.populateToolbars()
        
        self.setWindowTitle('Animal Counter')
        self.setWindowIconFbs()

        self.fileDialogDirectory = Path().home()

        QCoreApplication.setOrganizationName('WAO')
        QCoreApplication.setApplicationName('Game Counter')
        self.readSettings()

    def closeEvent(self, event):
        self.writeSettings()
        event.accept()

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value
        self.aboutAct.setText(f'&About v{self.version}')

    @property
    def appContext(self):
        return self._appContext

    @appContext.setter
    def appContext(self, context):
        self._appContext = context
        self.imageGridViewer.appContext = context
        self.imagePainter.appContext = context
        self.tracker.appContext = context

        self.readStyleSheet()

        self.setWindowIconFbs()
        self.createActions()

        self.clearToolbars()
        self.clearMenus()

        self.populateToolbars()
        self.populateMenus()

    def readStyleSheet(self):
        if self.appContext is not None:
            fp = self.appContext.get_resource(self.stylesheetPath)
            f = QFile(fp)
            f.open(QFile.ReadOnly | QFile.Text)
            stream = QTextStream(f)
            self.setStyleSheet(stream.readAll())
            # f.close()

    def setWindowIconFbs(self):
        if self.appContext is None:
            fp = '../icons/mainWindowIcon.png'
        else:
            fp = self.appContext.get_resource('mainWindowIcon.png')
        self.setWindowIcon(QIcon(fp))

    def writeSettings(self):
        settings = QSettings()

        settings.beginGroup('MainWindow')
        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())
        settings.setValue('isMaximized', self.isMaximized())
        settings.setValue('fileDialogDirectory', self.fileDialogDirectory)
        settings.endGroup()

        settings.beginGroup('Panels')
        settings.setValue('tracker', self.trackerDock.isVisible())
        settings.setValue('imageGrid', self.imageGridDock.isVisible())
        settings.setValue('trackerAdd', self.trackerAddDock.isVisible())
        settings.endGroup()

        settings.beginGroup('ImageGrid')
        settings.setValue('rows', self.imageGridViewer.rows)
        settings.setValue('cols', self.imageGridViewer.cols)
        settings.endGroup()

        settings.beginGroup('ImagePainter')
        settings.setValue('penWidth', self.imagePainter.penWidth)
        settings.setValue('penColor', self.imagePainter.penColor)
        settings.endGroup()

    def readSettings(self):
        settings = QSettings()

        settings.beginGroup('MainWindow')

        if settings.value('isMaximized') == True:
            self.setWindowState(Qt.WindowMaximized)
        else:
            self.resize(settings.value('size', QSize(800, 500)))

            # if there is no position already saved, it will center itself
            if settings.contains('pos'):
                self.move(settings.value('pos'))
            else:
                screenGeometry = QGuiApplication.primaryScreen().geometry()
                screenHeight = screenGeometry.height()
                screenWidth = screenGeometry.width()
                self.move(QPoint(
                    (screenWidth-self.size().width())/2,
                    (screenHeight-self.size().height())/2
                ))

        self.fileDialogDirectory = Path(
            settings.value('fileDialogDirectory', Path().home())
        )

        settings.endGroup()

        settings.beginGroup('Panels')
        self.trackerDock.setVisible(settings.value('tracker', 'true')=='true')
        self.imageGridDock.setVisible(settings.value('imageGrid', 'true')=='true')
        self.trackerAddDock.setVisible(settings.value('trackerAdd', 'true')=='true')
        settings.endGroup()

        settings.beginGroup('ImageGrid')
        self.imageGridViewer.rows = settings.value('rows', 2)
        self.imageGridViewer.cols = settings.value('cols', 2)
        settings.endGroup()

        settings.beginGroup('ImagePainter')
        self.imagePainter.penWidth = settings.value('penWidth', 30)
        if settings.contains('penColor'):
            self.imagePainter.setPenColor(settings.value('penColor'))
        else:
            self.imagePainter.setDefaultPenColor()
        settings.endGroup()

    def resetSettings(self):
        settings = QSettings()
        settings.clear()
        self.readSettings()

    @pyqtSlot(QPixmap)
    def changeMainImage(self, newPixmap):
        self.imagePainter.setMainPixmap(newPixmap)
        self.imagePainter.bestFitImage()

    @pyqtSlot(QPixmap)
    def updateWindowTitle(self):
        fp = Path(self.imageGridViewer.imageGrids.getFocusedGrid().baseImgPath)
        self.setWindowTitle(f'Animal Counter - {fp.name}')
    
    @pyqtSlot(QPixmap)
    def updateTrackerFile(self):
        fp = Path(self.imageGridViewer.imageGrids.getFocusedGrid().baseImgPath)
        self.tracker.currentImageFile = fp.name
        self.tracker.render()

    def updateImageGridVisibility(self):
        if self.imageGridsToggle.isChecked():
            self.imageGridViewer.show()
        else:
            self.imageGridViewer.hide()

    def save(self):
        if self.imageGridViewer.count() != 0:
            self.imagePainter.flattenImage()
            self.tracker.dump()

    def open(self):
        QFileDialog().setDirectory(str(self.fileDialogDirectory))
        options = QFileDialog.Options()
        fileNames, _ = QFileDialog.getOpenFileNames(self, 
            'Open transect files', '',
            'Images/JSON (*.png *.jpeg *.jpg *.bmp *.gif *.json)',
            options=options)

        filePaths: Path = [Path(name) for name in fileNames]
        if not filePaths:
            return

        self.fileDialogDirectory = filePaths[0].parent

        # remove JSON files from the paths
        JSONPaths: Path = []
        imagePaths: Path = []

        for fp in filePaths:
            if fp.suffix == '.json':
                JSONPaths.append(fp)
            else:
                imagePaths.append(fp)

        if imagePaths:

            # worker = Worker(self.imageGridViewer.openFiles, imagePaths)
            # worker.signals.finished.connect(self.imageGridViewer.focusFirstGrid)
            # worker.signals.finished.connect(self.imagePainter.centerImage)
            # worker.signals.progress.connect(self.updateImageGridProgressBar)

            # self.threadpool.start(worker)

            self.imageGridViewer.openFiles(imagePaths)
            self.tracker.JSONDumpFile = imagePaths[0].parent / Path('counts.json')
            self.imageGridViewer.focusFirstGrid()
            self.imagePainter.centerImage()

        if JSONPaths:
            self.tracker.load(JSONPaths[0])

    def openFile(self, fileName):
        self.imageGridViewer.openFile(fileName)

    @pyqtSlot(int)
    def updateImageGridProgressBar(self, value):
        print(f'progress on images is: {value}')

    def about(self):
        QMessageBox.about(self,
            f'About Game Counter v{self.version}',
            '<p>The <b>Game Counter</b> provides convenient tools for '
            'counting game animals in arial photographs.</p>'
            '<p>Ideally, one can open a entire folder of photos '
            'from a single transect, and use the built-in tools to '
            '<b>circle</b> and <b>count</b> the game animals present.<p>'
            '<p>Summarize your counts with <b>tracker | summarize.</b>')

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_Space):
            self.imagePainter.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def createConnections(self):
        self.imageGridViewer.imageGrids.focusChanged.connect(self.changeMainImage)
        self.imageGridViewer.imageGrids.focusChanged.connect(self.imagePainter.clearDrawnItems)
        self.imageGridViewer.imageGrids.focusChanged.connect(self.updateWindowTitle)
        self.imageGridViewer.imageGrids.focusChanged.connect(self.updateTrackerFile)
        self.imagePainter.imageFlattened.connect(self.imageGridViewer.changeFocusedImageData)

    def createActions(self):

        if self.appContext is None:
            addAnimalFp = './resources/addAnimalIcon.png'
            trackerViewIconFp = 'showTrackerIcon.png'
            gridIconFp = 'showGridIcon.png'
            openIconFp = 'openIcon.png'
            saveIconFp = 'saveIcon.png'
        else:
            addAnimalFp = self.appContext.get_resource('showAnimalAdderIcon.png')
            trackerViewIconFp = self.appContext.get_resource('showTrackerIcon.png')
            gridIconFp = self.appContext.get_resource('showGridIcon.png')
            openIconFp = self.appContext.get_resource('openIcon.png')
            saveIconFp = self.appContext.get_resource('saveIcon.png')

        self.saveAct = QAction(QIcon(saveIconFp), 'Save', self, shortcut=QKeySequence.Save, triggered=self.save)
        self.openAct = QAction(QIcon(openIconFp), '&Open...', self, shortcut=QKeySequence.Open, triggered=self.open)
        self.exitAct = QAction('E&xit', self, shortcut='Ctrl+Q', triggered=self.close)
        self.aboutAct = QAction(f'&About', self, triggered=self.about)
        self.aboutQtAct = QAction('About &Qt', self, triggered=qApp.aboutQt)
        self.resetSettingsAct = QAction('Default Settings', self, triggered=self.resetSettings)

        self.imageGridsToggle = self.imageGridDock.toggleViewAction()
        self.imageGridsToggle.setShortcut(Qt.CTRL + Qt.Key_G)
        self.imageGridsToggle.setIcon(QIcon(gridIconFp))

        self.addAnimalToggle = self.trackerAddDock.toggleViewAction()
        self.addAnimalToggle.setIcon(QIcon(addAnimalFp))

        self.trackerViewToggle = self.trackerDock.toggleViewAction()
        self.trackerViewToggle.setIcon(QIcon(trackerViewIconFp))

    def clearMenus(self):
        self.fileMenu.clear()
        self.viewMenu.clear()
        self.helpMenu.clear()

    def clearToolbars(self):
        self.viewToolBar.clear()
        self.fileToolBar.clear()

    def createMenus(self):
        self.fileMenu = QMenu('&File', self)
        self.viewMenu = QMenu('&View', self)
        self.helpMenu = QMenu('&Help', self)

    def populateMenus(self):
        
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.resetSettingsAct)
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.imageGridsToggle)
        self.viewMenu.addAction(self.addAnimalToggle)
        self.viewMenu.addAction(self.trackerViewToggle)

        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.arangeMenus()

    def arangeMenus(self):

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.imageGridViewer.menu)
        self.menuBar().addMenu(self.tracker.menu)
        self.menuBar().addMenu(self.helpMenu)

    def createToolbars(self):
        self.viewToolBar = QToolBar()
        self.fileToolBar = QToolBar()

    def populateToolbars(self):

        self.viewToolBar.addAction(self.imageGridsToggle)
        self.viewToolBar.addAction(self.addAnimalToggle)
        self.viewToolBar.addAction(self.trackerViewToggle)

        self.fileToolBar.addAction(self.saveAct)
        self.fileToolBar.addAction(self.openAct)

        self.arangeToolbars()

    def arangeToolbars(self):

        self.addToolBar(Qt.LeftToolBarArea, self.fileToolBar)
        self.addToolBar(Qt.LeftToolBarArea, self.imagePainter.toolbar)
        self.addToolBar(Qt.LeftToolBarArea, self.imageGridViewer.toolbar)
        self.addToolBar(Qt.LeftToolBarArea, self.tracker.toolbar)
        self.addToolBar(Qt.LeftToolBarArea, self.viewToolBar)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imageViewer = QGameCounter()
    imageViewer.show()
    # imageViewer.openFile(r'.\transect\InkedDSC02010_LI.jpg')
    # imageViewer.openFile(r'.\transect\InkedDSC02012_LI.jpg')
    sys.exit(app.exec_())