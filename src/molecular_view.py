from PyQt4 import QtGui, QtCore

import molecular_scene
from paint_widget import PaintWidget

SCROLL_DISTANCE = 50
SCROLL_SPEED = 20
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3


class MolecularView(QtGui.QGraphicsView):
    """Graphics view that is used to show the contents of the main scene."""

    def __init__(self, parent):
        """Initialize the base class and set the default flags and parameters."""
        super(MolecularView, self).__init__(parent)
        self.setAcceptDrops(True)
        self.panning = False
        self.mouse_pos = None
        self.scale_factor = 1
        self.min_factor = 0.1
        self.max_factor = 2.5
        self.wheel_counter = 0
        self.overlay = OverlayWidget(self)
        self.overlay.show()
        self.paint_widget = PaintWidget(self)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.paint_widget)
        layout.setAlignment(QtCore.Qt.AlignBottom)
        layout.setMargin(0)
        self.setLayout(layout)

        self.scroll_dir = set()
        self.scroll_timer = QtCore.QTimer(self)
        self.scroll_timer.start(20)
        QtCore.QObject().connect(self.scroll_timer, QtCore.SIGNAL("timeout()"),
                                 self.scrollTimeOut)

        self.setRenderHint(QtGui.QPainter.Antialiasing, True)

    def autoScroll(self, point):
        """Check if the point is close to an edge and set the scroll direction
        to that edge if it is.
        point = scene point
        """
        self.scroll_dir = set()
        view_pos = self.mapFromScene(point)
        if view_pos.x() < SCROLL_DISTANCE:
            self.scroll_dir.add(LEFT)
        if self.width() - view_pos.x() < SCROLL_DISTANCE:
            self.scroll_dir.add(RIGHT)
        if view_pos.y() < SCROLL_DISTANCE:
            self.scroll_dir.add(UP)
        if self.height() - view_pos.y() < SCROLL_DISTANCE:
            self.scroll_dir.add(DOWN)

    def endScroll(self):
        """End the auto scrolling."""
        self.scroll_dir = set()

    def scrollTimeOut(self):
        """Scroll the scene on scroll timer timeout if direction is set."""
        if LEFT in self.scroll_dir:
            scroll_bar = self.horizontalScrollBar()
            scroll_bar.setValue(scroll_bar.value() - SCROLL_SPEED)
        if RIGHT in self.scroll_dir:
            scroll_bar = self.horizontalScrollBar()
            scroll_bar.setValue(scroll_bar.value() + SCROLL_SPEED)
        if UP in self.scroll_dir:
            scroll_bar = self.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.value() - SCROLL_SPEED)
        if DOWN in self.scroll_dir:
            scroll_bar = self.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.value() + SCROLL_SPEED)

    def wheelEvent(self, event):
        """Scale the view when wheel is scrolled."""
        if event.modifiers() == QtCore.Qt.ControlModifier:
            self.wheel_counter += event.delta()
            if abs(self.wheel_counter) > 80:
                self.wheel_counter = 0
                if event.delta() < 0 and self.scene().current_layer_i > 0:
                    self.scene().setLayer(self.scene().current_layer_i - 1)
                elif (event.delta() < 0 and self.scene().current_layer_i == 0 and
                    self.scene().draw_mode == molecular_scene.DRAW_SURFACE_ONLY):
                    self.scene().draw_mode = molecular_scene.DRAW_ALL
                elif (event.delta() > 0 and self.scene().current_layer_i == 0 and
                    self.scene().draw_mode == molecular_scene.DRAW_ALL):
                    self.scene().draw_mode = molecular_scene.DRAW_SURFACE_ONLY
                elif event.delta() > 0:
                    self.scene().setLayer(self.scene().current_layer_i + 1)
                self.scene().update()
        else:
            self.setTransformationAnchor(self.AnchorUnderMouse)
            factor = 1 + 0.1* abs(event.delta()/120.0)
            if event.delta() < 0:
                factor = 1.0/factor
            if (self.scale_factor*factor > self.min_factor and
                    self.scale_factor*factor < self.max_factor):
                self.scale_factor *= factor
                self.scale(factor, factor)

    def mousePressEvent(self, event):
        """Start panning the scene if middle mouse button is pressed."""
        super(MolecularView, self).mousePressEvent(event)
        if (event.button() == QtCore.Qt.MiddleButton    or
               (event.button() == QtCore.Qt.LeftButton  and
                event.modifiers() & QtCore.Qt.ControlModifier)):
            self.panning = True
            self.mouse_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """Stop panning if middle mouse button is released."""
        super(MolecularView, self).mouseReleaseEvent(event)
        self.panning = False
        self.mouse_pos = None

    def mouseMoveEvent(self, event):
        """If user is panning, move the scene based on the
        movement of the mouse.
        """
        super(MolecularView, self).mouseMoveEvent(event)
        if self.panning:
            diff = event.pos() - self.mouse_pos
            self.mouse_pos = event.pos()
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - diff.y())
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - diff.x())


class OverlayWidget(QtGui.QWidget):

    def __init__(self, parent):
        super(OverlayWidget, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

    def sizeHint(self):
        return QtCore.QSize(100, 100)

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QColor(0, 255, 0))
        qp.setFont(QtGui.QFont(QtGui.QFont().defaultFamily(), 20))
        scene = self.parent().scene()
        if scene.current_layer_i == 0 and scene.draw_mode == molecular_scene.DRAW_ALL:
            text = "T"
        elif scene.current_layer_i == 0:
            text = "S"
        else:
            text = str(scene.current_layer_i)
        qp.drawText(10, 30, text)
