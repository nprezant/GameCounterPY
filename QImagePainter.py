from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QWheelEvent, QKeyEvent
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem
)

class QImagePainter(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)

        self.mainPixmapItem = self.scene.addPixmap(QPixmap())

    def setMainPixmapFromPath(self, imgPath):
        image = QImage(str(imgPath))
        pixmap = self.mainPixmapItem.pixmap()
        pixmap.convertFromImage(image)
        self.mainPixmapItem.setPixmap(pixmap)

    def wheelEvent(self, event: QWheelEvent):
        self.scaleView(2 ** float(event.angleDelta().y()/240))

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Up:
            self.mainPixmapItem.moveBy(0,-10)
        elif key == Qt.Key_Down:
            self.mainPixmapItem.moveBy(0,10)
        elif key == Qt.Key_Left:
            self.mainPixmapItem.moveBy(-10,0)
        elif key == Qt.Key_Right:
            self.mainPixmapItem.moveBy(10,0)
        else:
            QGraphicsView().keyPressEvent(event)

    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        if (factor < 0.07 or factor > 100):
            return

        self.scale(scaleFactor, scaleFactor)

