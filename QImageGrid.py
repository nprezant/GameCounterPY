from pathlib import Path

from PyQt5.QtCore import Qt, QSize, QFile, QTextStream, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QKeyEvent, QIcon
from PyQt5.QtWidgets import (
    QLabel, QSizePolicy, QScrollArea, QMainWindow,
    QFileDialog, QWidget, QGridLayout, QVBoxLayout, QMessageBox,
    QToolBar, QAction, QMenu, QInputDialog
)

from QImageGridErrors import MoveGridItemFocusError, MoveGridFocusError

class QImageLabel(QLabel):

    # signals
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.imgPath = None

        self.setBackgroundRole(QPalette.Base)
        self.setScaledContents(True)

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)

    def readImage(self):
        # read in the image
        image = QImage(str(self.imgPath))
        if image.isNull():
            QMessageBox.information(self,
                'Image Viewer',
                f'Cannot load {self.imgPath}')
            return
        self.setImage(image)

    def setImagePath(self, imgPath):
        self.imgPath = imgPath
        self.readImage()

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

    clsRows = 2
    clsCols = 2

    def __init__(self, baseImgPath):

        super().__init__()
        self.baseImgPath = baseImgPath

        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(0)
        self.setLayout(self.gridLayout)

        self.setBackgroundRole(QPalette.Dark)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored))

        # options
        # self.splitDir = self.baseImgPath.parent / Path('split')
        self.rows = self.clsRows
        self.cols = self.clsCols

        # defaults
        self._focusItemRow = 0
        self._focusItemColumn = 0

        # read in the image as a grid
        self.splitImages = None
        self.readImage()

    def readImage(self):

        if self.rows > 1 and self.cols > 1:
            # split image
            self.splitImages = self._splitImage() # split_image(self.baseImgPath, self.splitDir, self.rows, self.cols)

            # read in pieces
            for row, imgRow in enumerate(self.splitImages):
                for col, image in enumerate(imgRow):
                    imageLabel  = QImageLabel()
                    imageLabel.setImage(image)
                    self.gridLayout.addWidget(imageLabel, row, col)
        
        else:
            imageLabel = QImageLabel()
            imageLabel.setImagePath(self.baseImgPath)
            self.gridLayout.addWidget(imageLabel, 0, 0)

    def _splitImage(self):

        # open image
        img = QImage(str(self.baseImgPath))

        width = img.width()
        height = img.height()

        segmentWidth = width / self.cols
        segmentHeight = height / self.rows

        # hold list of image labels
        splitImageList = []
        imageRow = []

        # crop image into AxB
        for row in range(self.rows):
            for col in range(self.cols):

                x = width - (self.cols - col) * segmentWidth
                y = height - (self.rows - row) * segmentHeight

                cropped = img.copy(x, y, segmentWidth, segmentHeight)
                imageRow.append(cropped)

            splitImageList.append(imageRow.copy())
            imageRow.clear()

        return splitImageList

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

    def reloadImage(self):
        for widget in self.findChildren(QImageLabel, options=Qt.FindDirectChildrenOnly):
            widget.deleteLater()
        self.readImage()

    def clearFocusItem(self):
        widget = self.getFocusWidget()
        try:
            widget.clearHighlight()
        except AttributeError:
            pass

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
        self.VBoxLayout.insertWidget(self.VBoxLayout.count()-1, imgGrid)

        self.connectGridSignals(imgGrid)

    def connectGridSignals(self, grid):
        for img in grid.children():
            if isinstance(img, QImageLabel):
                img.clicked.connect(self.imageClicked)

    def removeFocusedGrid(self):
        # TODO
        grid = self.getFocusedGrid() # .VBoxLayout.itemAt(self._focusItemIndex)
        if isinstance(grid, QImageGrid):
            self.VBoxLayout.removeWidget(grid)
            grid.deleteLater()
            try:
                self.moveGridFocusUp()
            except MoveGridFocusError:
                pass
            finally:
                newGrid = self.getFocusedGrid()
                if newGrid is not None:
                    newGrid.reFocus()
                    self.emitFocusChanged()

    def reloadFocusedGrid(self):
        grid = self.getFocusedGrid()
        grid.reloadImage()
        self.connectGridSignals(grid)
        # self.getFocusedGrid().reFocus()
        # self.emitFocusChanged() # TODO this causes AttributeError: 'QWidgte' object has no attribute 'pixmap'

    def getFocusedGrid(self) -> QImageGrid:
        imgGridItem = self.VBoxLayout.itemAt(self._focusItemIndex)
        if imgGridItem is None:
            return None
        else:
            return imgGridItem.widget()

    @pyqtSlot()
    def imageClicked(self):

        # clear the currently selected image
        oldGrid = self.getFocusedGrid()
        if oldGrid is not None:
            oldGrid.clearFocusItem()

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
                'Grid "-1" does not exist'
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

        self.toolbar = QToolBar()
        self.initToolbar()

        self.initMenu() # makes self.menu

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

    def removeFocusedGrid(self):
        self.imageGrids.removeFocusedGrid()

    def reloadFocusedImage(self):
        self.imageGrids.reloadFocusedGrid()

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

    def createActions(self):
        self.itemFocusDownAct = QAction('Down Item', self, shortcut=Qt.CTRL + Qt.Key_Down, triggered=self.moveFocusDown)
        self.itemFocusUpAct = QAction('Up Item', self, shortcut=Qt.CTRL + Qt.Key_Up, triggered=self.moveFocusUp)
        self.itemFocusLeftAct = QAction('Left Item', self, shortcut=Qt.CTRL + Qt.Key_Left, triggered=self.moveFocusLeft)
        self.itemFocusRightAct = QAction('Right Item', self, shortcut=Qt.CTRL + Qt.Key_Right, triggered=self.moveFocusRight)

        self.resetImageAct = QAction(QIcon('./icons/refreshIcon.png'), 'Reset Image', self, shortcut=Qt.CTRL + Qt.Key_R, triggered=self.reloadFocusedImage)

        self.promptGridRowsAct = QAction('Set grid rows', self, triggered=self.promptForGridRows)
        self.promptGridColumnsAct = QAction('Set grid columns', self, triggered=self.promptForGridColumns)

        self.removeFocusedGridAct = QAction('Remove current image', self, shortcut=Qt.CTRL + Qt.Key_W, triggered=self.removeFocusedGrid)

    def initMenu(self):
        self.menu = QMenu('&Grids', self)
        self.menu.addAction(self.itemFocusDownAct)
        self.menu.addAction(self.itemFocusUpAct)
        self.menu.addAction(self.itemFocusLeftAct)
        self.menu.addAction(self.itemFocusRightAct)
        self.menu.addSeparator()
        self.menu.addAction(self.promptGridRowsAct)
        self.menu.addAction(self.promptGridColumnsAct)
        self.menu.addSeparator()
        self.menu.addAction(self.removeFocusedGridAct)

    def initToolbar(self):
        self.createActions()
        self.toolbar.addAction(self.resetImageAct)

    def promptForGridRows(self):
        rows, okPressed = QInputDialog.getInt(self, 'Grid Rows','Number of grid rows:', QImageGrid.clsRows, 1, 20, 1)
        if okPressed:
            QImageGrid.clsRows = rows

    def promptForGridColumns(self):
        cols, okPressed = QInputDialog.getInt(self, 'Grid Columns','Number of grid columns:', QImageGrid.clsCols, 1, 20, 1)
        if okPressed:
            QImageGrid.clsCols = cols