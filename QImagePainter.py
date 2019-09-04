from PyQt5.QtCore import Qt, QRectF, QMarginsF, QTimeLine
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QWheelEvent, QKeyEvent, QIcon, QPen, QColor
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QToolBar, QAction
)

class QImagePainter(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)

        self.mainPixmapItem = self.scene.addPixmap(QPixmap())

        # self.mainPixmapItem.ItemIsMovable = True
        # self.setDragMode = QGraphicsView.ScrollHandDrag

        # policies
        # self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        # self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.toolbar = QToolBar()
        self.initToolbar()

        self._pen = QPen(QColor(50, 150, 230))
        self._pen.setWidth(10)

        self._drawStartPos = None
        self._dynamicOval = None
        self._drawnItems = []

        self._numScheduledScalings = 0
        self._numScheduledHTranslations = 0
        self._numScheduledVTranslations = 0

    def setMainPixmapFromPath(self, imgPath):

        # set image
        image = QImage(str(imgPath))
        pixmap = self.mainPixmapItem.pixmap()
        pixmap.convertFromImage(image)
        self.mainPixmapItem.setPixmap(pixmap)

        # set scene rect
        boundingRect = self.mainPixmapItem.boundingRect()
        margin = boundingRect.width() * 2
        boundingRect += QMarginsF(margin,margin,margin,margin)
        self.scene.setSceneRect(boundingRect)

        # manage view
        self.bestFitImage()

    def centerImage(self):
        self.centerOn(self.mainPixmapItem)

    def bestFitImage(self):
        self.fitInView(self.mainPixmapItem, Qt.KeepAspectRatio)

    def wheelEvent(self, event: QWheelEvent):
        numDegrees = event.angleDelta().y() / 8
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
        elif key == Qt.Key_Space:
            self.bestFitImage()
        else:
            super().keyPressEvent(event)

    def translateVertical(self, dy):
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() + dy)

    def translateHorizontal(self, dx):
        bar = self.horizontalScrollBar()
        bar.setValue(bar.value() + dx)

    def translateHorizontalEvent(self, dx):
        numSteps = dx * 2
        self._numScheduledHTranslations += numSteps

        if (self._numScheduledHTranslations * numSteps < 0): # if user moved the wheel in another direction, we reset previously scheduled scalings
            self._numScheduledHTranslations = numSteps

        anim = QTimeLine(350, self)
        anim.setUpdateInterval(20)

        anim.valueChanged.connect(self.translateHTime)
        anim.finished.connect(self.translateHAnimFinished)
        anim.start()

    def translateHTime(self, x):
        dx = self._numScheduledHTranslations / 200
        self.translateHorizontal(dx)

    def translateHAnimFinished(self):
        if (self._numScheduledHTranslations > 0):
            self._numScheduledHTranslations -= 1
        else:
            self._numScheduledHTranslations += 1
        self.sender().deleteLater()

    def translateVerticalEvent(self, dy):
        numSteps = dy * 2
        self._numScheduledVTranslations += numSteps

        if (self._numScheduledVTranslations * numSteps < 0): # if user moved the wheel in another direction, we reset previously scheduled scalings
            self._numScheduledVTranslations = numSteps

        anim = QTimeLine(350, self)
        anim.setUpdateInterval(20)

        anim.valueChanged.connect(self.translateVTime)
        anim.finished.connect(self.translateVAnimFinished)
        anim.start()

    def translateVTime(self, y):
        dy = self._numScheduledVTranslations / 200
        self.translateVertical(dy)

    def translateVAnimFinished(self):
        if (self._numScheduledVTranslations > 0):
            self._numScheduledVTranslations -= 1
        else:
            self._numScheduledVTranslations += 1
        self.sender().deleteLater()

    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        if (factor < 0.8 or factor > 100):
            return

        self.scale(scaleFactor, scaleFactor)

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

    def toggleOvalMode(self):
        if self.ovalModeAct.isChecked():
            self.selectionModeAct.setChecked(False)
        else:
            self.ovalModeAct.setChecked(True)

    def createActions(self):
        self.selectionModeAct = QAction(QIcon('./icons/selectIcon.png'), '&Select', self, checkable=True, checked=True, triggered=self.toggleSelectionMode)
        self.ovalModeAct = QAction(QIcon('./icons/ovalIcon.png'), '&Draw Oval', self, checkable=True, checked=False, triggered=self.toggleOvalMode)

    def initToolbar(self):
        self.createActions()
        self.toolbar.addAction(self.selectionModeAct)
        self.toolbar.addAction(self.ovalModeAct)



class QImagePainterToolbar(QToolBar):

    def __init__(self):
        super().__init__()
