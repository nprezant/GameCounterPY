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

        self.setWindowTitle('Image Grid Viewer and Painter')
        self.setWindowIcon(QIcon('./icons/mainWindowIcon.png'))
        self.resize(800, 500)

    @pyqtSlot(QPixmap)
    def changeMainImage(self, newPixmap):
        # print(f'Hi. {newPath}')
        # self.imagePainter.setMainPixmapFromPath(newPath)
        self.imagePainter.setMainPixmap(newPixmap)

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

    def createActions(self):
        self.openAct = QAction('&Open...', self, shortcut='Ctrl+O', triggered=self.open)
        self.exitAct = QAction('E&xit', self, shortcut='Ctrl+W', triggered=self.close)
        self.aboutAct = QAction('&About', self, triggered=self.about)
        self.aboutQtAct = QAction('About &Qt', self, triggered=qApp.aboutQt)

        self.itemFocusDownAct = QAction('Down Item', self, shortcut=Qt.CTRL + Qt.Key_Down, triggered=self.imageGridViewer.moveFocusDown)
        self.itemFocusUpAct = QAction('Up Item', self, shortcut=Qt.CTRL + Qt.Key_Up, triggered=self.imageGridViewer.moveFocusUp)
        self.itemFocusLeftAct = QAction('Left Item', self, shortcut=Qt.CTRL + Qt.Key_Left, triggered=self.imageGridViewer.moveFocusLeft)
        self.itemFocusRightAct = QAction('Right Item', self, shortcut=Qt.CTRL + Qt.Key_Right, triggered=self.imageGridViewer.moveFocusRight)

        self.imageGridsToggle = self.imageGridDock.toggleViewAction()
        self.imageGridsToggle.setShortcut(Qt.CTRL + Qt.Key_G)

    def createMenus(self):
        self.fileMenu = QMenu('&File', self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu('&View', self)
        self.viewMenu.addAction(self.itemFocusDownAct)
        self.viewMenu.addAction(self.itemFocusUpAct)
        self.viewMenu.addAction(self.itemFocusLeftAct)
        self.viewMenu.addAction(self.itemFocusRightAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.imageGridsToggle)

        self.helpMenu = QMenu('&Help', self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def createToolbars(self):
        self.addToolBar(Qt.LeftToolBarArea, self.imagePainter.toolbar)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imageViewer = QGameCounter()
    imageViewer.show()
    imageViewer.openFile(r'.\transect\InkedDSC02010_LI.jpg')
    # imageViewer.openFile(r'.\transect\fine.jpeg')
    # imageViewer.openFile(r'.\transect\bikes.jpg')
    # imageViewer.openFile(r'.\transect\fine.jpeg')
    sys.exit(app.exec_())