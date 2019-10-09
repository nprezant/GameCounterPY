from PyQt5.QtCore import Qt, QRectF, QMarginsF, QTimeLine, pyqtSignal, QSize
from PyQt5.QtGui import QKeySequence, QImage, QPixmap, QPalette, QPainter, QWheelEvent, QKeyEvent, QIcon, QPen, QColor
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QToolBar, QAction,
    QApplication, QInputDialog, QMenu, QToolButton, QPushButton
)

COLORS = {
    'Teleric Blue': '#3296e6',
    'Blue': 'Blue',
    'Green': 'DarkGreen',
    'Teal': 'Teal',
    'Red': 'Red',
    'Orange': 'Orange',
    'Magenta': 'Magenta',
    'Black': 'Black',
    'White': 'White',
}

class QPaletteIcon(QIcon):

    def __init__(self, color):
        super().__init__()

        self.color = color

        pixmap = QPixmap(100, 100)
        pixmap.fill(QColor(color))
        self.addPixmap(pixmap)

class QSmoothGraphicsView(QGraphicsView):
    '''Implements smooth mouse/keyboard navigation'''

    def __init__(self):
        super().__init__()
        
        self._numScheduledScalings = 0
        self._numScheduledHTranslations = 0
        self._numScheduledVTranslations = 0

        self.animatingH = False
        self.animatingV = False

        self.controlDown = False

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Up:
            self.translateVerticalEvent(-100)
        elif key == Qt.Key_Down:
            self.translateVerticalEvent(100)
        elif key == Qt.Key_Left:
            self.translateHorizontalEvent(-100)
        elif key == Qt.Key_Right:
            self.translateHorizontalEvent(100)
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.zoom(75)

    def wheelEvent(self, event: QWheelEvent):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            super().wheelEvent(event)
        else:
            self.zoom(event.angleDelta().y() / 8)

    def zoom(self, numDegrees):
        numSteps = numDegrees / 15
        self._numScheduledScalings += numSteps

        if (self._numScheduledScalings * numSteps < 0): # if user moved the wheel in another direction, we reset previously scheduled scalings
            self._numScheduledScalings = numSteps

        anim = QTimeLine(350, self)
        anim.setUpdateInterval(20)

        anim.valueChanged.connect(self.scalingTime)
        anim.finished.connect(self.scaleAnimFinished)
        anim.start()

    def scalingTime(self, x):
        factor = 1 + self._numScheduledScalings / 300.0
        self.scaleView(factor)

    def scaleAnimFinished(self):
        if (self._numScheduledScalings > 0):
            self._numScheduledScalings -= 1
        else:
            self._numScheduledScalings += 1
        self.sender().deleteLater()

    def translateVertical(self, dy):
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() + dy)

    def translateHorizontal(self, dx):
        bar = self.horizontalScrollBar()
        bar.setValue(bar.value() + dx)

    def translateHorizontalEvent(self, dx):
        numSteps = dx * 20
        self._numScheduledHTranslations += numSteps

        if (self._numScheduledHTranslations * numSteps < 0): # if user moved the wheel in another direction, we reset previously scheduled scalings
            self._numScheduledHTranslations = numSteps

        if not self.animatingH:
            anim = QTimeLine(350, self)
            anim.setUpdateInterval(10)

            anim.valueChanged.connect(self.translateHTime)
            anim.finished.connect(self.translateHAnimFinished)
            anim.start()

    def translateHTime(self, x):
        if self._numScheduledHTranslations > 0:
            dx = 10
        else:
            dx = -10
        self.translateHorizontal(dx)

    def translateHAnimFinished(self):
        if (self._numScheduledHTranslations > 0):
            self._numScheduledHTranslations -= 1
        else:
            self._numScheduledHTranslations += 1
        self.sender().deleteLater()
        self.animatingH = False

    def translateVerticalEvent(self, dy):
        numSteps = dy * 20
        self._numScheduledVTranslations += numSteps

        if (self._numScheduledVTranslations * numSteps < 0): # if user moved the wheel in another direction, we reset previously scheduled scalings
            self._numScheduledVTranslations = numSteps

        if not self.animatingV:
            anim = QTimeLine(350, self)
            anim.setUpdateInterval(10)

            anim.valueChanged.connect(self.translateVTime)
            anim.finished.connect(self.translateVAnimFinished)
            anim.start()

    def translateVTime(self, y):
        if self._numScheduledVTranslations > 0:
            dy = 10
        else:
            dy = -10

        # dy = self._numScheduledVTranslations / 500
        self.translateVertical(dy)

    def translateVAnimFinished(self):
        if (self._numScheduledVTranslations > 0):
            self._numScheduledVTranslations -= 1
        else:
            self._numScheduledVTranslations += 1
        self.sender().deleteLater()
        self.animatingV = False

    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        if (factor < 0.02 or factor > 100):
            return

        self.scale(scaleFactor, scaleFactor)
    

class QImagePainter(QSmoothGraphicsView):

    # signals
    imageFlattened = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)

        self.mainPixmapItem = self.scene.addPixmap(QPixmap())

        self._appContext = None

        # policies
        # self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        # self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.toolbar = QToolBar()
        self.initToolbar()

        self._pen = QPen()
        self._pen.setWidth(50)
        self.setDefaultPenColor()

        self._drawStartPos = None
        self._dynamicOval = None
        self._drawnItems = []

        self.updateDragMode()

    @property
    def appContext(self):
        return self._appContext

    @appContext.setter
    def appContext(self, context):
        self._appContext = context
        self.toolbar.clear()
        self.initToolbar()

    def setMainPixmapFromPath(self, imgPath):

        # set image
        image = QImage(str(imgPath))
        pixmap = self.mainPixmapItem.pixmap()
        pixmap.convertFromImage(image)
        self.setMainPixmap(pixmap)

    def setMainPixmap(self, pixmap):
        self.mainPixmapItem.setPixmap(pixmap)

        # set scene rect
        boundingRect = self.mainPixmapItem.boundingRect()
        margin = 0
        boundingRect += QMarginsF(margin,margin,margin,margin)
        self.scene.setSceneRect(boundingRect)

    def saveImage(self, fileName):
        image = self.flattenImage()
        image.save(fileName)

    def flattenImageIfDrawnOn(self):
        if not len(self._drawnItems) == 0:
            self.flattenImage()

    def flattenImage(self):

        # get region of scene
        area = self.mainPixmapItem.boundingRect()

        # create a QImage to render to and fix up a QPainter for it
        image = QImage(area.width(), area.height(), QImage.Format_ARGB32_Premultiplied)
        painter = QPainter(image)

        # render the region of interest to the QImage
        self.scene.render(painter, QRectF(image.rect()), area)
        painter.end()

        # set this flattened image to this view
        pixmap = self.mainPixmapItem.pixmap()
        pixmap.convertFromImage(image)
        self.setMainPixmap(pixmap)

        # clear the drawings from the view
        self.clearDrawnItems()

        # emit flattened image signal
        self.imageFlattened.emit(image)

        # return the flattened image
        return image

    def clearDrawnItems(self):
        for item in self._drawnItems:
            self.scene.removeItem(item)

        self._drawnItems.clear()

    def removeLastDrawnItem(self):
        try:
            item = self._drawnItems.pop()
        except IndexError:
            pass
        else:
            self.scene.removeItem(item)

    def scaleView(self, scaleFactor):
        # print(f'self.width: {self.width()}')
        # print(f'pixmap.width(): {self.scene.map.mainPixmapItem.boundingRect().width()}')
        self.scale(scaleFactor, scaleFactor)

    def centerImage(self):
        self.centerOn(self.mainPixmapItem)

    def bestFitImage(self):
        self.fitInView(self.mainPixmapItem, Qt.KeepAspectRatio)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Space:
            self.bestFitImage()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self._drawStartPos = None
        if self.ovalModeAct.isChecked():
            if self.mainPixmapItem.isUnderMouse():
                self._drawStartPos = self.mapToScene(event.pos())
                self._dynamicOval = self.scene.addEllipse(
                    QRectF(self._drawStartPos.x(), self._drawStartPos.y(), 1, 1),
                    self._pen
                )
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dynamicOval:
            pos = self.mapToScene(event.pos())
            self._dynamicOval.setRect(
                QRectF(self._drawStartPos.x(), self._drawStartPos.y(),
                pos.x() - self._drawStartPos.x(), pos.y() - self._drawStartPos.y())
            )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dynamicOval:
            self._drawnItems.append(self._dynamicOval)
            self._dynamicOval = None
        else:
            super().mouseReleaseEvent(event)

    def toggleSelectionMode(self):
        if self.selectionModeAct.isChecked():
            self.ovalModeAct.setChecked(False)
        else:
            self.selectionModeAct.setChecked(True)
        self.updateDragMode()

    def toggleOvalMode(self):
        if self.ovalModeAct.isChecked():
            self.selectionModeAct.setChecked(False)
        else:
            self.ovalModeAct.setChecked(True)
        self.updateDragMode()

    def updateDragMode(self):
        if self.selectionModeAct.isChecked():
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.NoDrag)

    @property
    def penWidth(self):
        return self._pen.width()

    @penWidth.setter
    def penWidth(self, value):
        self._pen.setWidth(value)

    @property
    def penColor(self):
        return self._pen.color()

    @penColor.setter
    def penColor(self, value):
        self._pen.setColor(QColor(value))

    def setDefaultPenColor(self):
        self.setPenColor(COLORS['Teleric Blue']) 

    def promptForPenWidth(self):
        width, okPressed = QInputDialog.getInt(self, 'Pen Width','Pen width (px):', self.penWidth, 1, 100, 1)
        if okPressed:
            self.penWidth = width

    def setResourcePaths(self):
        if self.appContext is None:
            self.selectionModeFp = './icons/selectIcon.png'
            self.ovalModeFp = './icons/ovalIcon.png'
            self.flattenFp = './icons/saveIcon.png'
            self.undoFp = './icons/undoIcon.png'
            self.penFp = './icons/pen.png'
            self.penWidthFp = './icons/penWidth.png'
        else:
            self.selectionModeFp = self.appContext.get_resource('selectIcon.png')
            self.ovalModeFp = self.appContext.get_resource('ovalIcon.png')
            self.flattenFp = self.appContext.get_resource('saveIcon.png')
            self.undoFp = self.appContext.get_resource('undoIcon.png')
            self.penFp = self.appContext.get_resource('pen.png')
            self.penWidthFp = self.appContext.get_resource('penWidth.png')

    def createActions(self):
        self.setResourcePaths()
        
        self.selectionModeAct = QAction(QIcon(self.selectionModeFp), 'Select (v)', self, checkable=True, checked=True, shortcut=Qt.Key_V, triggered=self.toggleSelectionMode)
        self.ovalModeAct = QAction(QIcon(self.ovalModeFp), 'Draw &Oval (o)', self, checkable=True, checked=False, shortcut=Qt.Key_O, triggered=self.toggleOvalMode)
        self.flattenAct = QAction(QIcon(self.flattenFp), 'Save', self, shortcut=QKeySequence.Save, triggered=self.flattenImage)
        self.undoAct = QAction(QIcon(self.undoFp), 'Undo', self, shortcut=QKeySequence.Undo, triggered=self.removeLastDrawnItem)

        self.setPenWidthAct = QAction(QIcon(self.penWidthFp), 'Set Pen Width', self, triggered=self.promptForPenWidth)

    def addPenToolMenu(self):
        penButton = QToolButton(self)
        penButton.setText('Pen')
        penButton.setIcon(QIcon(self.penFp))
        penButton.setPopupMode(QToolButton.InstantPopup)

        self.penMenu = QMenu(penButton)
        self.penMenu.addAction(self.setPenWidthAct)

        self.addPaletteToMenu(self.penMenu)

        penButton.setMenu(self.penMenu)

        self.toolbar.addWidget(penButton)

    def setPenColor(self, color):
        qColor = QColor(color)
        for a in self.penMenu.actions():
            a.setChecked(False)
            try:
                actionColor = QColor(a.color)
            except AttributeError:
                pass
            else:
                if actionColor == qColor:
                    a.setChecked(True)
                    self.penColor = actionColor

    def addPaletteToMenu(self, menu):
        for name, color in COLORS.items():
            paletteIcon = QPaletteIcon(color)
            action = QAction(paletteIcon, name, self, checkable=True)
            action.color = color
            action.triggered.connect(lambda checked, color=color: self.setPenColor(color))
            menu.addAction(action)

    def initToolbar(self):
        self.createActions()
        # self.toolbar.addAction(self.flattenAct)
        self.toolbar.addAction(self.undoAct)
        # self.toolbar.addSeparator()
        self.toolbar.addAction(self.selectionModeAct)
        self.toolbar.addAction(self.ovalModeAct)
        self.addPenToolMenu()


class QImagePainterToolbar(QToolBar):

    def __init__(self):
        super().__init__()
