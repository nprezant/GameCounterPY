from PyQt5.QtCore import Qt, QRectF, QMarginsF
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
        self._pen.setWidth(3)

        self._drawStartPos = None
        self._dynamicOval = None
        self._drawnItems = []

    def setMainPixmapFromPath(self, imgPath):

        # set image
        image = QImage(str(imgPath))
        pixmap = self.mainPixmapItem.pixmap()
        pixmap.convertFromImage(image)
        self.mainPixmapItem.setPixmap(pixmap)

        # set scene rect
        boundingRect = self.mainPixmapItem.boundingRect()
        margin = 2000
        boundingRect += QMarginsF(margin,margin,margin,margin)
        self.scene.setSceneRect(boundingRect)

        # center on image
        self.centerOn(self.mainPixmapItem)

    def wheelEvent(self, event: QWheelEvent):
        self.scaleView(2 ** float(-event.angleDelta().y()/280))

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Up:
            self.translateVertical(-10)
        elif key == Qt.Key_Down:
            self.translateVertical(10)
        elif key == Qt.Key_Left:
            self.translateHorizontal(-10)
        elif key == Qt.Key_Right:
            self.translateHorizontal(10)
        elif key == Qt.Key_Space:
            self.centerOn(self.mainPixmapItem)
        else:
            QGraphicsView().keyPressEvent(event)

    def translateVertical(self, dy):
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() + dy)

    def translateHorizontal(self, dx):
        bar = self.horizontalScrollBar()
        bar.setValue(bar.value() + dx)

    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        if (factor < 0.1 or factor > 100):
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
