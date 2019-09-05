from pathlib import Path

from PyQt5.QtCore import Qt, QSize, QFile, QTextStream, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QKeyEvent
from PyQt5.QtWidgets import (
    QLabel, QSizePolicy, QScrollArea, QMainWindow,
    QFileDialog, QWidget, QGridLayout, QVBoxLayout, QMessageBox
)

from QImageGridErrors import MoveGridItemFocusError, MoveGridFocusError

from splitter import split_image

class QImageLabel(QLabel):

    # signals
    clicked = pyqtSignal()

    def __init__(self, imgPath=None):
        super().__init__()

        self.imgPath = imgPath

        self.setBackgroundRole(QPalette.Base)
        self.setScaledContents(True)

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)

        if imgPath is not None:
            self.readImage()

    def readImage(self):
        # read in the image
        image = QImage(str(self.imgPath))
        if image.isNull():
            QMessageBox.information(self,
                'Image Viewer',
                f'Cannot load {self.imgPath}')
            return
        self.setImage(image)

    def setImage(self, image: QImage):
        # save the image
        self.image = image

        # get the original image size & AR
        self.originalSize = image.size()
        self.originalAR = self.originalSize.height() / self.originalSize.width()

        # set the image into the label
        self.setPixmap(QPixmap.fromImage(image))

    def heightForWidth(self, w):
        return w * self.originalAR

    def highlight(self):
        self.setProperty('highlighted', True)

    def clearHighlight(self):
        self.setProperty('highlighted', False)

    def mouseReleaseEvent(self, event):
        self.clicked.emit()

class QImageGrid(QWidget):

    def __init__(self, baseImgPath):

        super().__init__()
        self.baseImgPath = baseImgPath

        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(0)
        self.setLayout(self.gridLayout)

        self.setBackgroundRole(QPalette.Dark)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored))

        # options
        self.splitDir = self.baseImgPath.parent / Path('split')
        self.rows = 1
        self.cols = 1

        # defaults
        self._focusItemRow = 0
        self._focusItemColumn = 0

        # read in the image as a grid
        self.readImage()

    def readImage(self):

        if self.rows > 1 and self.cols > 1:
            # split image
            imgPaths = split_image(self.baseImgPath, self.splitDir, self.rows, self.cols)

            # read in pieces
            for row, imgRow in enumerate(imgPaths):
                for col, imgPath in enumerate(imgRow):
                    imageLabel = QImageLabel(imgPath)
                    self.gridLayout.addWidget(imageLabel, row, col)
        
        else:
            self.gridLayout.addWidget(QImageLabel(self.baseImgPath), 0, 0)

    def writeImage(self):

        if self.rows > 1 and self.cols > 1:
            # assumes all images are the same size within a grid
            width = self.getItemAtPosition(0,0).widget().image.width()
            height = self.getItemAtPosition(0,0).widget().image.height()

            mergedImage = QImage(width*self.cols, height*self.rows, QImage.Format_RGB32)
            painter = QPainter(mergedImage)

            for row in range(self.rows):
                for col in range(self.cols):
                    widget = self.getItemAtPosition(row, col).widget()
                    image = widget.image
                    painter.drawImage(col * width, row * height, image)
            
            painter.end()

        else:
            mergedImage = self.getItemAtPosition(0, 0).widget().image

        # save the merged file
        savePath = self.baseImgPath.parent / Path(f'{self.baseImgPath.stem}_Inked{self.baseImgPath.suffix}')
        mergedImage.save(str(savePath))

    def clearFocusItem(self):
        widget = self.getFocusWidget()
        widget.clearHighlight()

    def getFocusItem(self):
        return self.getItemAtPosition(self._focusItemRow, self._focusItemColumn)

    def getItemAtPosition(self, row, col):
        item = self.gridLayout.itemAtPosition(row, col)

        if item is None:
            raise ValueError(f'No item at ({self._focusItemRow}, {self._focusItemColumn}')

        return item

    def getFocusWidget(self):
        return self.getFocusItem().widget()

    def setFocusWidget(self, widget):
        index = self.gridLayout.indexOf(widget)
        row, col, _, _ = self.gridLayout.getItemPosition(index)
        self.setFocusItem(row, col)

    def setFocusItem(self, row, col):
        item = self.gridLayout.itemAtPosition(row, col)
        
        if item is None:
            raise MoveGridItemFocusError(
                self._focusItemRow, self._focusItemColumn,row, col,
                f'No item at ({row}, {col}'
            )
        
        # only set the new focus row and column if there is an item there
        self.clearFocusItem()

        widget = item.widget()
        widget.highlight()

        self._focusItemRow = row
        self._focusItemColumn = col
        
        return widget

    def reFocus(self):
        self.setFocusItem(self._focusItemRow, self._focusItemColumn)

    def moveFocusDown(self):
        row = self._focusItemRow + 1
        col = self._focusItemColumn
        return self.setFocusItem(row, col)

    def moveFocusUp(self):
        row = self._focusItemRow - 1
        col = self._focusItemColumn
        return self.setFocusItem(row, col)

    def moveFocusLeft(self):
        row = self._focusItemRow
        col = self._focusItemColumn - 1
        return self.setFocusItem(row, col)

    def moveFocusRight(self):
        row = self._focusItemRow
        col = self._focusItemColumn + 1
        return self.setFocusItem(row, col)


class QImageGrids(QWidget):

    # signals
    focusChanged = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()

        self.VBoxLayout = QVBoxLayout()
        self.setLayout(self.VBoxLayout)
        self.VBoxLayout.addStretch()
        
        self.setBackgroundRole(QPalette.Light)

        self._focusItemIndex = 0
        
    def add(self, imgPath):
        imgGrid = QImageGrid(imgPath)
        # imgGrid.setMinimumHeight(100)
        self.VBoxLayout.insertWidget(self.VBoxLayout.count()-1, imgGrid)

        for img in imgGrid.children():
            if isinstance(img, QImageLabel):
                img.clicked.connect(self.imageClicked)

    def getFocusedGrid(self) -> QImageGrid:
        imgGridItem = self.VBoxLayout.itemAt(self._focusItemIndex)
        if imgGridItem is None:
            return None
        else:
            return imgGridItem.widget()

    @pyqtSlot()
    def imageClicked(self):

        # clear the currently selected image
        self.getFocusedGrid().clearFocusItem()

        # focus on the new image
        imgLabel = self.sender()
        self._focusItemIndex = self.VBoxLayout.indexOf(imgLabel.parent())
        self.getFocusedGrid().setFocusWidget(imgLabel)
        imgLabel.clicked.connect(self.emitFocusChanged)

    def emitFocusChanged(self):
        pixmap = self.getFocusedGrid().getFocusWidget().pixmap()
        self.focusChanged.emit(pixmap)

    def moveGridFocusDown(self):
        # only shift if we're not already at the bottom
        if not self._focusItemIndex == self.VBoxLayout.count() - 2:
            self._focusItemIndex += 1
        else:
            raise MoveGridFocusError(
                self._focusItemIndex, self._focusItemIndex + 1,
                f'Grid {self._focusItemIndex + 1} does not exist'
            )

    def moveGridFocusUp(self):
        # only shift if we're not already at the top
        if not self._focusItemIndex == 0:
            self._focusItemIndex -= 1
        else:
            raise MoveGridFocusError(
                self._focusItemIndex, self._focusItemIndex - 1,
                'Grid -1 does not exist'
            )

    def moveItemFocusDown(self):
        grid = self.getFocusedGrid()
        try:
            grid.moveFocusDown()
        except MoveGridItemFocusError as e:

            try:
                self.moveGridFocusDown()
            except MoveGridFocusError:
                pass
            else:
                newGrid = self.getFocusedGrid()
                newGrid.setFocusItem(0, e.column)
                grid.clearFocusItem()
                self.emitFocusChanged()

        else:
            self.emitFocusChanged()

    def moveItemFocusUp(self):
        grid = self.getFocusedGrid()
        try:
            grid.moveFocusUp()
        except MoveGridItemFocusError as e:

            try:
                self.moveGridFocusUp()
            except MoveGridFocusError:
                pass
            else:
                newGrid = self.getFocusedGrid()
                newGrid.setFocusItem(newGrid.rows-1, e.column)
                grid.clearFocusItem()
                self.emitFocusChanged()

        else:
            self.emitFocusChanged()

    def moveItemFocusLeft(self):
        grid = self.getFocusedGrid()
        try:
            grid.moveFocusLeft()
        except MoveGridItemFocusError:
            pass
        else:
            self.emitFocusChanged()
        
    def moveItemFocusRight(self):
        grid = self.getFocusedGrid()
        try:
            grid.moveFocusRight()
        except MoveGridItemFocusError:
            pass
        else:
            self.emitFocusChanged()


class QImageGridViewer(QScrollArea):

    def __init__(self):

        super().__init__()

        self.imageGrids = QImageGrids()
        self.imageGrids.focusChanged.connect(self.focusChangedSlot)

        self.setBackgroundRole(QPalette.Dark)
        self.setWidget(self.imageGrids)
        self.setWidgetResizable(True)

        self.stylesheetPath = './QImageGridStyle.qss'
        self.readStyleSheet()

    def readStyleSheet(self):
        f = QFile(self.stylesheetPath)
        f.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(f)
        self.setStyleSheet(stream.readAll())

    def open(self):
        options = QFileDialog.Options()
        fileNames, _ = QFileDialog.getOpenFileNames(self, 
            'QFileDialog.getOpenFileNames()', '',
            'Images (*.png *.jpeg *.jpg *.bmp *.gif)',
            options=options)

        if fileNames:
            for fileName in fileNames:
                self.openFile(fileName)

    def openFile(self, fileName):
        self.imageGrids.add(Path(fileName))

    def focusLastGrid(self):
        oldGrid = self.imageGrids.getFocusedGrid()

        if oldGrid is None:
            return

        oldGrid.clearFocusItem()

        self.imageGrids._focusItemIndex = self.imageGrids.VBoxLayout.count() - 2
        newGrid = self.imageGrids.getFocusedGrid()
        newGrid.setFocusItem(0, 0)
        self.imageGrids.emitFocusChanged()

    def keyPressEvent(self, event: QKeyEvent):
        QMainWindow().keyPressEvent(event)

    def ensureFocusedItemVisible(self):
        self.ensureWidgetVisible(self.imageGrids.getFocusedGrid().getFocusWidget())

    @pyqtSlot()
    def focusChangedSlot(self):
        self.readStyleSheet()
        self.ensureFocusedItemVisible()

    @pyqtSlot(QImage)
    def changeFocusedImageData(self, newImage):
        widget = self.imageGrids.getFocusedGrid().getFocusWidget()
        widget.setImage(newImage)
        self.imageGrids.getFocusedGrid().writeImage()

    def moveFocusDown(self):
        self.imageGrids.moveItemFocusDown()

    def moveFocusUp(self):
        self.imageGrids.moveItemFocusUp()

    def moveFocusLeft(self):
        self.imageGrids.moveItemFocusLeft()

    def moveFocusRight(self):
        self.imageGrids.moveItemFocusRight()

    def sizeHint(self):
        return QSize(150,400)