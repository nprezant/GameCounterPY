from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QKeySequence, QIcon, QImage, QPixmap, QKeyEvent
from PyQt5.QtWidgets import (
    QMessageBox, QMainWindow, QShortcut,
    QMenu, QAction, qApp,
    QGraphicsScene, QGraphicsView, QGraphicsItem,
    QDockWidget, QWidget, QToolBar, QFileDialog
)

from QImageGrid import QImageGridViewer
from QImagePainter import QImagePainter
from QGameCountTracker import QGameCountTracker

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

        self._appContext = None

        self.createConnections()
        self.createActions()
        self.createMenus()
        self.createToolbars()
        
        self.setWindowTitle('Animal Counter')
        self.setWindowIconFbs()
        self.resize(800, 500)

    @property
    def appContext(self):
        return self._appContext

    @appContext.setter
    def appContext(self, context):
        self._appContext = context
        self.imageGridViewer.appContext = context
        self.imagePainter.appContext = context
        self.tracker.appContext = context

        self.setWindowIconFbs()
        self.createActions()

    def setWindowIconFbs(self):
        if self.appContext is None:
            fp = '../icons/mainWindowIcon.png'
        else:
            fp = self.appContext.get_resource('mainWindowIcon.png')
        self.setWindowIcon(QIcon(fp))

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

    def open(self):
        options = QFileDialog.Options()
        fileNames, _ = QFileDialog.getOpenFileNames(self, 
            'Open image files', '',
            'Images/JSON (*.png *.jpeg *.jpg *.bmp *.gif *.json)',
            options=options)

        filePaths: Path = [Path(name) for name in fileNames]

        # remove JSON files from the paths
        JSONPaths: Path = []
        imagePaths: Path = []

        for fp in filePaths:
            if fp.suffix == '.json':
                JSONPaths.append(fp)
            else:
                imagePaths.append(fp)

        if imagePaths:
            self.imageGridViewer.openFiles(imagePaths)
            self.imageGridViewer.focusFirstGrid()
            self.imagePainter.centerImage()
            if self.tracker.JSONDumpFile is None:
                self.tracker.JSONDumpFile = imagePaths[0].parent / Path('counts.json')

        if JSONPaths:
            self.tracker.load(JSONPaths[0])

    def openFile(self, fileName):
        self.imageGridViewer.openFile(fileName)

    def about(self):
        QMessageBox.about(self,
            'About Image Grid Viewer',
            '<p>The <b>Image Grid Viewer</b> displays images in a nice '
            'scrolling grid.</p>')

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
        self.imagePainter.imageFlattened.connect(self.tracker.dump)

    def createActions(self):

        if self.appContext is None:
            addAnimalFp = './resources/addAnimalIcon.png'
            trackerViewIconFp = 'showTrackerIcon.png'
            gridIconFp = 'showGridIcon.png'
        else:
            addAnimalFp = self.appContext.get_resource('showAnimalAdderIcon.png')
            trackerViewIconFp = self.appContext.get_resource('showTrackerIcon.png')
            gridIconFp = self.appContext.get_resource('showGridIcon.png')

        self.openAct = QAction('&Open...', self, shortcut='Ctrl+O', triggered=self.open)
        self.exitAct = QAction('E&xit', self, shortcut='Ctrl+Q', triggered=self.close)
        self.aboutAct = QAction('&About', self, triggered=self.about)
        self.aboutQtAct = QAction('About &Qt', self, triggered=qApp.aboutQt)

        self.imageGridsToggle = self.imageGridDock.toggleViewAction()
        self.imageGridsToggle.setShortcut(Qt.CTRL + Qt.Key_G)
        self.imageGridsToggle.setIcon(QIcon(gridIconFp))

        self.addAnimalToggle = self.trackerAddDock.toggleViewAction()
        self.addAnimalToggle.setIcon(QIcon(addAnimalFp))

        self.trackerViewToggle = self.trackerDock.toggleViewAction()
        self.trackerViewToggle.setIcon(QIcon(trackerViewIconFp))

    def createMenus(self):
        self.fileMenu = QMenu('&File', self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu('&View', self)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.imageGridsToggle)
        self.viewMenu.addAction(self.addAnimalToggle)
        self.viewMenu.addAction(self.trackerViewToggle)

        self.helpMenu = QMenu('&Help', self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.imageGridViewer.menu)
        self.menuBar().addMenu(self.tracker.menu)
        self.menuBar().addMenu(self.helpMenu)

    def createToolbars(self):
        self.viewToolBar = QToolBar()
        self.viewToolBar.addAction(self.addAnimalToggle)
        self.viewToolBar.addAction(self.trackerViewToggle)

        self.addToolBar(Qt.LeftToolBarArea, self.imagePainter.toolbar)
        self.addToolBar(Qt.LeftToolBarArea, self.imageGridViewer.toolbar)
        # self.addToolBar(Qt.LeftToolBarArea, self.tracker.toolbar)
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