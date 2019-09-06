from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QKeySequence, QIcon, QImage, QPixmap, QKeyEvent
from PyQt5.QtWidgets import (
    QMessageBox, QMainWindow, QShortcut,
    QMenu, QAction, qApp,
    QGraphicsScene, QGraphicsView, QGraphicsItem,
    QDockWidget, QWidget
)

from QImageGrid import QImageGridViewer
from QImagePainter import QImagePainter

class QGameCounter(QMainWindow):

    def __init__(self):
        super().__init__()

        self.imageGridViewer = QImageGridViewer()
        self.imagePainter = QImagePainter()

        self.setCentralWidget(self.imagePainter)

        self.imageGridDock = QDockWidget('Grid Viewer', self)
        self.imageGridDock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.imageGridDock.setWidget(self.imageGridViewer)
        self.imageGridDock.setTitleBarWidget(QWidget())
        self.addDockWidget(Qt.RightDockWidgetArea, self.imageGridDock)

        self.createConnections()
        self.createActions()
        self.createMenus()
        self.createToolbars()

        self.setWindowTitle('Animal Counter')
        self.setWindowIcon(QIcon('./icons/mainWindowIcon.png'))
        self.resize(800, 500)

    @pyqtSlot(QPixmap)
    def changeMainImage(self, newPixmap):
        self.imagePainter.setMainPixmap(newPixmap)
        self.imagePainter.bestFitImage()

    @pyqtSlot(QPixmap)
    def updateWindowTitle(self):
        fp = Path(self.imageGridViewer.imageGrids.getFocusedGrid().baseImgPath)
        self.setWindowTitle(f'Animal Counter - {fp.name}')

    def updateImageGridVisibility(self):
        if self.imageGridsToggle.isChecked():
            self.imageGridViewer.show()
        else:
            self.imageGridViewer.hide()

    def open(self):
        self.imageGridViewer.open()
        self.imageGridViewer.focusLastGrid()
        self.imagePainter.centerImage()

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
        self.imagePainter.imageFlattened.connect(self.imageGridViewer.changeFocusedImageData)

    def createActions(self):
        self.openAct = QAction('&Open...', self, shortcut='Ctrl+O', triggered=self.open)
        self.exitAct = QAction('E&xit', self, shortcut='Ctrl+W', triggered=self.close)
        self.aboutAct = QAction('&About', self, triggered=self.about)
        self.aboutQtAct = QAction('About &Qt', self, triggered=qApp.aboutQt)

        self.imageGridsToggle = self.imageGridDock.toggleViewAction()
        self.imageGridsToggle.setShortcut(Qt.CTRL + Qt.Key_G)

    def createMenus(self):
        self.fileMenu = QMenu('&File', self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu('&View', self)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.imageGridsToggle)

        self.helpMenu = QMenu('&Help', self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.imageGridViewer.menu)
        self.menuBar().addMenu(self.helpMenu)

    def createToolbars(self):
        self.addToolBar(Qt.LeftToolBarArea, self.imagePainter.toolbar)
        self.addToolBar(Qt.LeftToolBarArea, self.imageGridViewer.toolbar)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imageViewer = QGameCounter()
    imageViewer.show()
    # imageViewer.openFile(r'.\transect\InkedDSC02010_LI.jpg')
    # imageViewer.openFile(r'.\transect\InkedDSC02012_LI.jpg')
    sys.exit(app.exec_())