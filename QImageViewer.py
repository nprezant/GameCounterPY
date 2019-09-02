from PyQt5.QtCore import Qt, QFile, QTextStream
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
from PyQt5.QtWidgets import (
    QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu,
    QAction, qApp, QFileDialog, QWidget
)

from QImageGrid import QImageLabel


class QImageViewer(QScrollArea):
    def __init__(self):
        super().__init__()

        self.scaleFactor = 0.0

        self.imageLabel = QImageLabel()
        self.setWidget(self.imageLabel)

        self.setBackgroundRole(QPalette.Dark)
        self.setWidgetResizable(False)

        self.createActions()
        
        self.stylesheetPath = './QImageGridStyle.qss'
        self.readStyleSheet()

    def readStyleSheet(self):
        f = QFile(self.stylesheetPath)
        f.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(f)
        self.setStyleSheet(stream.readAll())

    def open(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                  'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        if fileName:
            self.openFile(fileName)

    def openFile(self, fileName):
        self.imageLabel.imgPath = fileName
        self.imageLabel.readImage()
        self.fitSize()

    def fitSize(self):
        try:
            self.imageLabel.resize(self.width() - 5, self.width() * self.imageLabel.originalAR - 5)
            self.scaleFactor = self.imageLabel.width() / self.imageLabel.originalSize.width()
        except:
            pass
        finally:
            self.centerImage()

    def centerImage(self):
        self.setAlignment(Qt.AlignCenter)

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def createActions(self):
        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut=Qt.Key_I, triggered=self.zoomIn)
        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut=Qt.Key_O, triggered=self.zoomOut)
        self.fitSizeAct = QAction("Fit Size", self, shortcut=Qt.Key_Space, triggered=self.fitSize)

    def scaleImage(self, factor):
        oldFactor = self.scaleFactor
        self.scaleFactor *= factor

        try:
            self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())
        except AttributeError:
            self.scaleFactor = oldFactor
        else:
            self.adjustScrollBar(self.horizontalScrollBar(), factor)
            self.adjustScrollBar(self.verticalScrollBar(), factor)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imageViewer = QImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())
