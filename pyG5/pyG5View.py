"""
Created on 6 Aug 2021.

@author: Ben Lauret
"""

import logging

from math import cos, radians, sin, sqrt
from functools import wraps

from PyQt6.QtCore import QLine, QPoint, QPointF, QRectF, Qt, pyqtSlot
from PyQt6.QtGui import (
    QBrush,
    QPainter,
    QPolygonF,
    QColor,
    QLinearGradient,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

g5Width = 480
g5CenterX = g5Width / 2
g5Height = 360
g5CenterY = g5Height / 2

g5Diag = sqrt(g5Width**2 + g5Height**2)

mstokt = 1.94384


class pyG5DualStack(QWidget):
    """Base class for the G5 wdiget view."""

    def __init__(self, parent=None):
        """g5Widget Constructor.

        Args:
            parent: Parent Widget

        Returns:
            self
        """
        QWidget.__init__(self, parent)

        self.pyG5AI = pyG5AIWidget()
        self.pyG5AI.setFixedSize(g5Width, g5Height)
        self.pyG5HSI = pyG5HSIWidget()
        self.pyG5HSI.setFixedSize(g5Width, g5Height)

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.pyG5AI)
        self.vlayout.addWidget(self.pyG5HSI)
        self.vlayout.setSpacing(0)
        self.vlayout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.vlayout)


class pyG5Widget(QWidget):
    """Base class for the G5 wdiget view."""

    def __init__(self, parent=None):
        """g5Widget Constructor.

        Args:
            parent: Parent Widget

        Returns:
            self
        """
        QWidget.__init__(self, parent)

        self.logger = logging.getLogger(self.__class__.__name__)

        """property name, default value"""
        propertyList = [
            ("gpsdmedist", 0),
            ("gpshsisens", 0),
            ("nav1type", 0),
            ("nav2type", 0),
            ("gpstype", 0),
            ("avionicson", 0),
            ("hsiSource", 0),
            ("nav1fromto", 0),
            ("nav2fromto", 0),
            ("gpsfromto", 0),
            ("nav1crs", 0),
            ("nav1gsavailable", 0),
            ("nav1gs", 0),
            ("nav2crs", 0),
            ("gpscrs", 0),
            ("nav2gsavailable", 0),
            ("nav2gs", 0),
            ("nav1dft", 0),
            ("nav2dft", 0),
            ("gpsdft", 0),
            ("gpsgsavailable", 0),
            ("gpsvnavavailable", 0),
            ("gpsgs", 0),
            ("groundTrack", 0),
            ("magHeading", 0),
            ("windDirection", 0),
            ("windSpeed", 0),
            ("rollAngle", 0),
            ("pitchAngle", 0),
            ("gs", 0),
            ("kias", 0),
            ("kiasDelta", 0),
            ("ktas", 0),
            ("altitude", 0),
            ("alt_setting", 29.92),
            ("vh_ind_fpm", 0),
            ("turnRate", 0),
            ("slip", 0),
            ("headingBug", 0),
            ("vs", 30),
            ("vs0", 23),
            ("vfe", 88),
            ("vno", 118),
            ("vne", 127),
        ]

        def _make_setter(val):
            """Generate a setter function."""

            @wraps(val)
            def setter(inputVal):
                setattr(self, "_{}".format(val), inputVal)
                self.repaint()

            return setter

        for prop in propertyList:
            setattr(self, "_{}".format(prop[0]), prop[1])
            setattr(self, "{}".format(prop[0]), _make_setter(prop[0]))

    def setPen(self, width, color, style=Qt.PenStyle.SolidLine):
        """Set the pen color and width."""
        pen = self.qp.pen()
        pen.setColor(color)
        pen.setWidth(width)
        pen.setStyle(style)
        self.qp.setPen(pen)

    @pyqtSlot(dict)
    def drefHandler(self, retValues):
        """Handle the DREF update."""
        for idx, value in retValues.items():
            try:
                setattr(self, value[3], value[0])
            except Exception as e:
                self.logger.error("failed to set value {}: {}".format(value[5], e))
        self.repaint()


class pyG5HSIWidget(pyG5Widget):
    """Generate G5 wdiget view."""

    def __init__(self, parent=None):
        """g5Widget Constructor.

        Args:
            parent: Parent Widget

        Returns:
            self
        """
        pyG5Widget.__init__(self, parent)

    def getNavTypeString(self, navType, navIndex):
        """getNavTypeString.

        Args:
            type: type number

        Returns:
            string
        """
        value = int(navType)

        if value == 0:
            return ""
        elif value == 3:
            return "VOR" + navIndex
        elif value >= 4:
            return "LOC" + navIndex

        logging.error("Failed to decode navtype")

    def paintEvent(self, event):
        """Paint the widget."""
        self.qp = QPainter(self)

        greyColor = QColor(128, 128, 128, 255)
        rotatinghsiCircleRadius = 160
        hsiCircleRadius = 90
        hsiTextRadius = 120
        hsiCenter = 190
        groundTrackDiamondSize = 7

        headingBoxWidth = 50
        headingBoxHeight = 22

        font = self.qp.font()
        font.setPixelSize(headingBoxHeight - 2)
        font.setBold(True)
        self.qp.setFont(font)

        # Draw the background
        self.setPen(1, Qt.GlobalColor.black)
        self.qp.setBrush(QBrush(Qt.GlobalColor.black))
        self.qp.drawRect(0, 0, g5Width, g5Height)

        if self._avionicson == 0:
            self.setPen(1, Qt.GlobalColor.white)
            self.qp.drawLine(0, 0, g5Width, g5Height)
            self.qp.drawLine(0, g5Height, g5Width, 0)
            self.qp.end()
            return

        # Draw the Horizontal Situation Indicator circle
        self.setPen(2, greyColor)

        # offset the center to the Horizontal Situation Indicator center
        self.qp.translate(g5CenterX, hsiCenter)

        self.qp.drawArc(
            -hsiCircleRadius,
            -hsiCircleRadius,
            2 * hsiCircleRadius,
            2 * hsiCircleRadius,
            0,
            360 * 16,
        )

        # Draw the fixed Horizontal Situation Indicator marker
        hsiPeripheralMarkers = [
            45,
            90,
            135,
            225,
            270,
            315,
        ]
        self.setPen(2, Qt.GlobalColor.white)

        for marker in hsiPeripheralMarkers:
            self.qp.rotate(-marker)
            self.qp.drawLine(0, 170, 0, 185)
            self.qp.rotate(marker)

        # Draw the RotatingHSI lines and Text

        # rotate by the current magnetic heading
        self.qp.rotate(-self._magHeading)

        currentHead = 0
        while currentHead < 360:
            if (currentHead % 90) == 0:
                length = 20
            elif (currentHead % 10) == 0:
                length = 15
            else:
                length = 10
            self.qp.drawLine(
                0, rotatinghsiCircleRadius - length, 0, rotatinghsiCircleRadius
            )

            if currentHead == 0:
                text = "N"
            elif currentHead == 90:
                text = "E"
            elif currentHead == 180:
                text = "S"
            elif currentHead == 270:
                text = "W"
            elif (currentHead % 30) == 0:
                text = "{:2d}".format(int(currentHead / 10))
            else:
                text = ""

            if len(text):
                self.qp.translate(0, -hsiTextRadius)
                self.qp.rotate(+self._magHeading - currentHead)
                self.qp.drawText(
                    QRectF(
                        -self.qp.font().pixelSize() / 2 - 3,
                        -self.qp.font().pixelSize() / 2,
                        self.qp.font().pixelSize() + 6,
                        self.qp.font().pixelSize(),
                    ),
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                    text,
                )
                self.qp.rotate(-self._magHeading + currentHead)
                self.qp.translate(0, hsiTextRadius)

            self.qp.rotate(+5)
            currentHead += 5

        # draw the Heading bug
        self.setPen(1, Qt.GlobalColor.cyan)
        self.qp.setBrush(QBrush(Qt.GlobalColor.cyan))

        self.qp.rotate(180 + self._headingBug)

        self.qp.drawPolygon(
            QPolygonF(
                [
                    QPointF(-9, rotatinghsiCircleRadius - 1),
                    QPointF(+9, rotatinghsiCircleRadius - 1),
                    QPointF(+9, rotatinghsiCircleRadius + 6),
                    QPointF(+6, rotatinghsiCircleRadius + 6),
                    QPointF(0, rotatinghsiCircleRadius + 1),
                    QPointF(-6, rotatinghsiCircleRadius + 6),
                    QPointF(-9, rotatinghsiCircleRadius + 6),
                ]
            )
        )

        self.setPen(1, Qt.GlobalColor.black)
        gpscdianonciator = ""
        if int(self._hsiSource) == 2:
            cdiSource = "GPS"

            sensi = round(self._gpshsisens, 1)
            if sensi <= 0.1:
                gpscdianonciator = "LNAV"
            elif sensi == 0.12:
                gpscdianonciator = "DEPT"
            elif sensi == 0.4:
                gpscdianonciator = "TERM"
            elif sensi == 0.8:
                gpscdianonciator = "ENR"
            else:
                gpscdianonciator = ""

            navColor = Qt.GlobalColor.magenta
            navdft = self._gpsdft
            navfromto = self._gpsfromto
            navcrs = self._gpscrs
            if (self._gpsvnavavailable != -1000) or self._gpsgsavailable:
                vertAvailable = 1
            else:
                vertAvailable = 0
            gsDev = self._gpsgs
        elif int(self._hsiSource) == 1:
            cdiSource = "{}".format(self.getNavTypeString(self._nav2type, "2"))
            navColor = Qt.GlobalColor.green
            navdft = self._nav2dft
            navfromto = self._nav2fromto
            navcrs = self._nav2crs
            vertAvailable = self._nav2gsavailable
            gsDev = self._nav2gs
        else:
            cdiSource = "{}".format(self.getNavTypeString(self._nav1type, "1"))
            navColor = Qt.GlobalColor.green
            navdft = self._nav1dft
            navfromto = self._nav1fromto
            navcrs = self._nav1crs
            vertAvailable = self._nav1gsavailable
            gsDev = self._nav1gs

        self.qp.setBrush(QBrush(navColor))
        # Draw the CDI
        self.qp.rotate(90 - self._headingBug + navcrs)

        # CDI arrow
        self.qp.drawPolygon(
            QPolygonF(
                [
                    QPointF(rotatinghsiCircleRadius - 10, 0),
                    QPointF(rotatinghsiCircleRadius - 40, -20),
                    QPointF(rotatinghsiCircleRadius - 33, -3),
                    QPointF(hsiCircleRadius - 10, -3),
                    QPointF(hsiCircleRadius - 10, 3),
                    QPointF(rotatinghsiCircleRadius - 33, 3),
                    QPointF(rotatinghsiCircleRadius - 40, 20),
                ]
            )
        )
        # CDI bottom bar
        self.qp.drawPolygon(
            QPolygonF(
                [
                    QPointF(-rotatinghsiCircleRadius + 10, -3),
                    QPointF(-hsiCircleRadius + 10, -3),
                    QPointF(-hsiCircleRadius + 10, +3),
                    QPointF(-rotatinghsiCircleRadius + 10, +3),
                ]
            )
        )
        # CDI deflection bar
        if int(navfromto) != 0:
            hsiDeflectionBound = hsiCircleRadius / 75 * 2
            deflection = (
                max(min(navdft, hsiDeflectionBound), -hsiDeflectionBound) / 2 * 75
            )
            self.qp.drawPolygon(
                QPolygonF(
                    [
                        QPointF(hsiCircleRadius - 10, deflection - 3),
                        QPointF(-hsiCircleRadius + 10, deflection - 3),
                        QPointF(-hsiCircleRadius + 10, deflection + 3),
                        QPointF(hsiCircleRadius - 10, deflection + 3),
                    ]
                )
            )

            # NAV1 FromTo
            fromToTipX = 65
            if int(navfromto) == 2:
                self.qp.rotate(180)

            self.qp.drawPolygon(
                QPolygonF(
                    [
                        QPointF(fromToTipX - 10, 0),
                        QPointF(fromToTipX - 40, -20),
                        QPointF(fromToTipX - 30, 0),
                        QPointF(fromToTipX - 40, 20),
                    ]
                )
            )
            if int(navfromto) == 2:
                self.qp.rotate(180)

        self.qp.rotate(90)
        # CDI deflection circle
        self.setPen(2, Qt.GlobalColor.white)
        self.qp.setBrush(QBrush(Qt.GlobalColor.black))

        for i in [-81, -41, 31, 69]:
            self.qp.drawArc(
                QRectF(
                    i,
                    -6,
                    12,
                    12,
                ),
                0,
                360 * 16,
            )

        self.qp.resetTransform()

        font = self.qp.font()
        font.setPixelSize(15)
        font.setBold(False)
        self.qp.setFont(font)
        if int(self._hsiSource) == 2:
            self.setPen(2, Qt.GlobalColor.magenta)
        else:
            self.setPen(2, Qt.GlobalColor.green)

        self.qp.drawText(
            QRectF(g5CenterX - 70, hsiCenter - 50, 65, 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            cdiSource,
        )

        if len(gpscdianonciator):
            self.qp.drawText(
                QRectF(g5CenterX + 25, hsiCenter - 50, 65, 18),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                gpscdianonciator,
            )

        # Draw the heading Bug indicator bottom corner
        self.setPen(2, Qt.GlobalColor.cyan)
        self.qp.setBrush(QBrush(Qt.GlobalColor.black))

        headingWidth = 105
        headingHeigth = 30
        self.qp.drawRect(QRectF(g5Width, g5Height, -headingWidth, -headingHeigth))

        # draw the bug symbol
        self.setPen(1, Qt.GlobalColor.cyan)
        self.qp.setBrush(QBrush(Qt.GlobalColor.cyan))

        self.qp.drawPolygon(
            QPolygonF(
                [
                    QPointF(381, 336),
                    QPointF(381, 354),
                    QPointF(387, 354),
                    QPointF(387, 349),
                    QPointF(382, 346),
                    QPointF(382, 344),
                    QPointF(387, 341),
                    QPointF(387, 336),
                ]
            )
        )

        self.qp.drawText(
            QRectF(412, 336, 65, 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "{:03d}˚".format(int(self._headingBug)),
        )

        # draw the dist box
        if int(self._hsiSource) == 2:
            font.setPixelSize(12)
            font.setBold(False)
            self.qp.setFont(font)
            distRect = QRectF(g5Width - 105, 0, 105, 45)

            self.setPen(2, greyColor)
            self.qp.setBrush(QBrush(Qt.GlobalColor.black))
            self.qp.drawRect(distRect)

            self.qp.drawText(
                distRect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                "Dist NM",
            )

            font.setPixelSize(18)
            font.setBold(True)
            self.qp.setFont(font)
            self.setPen(1, navColor)

            distRect = QRectF(g5Width - 105, 12, 105, 45 - 12)
            self.qp.drawText(
                distRect,
                Qt.AlignmentFlag.AlignCenter,
                "{}".format(round(self._gpsdmedist, 1)),
            )

        # set default font size
        font = self.qp.font()
        font.setPixelSize(18)
        font.setBold(True)
        self.qp.setFont(font)

        # draw the wind box
        self.setPen(2, greyColor)
        self.qp.setBrush(QBrush(Qt.GlobalColor.black))

        self.qp.drawRect(0, 0, 105, 45)

        self.setPen(1, Qt.GlobalColor.white)
        self.qp.setBrush(QBrush(Qt.GlobalColor.white))

        self.qp.translate(25, 25)

        self.qp.rotate(180 - self._magHeading + self._windDirection)

        self.qp.drawPolygon(
            QPolygonF(
                [
                    QPointF(-5, 0),
                    QPointF(0, -10),
                    QPointF(5, 0),
                    QPointF(2, 0),
                    QPointF(2, 10),
                    QPointF(-2, 10),
                    QPointF(-2, 0),
                ]
            )
        )

        self.qp.resetTransform()

        self.qp.drawText(
            QRectF(50, 2, 50, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "{:03d}˚".format(int(self._windDirection)),
        )

        self.qp.drawText(
            QRectF(50, 22, 50, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "{:02d}kt".format(int(self._windSpeed * mstokt)),
        )

        # Draw the magnetic heading box
        self.setPen(2, greyColor)
        self.qp.setBrush(QBrush(Qt.GlobalColor.black))
        self.qp.drawPolygon(
            QPolygonF(
                [
                    QPointF(g5CenterX - headingBoxWidth / 2, 1),
                    QPointF(g5CenterX - headingBoxWidth / 2, headingBoxHeight),
                    QPointF(g5CenterX - 6, headingBoxHeight),
                    QPointF(g5CenterX, headingBoxHeight + 8),
                    QPointF(g5CenterX + 6, headingBoxHeight),
                    QPointF(g5CenterX + headingBoxWidth / 2, headingBoxHeight),
                    QPointF(g5CenterX + headingBoxWidth / 2, 1),
                ]
            )
        )

        self.qp.drawText(
            QRectF(
                g5CenterX - headingBoxWidth / 2, 1, headingBoxWidth, headingBoxHeight
            ),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "{:03d}˚".format(int(self._magHeading)),
        )

        # Draw the ground track
        self.setPen(0, Qt.GlobalColor.transparent)
        self.qp.setBrush(QBrush(Qt.GlobalColor.magenta))
        self.qp.translate(g5CenterX, hsiCenter)
        self.qp.rotate(-self._magHeading + self._groundTrack)
        self.qp.drawPolygon(
            QPolygonF(
                [
                    QPointF(
                        -groundTrackDiamondSize,
                        -rotatinghsiCircleRadius - groundTrackDiamondSize,
                    ),
                    QPointF(
                        +groundTrackDiamondSize,
                        -rotatinghsiCircleRadius - groundTrackDiamondSize,
                    ),
                    QPointF(+0, -rotatinghsiCircleRadius),
                ]
            )
        )
        self.setPen(3, greyColor, Qt.PenStyle.DashLine)
        self.qp.drawLine(0, 0, 0, -rotatinghsiCircleRadius)
        self.qp.resetTransform()

        # draw the aircraft
        self.setPen(1, Qt.GlobalColor.white)
        self.qp.setBrush(QBrush(Qt.GlobalColor.white))

        self.qp.drawPolygon(
            QPolygonF(
                [
                    QPointF(240, 163),
                    QPointF(235, 169),
                    QPointF(235, 180),
                    QPointF(215, 195),
                    QPointF(215, 200),
                    QPointF(235, 195),
                    QPointF(235, 205),
                    QPointF(227, 213),
                    QPointF(227, 217),
                    QPointF(240, 213),
                    QPointF(253, 217),
                    QPointF(253, 213),
                    QPointF(245, 205),
                    QPointF(245, 195),
                    QPointF(265, 200),
                    QPointF(265, 195),
                    QPointF(245, 180),
                    QPointF(245, 169),
                ]
            )
        )

        # draw the GlideScope
        gsWidth = 16
        gsHeigth = 192
        gsCircleRad = 10
        gsFromLeft = 20
        gsDiamond = 16

        if vertAvailable:
            # Vertical guidance source
            rect = QRectF(
                g5Width - gsFromLeft - gsWidth,
                hsiCenter - gsHeigth / 2 - 15,
                gsWidth,
                15,
            )

            font.setPixelSize(12)
            self.qp.setFont(font)
            self.setPen(1, navColor)

            vertSourceTxt = "G"
            if int(self._hsiSource) == 2 and self._gpsgsavailable == 0:
                vertSourceTxt = "V"

            self.qp.drawText(
                rect,
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                vertSourceTxt,
            )

            self.setPen(2, greyColor)
            self.qp.setBrush(QBrush(Qt.GlobalColor.transparent))

            self.qp.drawRect(rect)

            # main rectangle
            self.qp.drawRect(
                QRectF(
                    g5Width - gsFromLeft - gsWidth,
                    hsiCenter - gsHeigth / 2,
                    gsWidth,
                    gsHeigth,
                )
            )

            self.qp.drawLine(
                g5Width - gsFromLeft - gsWidth,
                hsiCenter,
                g5Width - gsFromLeft,
                hsiCenter,
            )

            for offset in [-70, -35, 35, 70]:
                self.qp.drawEllipse(
                    QPointF(
                        int(g5Width - gsFromLeft - gsWidth / 2),
                        int(hsiCenter + offset),
                    ),
                    gsCircleRad / 2,
                    gsCircleRad / 2,
                )

            self.setPen(1, Qt.GlobalColor.black)
            self.qp.setBrush(QBrush(navColor))

            self.qp.translate(
                g5Width - gsFromLeft - gsWidth, hsiCenter + gsDev / 2.5 * gsHeigth / 2
            )
            self.qp.drawPolygon(
                QPolygonF(
                    [
                        QPointF(0, 0),
                        QPointF(gsDiamond / 2, gsDiamond / 2),
                        QPointF(gsDiamond, 0),
                        QPointF(gsDiamond / 2, -gsDiamond / 2),
                    ]
                )
            )

            self.qp.resetTransform()

        # draw the CRS selection

        crsBoxHeight = 30
        crsBoxWidth = 105

        self.setPen(2, greyColor)
        self.qp.setBrush(QBrush(Qt.GlobalColor.black))

        rect = QRectF(0, g5Height - crsBoxHeight, crsBoxWidth, crsBoxHeight)
        self.qp.drawRect(rect)

        self.setPen(1, Qt.GlobalColor.white)

        font = self.qp.font()
        font.setPixelSize(15)
        self.qp.setFont(font)

        rect = QRectF(1, g5Height - crsBoxHeight + 1, crsBoxWidth - 2, crsBoxHeight - 2)
        self.qp.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, "CRS")

        font = self.qp.font()
        font.setPixelSize(25)
        self.qp.setFont(font)
        if int(self._hsiSource) == 2:
            self.setPen(1, Qt.GlobalColor.magenta)
        else:
            self.setPen(1, Qt.GlobalColor.green)
        rect = QRectF(40, g5Height - crsBoxHeight + 1, 65, crsBoxHeight - 2)
        self.qp.drawText(
            rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "{:03d}˚".format(int(navcrs))
        )

        self.qp.end()


class pyG5AIWidget(pyG5Widget):
    """Generate G5 wdiget view."""

    def __init__(self, parent=None):
        """g5Widget Constructor.

        Args:
            parent: Parent Widget

        Returns:
            self
        """
        pyG5Widget.__init__(self, parent)

        # parameters
        self.rollArcRadius = g5CenterY * 0.8
        self._pitchScale = 25

    def paintEvent(self, event):
        """Paint the widget."""
        diamondHeight = 14
        diamondWidth = 14

        self.qp = QPainter(self)

        if self._avionicson == 0:
            self.setPen(1, Qt.GlobalColor.black)
            self.qp.setBrush(QBrush(Qt.GlobalColor.black))
            self.qp.drawRect(0, 0, g5Width, g5Height)
            self.setPen(1, Qt.GlobalColor.white)
            self.qp.drawLine(0, 0, g5Width, g5Height)
            self.qp.drawLine(0, g5Height, g5Width, 0)
            self.qp.end()
            return

        # set default font size
        font = self.qp.font()
        font.setPixelSize(6)
        font.setBold(True)
        self.qp.setFont(font)

        self.setPen(1, Qt.GlobalColor.white)
        grad = QLinearGradient(g5CenterX, g5Height, g5CenterX, 0)
        grad.setColorAt(1, QColor(0, 50, 200, 255))
        grad.setColorAt(0, QColor(0, 255, 255, 255))
        self.qp.setBrush(grad)

        # draw contour + backgorun sky
        self.qp.drawRect(QRectF(0, 0, g5Width, g5Height))

        # draw the rotating part depending on the roll angle
        self.qp.translate(g5CenterX, g5CenterY)
        self.qp.rotate(-self._rollAngle)

        # draw the ground
        grad = QLinearGradient(
            g5CenterX,
            +self._pitchAngle / self._pitchScale * g5CenterY,
            g5CenterX,
            +g5Diag,
        )
        grad.setColorAt(0, QColor(152, 103, 45))
        grad.setColorAt(1, QColor(255, 222, 173))
        self.qp.setBrush(grad)

        self.qp.drawRect(
            QRectF(
                QPointF(
                    -g5Diag,
                    +self._pitchAngle / self._pitchScale * g5CenterY,
                ),
                QPointF(
                    +g5Diag,
                    +g5Diag,
                ),
            )
        )

        # draw the pitch lines
        height = 0
        pitch = 0
        width = [10, 20, 10, 30]
        mode = 0
        while height < self.rollArcRadius - 40:
            pitch += 2.5
            height = (
                pitch / self._pitchScale * g5CenterY
                + self._pitchAngle / self._pitchScale * g5CenterY
            )
            self.qp.drawLine(
                QPointF(
                    -width[mode],
                    height,
                ),
                QPointF(
                    width[mode],
                    height,
                ),
            )
            if width[mode] == 30:
                self.qp.drawText(QPoint(30 + 3, int(height + 2)), str(int(pitch)))
                self.qp.drawText(QPoint(-40, int(height + 2)), str(int(pitch)))
            mode = (mode + 1) % 4

        height = 0
        pitch = 0
        width = [10, 20, 10, 30]
        mode = 0
        while height > -self.rollArcRadius + 30:
            pitch -= 2.5
            height = (
                pitch / self._pitchScale * g5CenterY
                + self._pitchAngle / self._pitchScale * g5CenterY
            )
            self.qp.drawLine(
                QPointF(
                    -width[mode],
                    height,
                ),
                QPointF(
                    width[mode],
                    height,
                ),
            )
            if width[mode] == 30:
                self.qp.drawText(QPoint(30 + 3, int(height + 2)), str(abs(int(pitch))))
                self.qp.drawText(QPoint(-40, int(height + 2)), str(abs(int(pitch))))

            mode = (mode + 1) % 4

        # draw the static roll arc
        self.setPen(3, Qt.GlobalColor.white)

        bondingRect = QRectF(
            -self.rollArcRadius,
            -self.rollArcRadius,
            2 * self.rollArcRadius,
            2 * self.rollArcRadius,
        )
        self.qp.drawArc(bondingRect, 30 * 16, 120 * 16)

        # draw the Roll angle arc markers
        rollangleindicator = [
            [-30, 10],
            [-45, 5],
            [-135, 5],
            [-150, 10],
            [-60, 10],
            [-70, 5],
            [-80, 5],
            [-100, 5],
            [-110, 5],
            [-120, 10],
        ]

        self.qp.setBrush(QBrush(Qt.GlobalColor.white))
        self.setPen(2, Qt.GlobalColor.white)
        for lineParam in rollangleindicator:
            self.qp.drawLine(self.alongRadiusCoord(lineParam[0], lineParam[1]))

        self.setPen(1, Qt.GlobalColor.white)
        # draw the diamond on top of the roll arc
        self.qp.drawPolygon(
            QPolygonF(
                [
                    QPointF(
                        0,
                        -self.rollArcRadius - 2,
                    ),
                    QPointF(-diamondWidth / 2, -self.rollArcRadius - diamondHeight),
                    QPointF(+diamondWidth / 2, -self.rollArcRadius - diamondHeight),
                ]
            )
        )

        self.qp.resetTransform()

        # create the fixed diamond

        fixedDiamond = QPolygonF(
            [
                QPointF(g5CenterX, g5CenterY - self.rollArcRadius + 2),
                QPointF(
                    g5CenterX + diamondWidth / 2,
                    g5CenterY - self.rollArcRadius + diamondHeight,
                ),
                QPointF(
                    g5CenterX - diamondWidth / 2,
                    g5CenterY - self.rollArcRadius + diamondHeight,
                ),
            ]
        )

        self.qp.drawPolygon(fixedDiamond)

        # create the nose
        self.qp.setBrush(QBrush(Qt.GlobalColor.yellow))
        self.qp.setBackgroundMode(Qt.BGMode.OpaqueMode)

        self.setPen(1, Qt.GlobalColor.black)

        # solid polygon left
        nose = QPolygonF(
            [
                QPointF(g5CenterX - 1, g5CenterY + 1),
                QPointF(g5CenterX - 75, g5CenterY + 38),
                QPointF(g5CenterX - 54, g5CenterY + 38),
            ]
        )
        self.qp.drawPolygon(nose)

        # solid polygon right
        nose = QPolygonF(
            [
                QPointF(g5CenterX + 1, g5CenterY + 1),
                QPointF(g5CenterX + 75, g5CenterY + 38),
                QPointF(g5CenterX + 54, g5CenterY + 38),
            ]
        )
        self.qp.drawPolygon(nose)

        # solid marker left
        marker = QPolygonF(
            [
                QPointF(120, g5CenterY - 5),
                QPointF(155, g5CenterY - 5),
                QPointF(160, g5CenterY),
                QPointF(155, g5CenterY + 5),
                QPointF(120, g5CenterY + 5),
            ]
        )
        self.qp.drawPolygon(marker)

        # solid marker right
        marker = QPolygonF(
            [
                QPointF(360, g5CenterY - 5),
                QPointF(325, g5CenterY - 5),
                QPointF(320, g5CenterY),
                QPointF(325, g5CenterY + 5),
                QPointF(360, g5CenterY + 5),
            ]
        )
        self.qp.drawPolygon(marker)

        brush = QBrush(QColor(0x7E, 0x7E, 0x34, 255))
        self.qp.setBrush(brush)

        # cross pattern polygon left
        nose = QPolygonF(
            [
                QPointF(g5CenterX - 2, g5CenterY + 2),
                QPointF(g5CenterX - 33, g5CenterY + 38),
                QPointF(g5CenterX - 54, g5CenterY + 38),
            ]
        )
        self.qp.drawPolygon(nose)

        # cross pattern polygon right
        nose = QPolygonF(
            [
                QPointF(g5CenterX + 2, g5CenterY + 2),
                QPointF(g5CenterX + 33, g5CenterY + 38),
                QPointF(g5CenterX + 54, g5CenterY + 38),
            ]
        )
        self.qp.drawPolygon(nose)

        self.setPen(0, Qt.GlobalColor.transparent)
        # solid polygon right
        nose = QPolygonF(
            [
                QPointF(120, g5CenterY),
                QPointF(160, g5CenterY),
                QPointF(155, g5CenterY + 5),
                QPointF(120, g5CenterY + 5),
            ]
        )
        self.qp.drawPolygon(nose)
        # solid polygon right
        nose = QPolygonF(
            [
                QPointF(360, g5CenterY),
                QPointF(320, g5CenterY),
                QPointF(325, g5CenterY + 5),
                QPointF(360, g5CenterY + 5),
            ]
        )
        self.qp.drawPolygon(nose)

        #################################################
        # SPEED TAPE
        #################################################

        speedBoxLeftAlign = 7
        speedBoxHeight = 50
        speedBoxWdith = 75
        speedBoxSpikedimension = 10
        tasHeight = 30
        speedDeltaWidth = 4

        tapeScale = 50

        self.setPen(0, Qt.GlobalColor.transparent)

        self.qp.setBrush(QBrush(QColor(0, 0, 0, 90)))
        self.qp.drawRect(QRectF(0, 0, speedBoxLeftAlign + speedBoxWdith + 15, g5Height))

        if (self._kias + tapeScale / 2) > self._vne:

            brush = QBrush(QColor(Qt.GlobalColor.red))
            self.qp.setBrush(brush)

            self.qp.drawRect(
                QRectF(
                    speedBoxLeftAlign + speedBoxWdith + 8,
                    0,
                    8,
                    (1 - 2 * (self._vne - self._kias) / tapeScale) * g5CenterY,
                )
            )

        if (self._kias + tapeScale / 2) > self._vno:

            brush = QBrush(QColor(Qt.GlobalColor.yellow))
            self.qp.setBrush(brush)

            self.qp.drawRect(
                QRectF(
                    speedBoxLeftAlign + speedBoxWdith + 8,
                    (1 - 2 * (self._vne - self._kias) / tapeScale) * g5CenterY,
                    8,
                    (2 * (self._vne - self._vno) / tapeScale) * g5CenterY,
                )
            )

        if (self._kias + tapeScale / 2) > self._vs:

            brush = QBrush(QColor(Qt.GlobalColor.green))
            self.qp.setBrush(brush)
            self.qp.drawRect(
                QRectF(
                    speedBoxLeftAlign + speedBoxWdith + 8,
                    max(0, (1 - 2 * (self._vno - self._kias) / tapeScale) * g5CenterY),
                    8,
                    (1 - 2 * (self._vs - self._kias) / tapeScale) * g5CenterY,
                )
            )

        if (self._kias + tapeScale / 2) > self._vs:

            brush = QBrush(QColor(Qt.GlobalColor.white))
            self.qp.setBrush(brush)
            self.qp.drawRect(
                QRectF(
                    speedBoxLeftAlign + speedBoxWdith + 13,
                    max(0, (1 - 2 * (self._vfe - self._kias) / tapeScale) * g5CenterY),
                    3,
                    (1 - 2 * (self._vs0 - self._kias) / tapeScale) * g5CenterY,
                )
            )

        self.setPen(2, Qt.GlobalColor.white)

        self.qp.setBackgroundMode(Qt.BGMode.TransparentMode)
        font = self.qp.font()
        font.setPixelSize(speedBoxHeight - 15)

        # set default font size
        self.qp.setFont(font)

        currentTape = int(self._kias + tapeScale / 2)
        while currentTape > max(0, self._kias - tapeScale / 2):
            if (currentTape % 10) == 0:

                tapeHeight = (
                    1 - 2 * (currentTape - self._kias) / tapeScale
                ) * g5CenterY
                self.qp.drawLine(
                    QPointF(speedBoxLeftAlign + speedBoxWdith + 5, tapeHeight),
                    QPointF(speedBoxLeftAlign + speedBoxWdith + 15, tapeHeight),
                )

                self.qp.drawText(
                    QRectF(
                        speedBoxLeftAlign,
                        tapeHeight - speedBoxHeight / 2,
                        speedBoxWdith,
                        speedBoxHeight,
                    ),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    "{:d}".format(int(currentTape)),
                )

            elif (currentTape % 5) == 0:
                self.qp.drawLine(
                    QPointF(
                        speedBoxLeftAlign + speedBoxWdith + 8,
                        (1 - 2 * (currentTape - self._kias) / tapeScale) * g5CenterY,
                    ),
                    QPointF(
                        speedBoxLeftAlign + speedBoxWdith + 15,
                        (1 - 2 * (currentTape - self._kias) / tapeScale) * g5CenterY,
                    ),
                )

            currentTape -= 1

        speedBox = QPolygonF(
            [
                QPointF(speedBoxLeftAlign, g5CenterY + speedBoxHeight / 2),
                QPointF(
                    speedBoxLeftAlign + speedBoxWdith, g5CenterY + speedBoxHeight / 2
                ),
                QPointF(
                    speedBoxLeftAlign + speedBoxWdith,
                    g5CenterY + speedBoxSpikedimension,
                ),
                QPointF(
                    speedBoxLeftAlign + speedBoxWdith + speedBoxSpikedimension,
                    g5CenterY,
                ),
                QPointF(
                    speedBoxLeftAlign + speedBoxWdith,
                    g5CenterY - speedBoxSpikedimension,
                ),
                QPointF(
                    speedBoxLeftAlign + speedBoxWdith, g5CenterY - speedBoxHeight / 2
                ),
                QPointF(speedBoxLeftAlign, g5CenterY - speedBoxHeight / 2),
            ]
        )

        self.setPen(2, Qt.GlobalColor.white)

        brush = QBrush(QColor(0, 0, 0, 255))
        self.qp.setBrush(brush)

        self.qp.drawPolygon(speedBox)

        font = self.qp.font()
        font.setPixelSize(speedBoxHeight - 10)
        # set default font size
        self.qp.setFont(font)

        self.qp.drawText(
            QRectF(
                speedBoxLeftAlign,
                g5CenterY - speedBoxHeight / 2,
                speedBoxWdith,
                speedBoxHeight,
            ),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "{:03d}".format(int(self._kias)),
        )

        # draw the TAS box
        rect = QRectF(
            0,
            0,
            speedBoxLeftAlign + speedBoxWdith + 15,
            tasHeight,
        )
        self.qp.drawRect(rect)

        font = self.qp.font()
        font.setPixelSize(20)
        # set default font size
        self.qp.setFont(font)

        self.qp.drawText(
            rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "TAS {:03d} kt".format(int(self._ktas)),
        )

        # draw the TAS box
        rect = QRectF(
            0,
            g5Height - tasHeight,
            speedBoxLeftAlign + speedBoxWdith + 15,
            tasHeight,
        )
        self.qp.drawRect(rect)
        self.qp.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "GS")

        self.setPen(2, Qt.GlobalColor.magenta)

        self.qp.drawText(
            rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "{:03d} kt".format(int(self._gs * mstokt)),
        )

        self.setPen(1, Qt.GlobalColor.magenta)

        brush = QBrush(Qt.GlobalColor.magenta)
        self.qp.setBrush(brush)

        self.qp.drawRect(
            QRectF(
                speedBoxLeftAlign + speedBoxWdith + 15,
                g5CenterY,
                speedDeltaWidth,
                -2 * (self._kiasDelta * 10) / tapeScale * g5CenterY,
            )
        )

        #################################################
        # ALTITUDE TAPE
        #################################################

        altBoxRightAlign = 7
        altBoxHeight = 30
        altBoxWdith = 75
        altBoxSpikedimension = 10
        altTapeScale = 300
        altTapeLeftAlign = g5Width - altBoxRightAlign - altBoxWdith
        altSettingHeight = 30

        vsScale = 30
        vsIndicatorWidth = 7

        alttapteLeftBound = altTapeLeftAlign - 1.5 * altBoxSpikedimension
        self.setPen(0, Qt.GlobalColor.transparent)
        self.qp.setBrush(QBrush(QColor(0, 0, 0, 90)))
        self.qp.drawRect(
            QRectF(alttapteLeftBound, 0, g5Width - alttapteLeftBound, int(g5Height))
        )
        self.setPen(2, Qt.GlobalColor.white)

        self.qp.setBackgroundMode(Qt.BGMode.TransparentMode)
        font = self.qp.font()
        font.setPixelSize(10)
        # set default font size
        self.qp.setFont(font)

        # VS tape
        currentTape = vsScale

        while currentTape >= 0:
            tapeHeight = (vsScale - currentTape) / vsScale * g5Height
            if (currentTape % 5) == 0:

                self.qp.drawLine(
                    QPointF(g5Width - 10, tapeHeight),
                    QPointF(g5Width, tapeHeight),
                )
                self.qp.drawText(
                    QRectF(
                        g5Width - 30,
                        tapeHeight - 5,
                        15,
                        vsIndicatorWidth + 3,
                    ),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    "{:d}".format(abs(int(currentTape - vsScale / 2))),
                )
            else:
                self.qp.drawLine(
                    QPointF(g5Width - vsIndicatorWidth, tapeHeight),
                    QPointF(g5Width, tapeHeight),
                )

            currentTape -= 1
        # tapeHeight = (vsScale - currentTape) / vsScale * g5Height
        vsHeight = -self._vh_ind_fpm / 100 / vsScale * g5Height
        vsRect = QRectF(g5Width, g5CenterY, -vsIndicatorWidth, vsHeight)

        self.setPen(0, Qt.GlobalColor.transparent)

        brush = QBrush(QColor(Qt.GlobalColor.magenta))
        self.qp.setBrush(brush)

        self.qp.drawRect(vsRect)

        self.setPen(2, Qt.GlobalColor.white)

        font = self.qp.font()
        font.setPixelSize(20)
        # set default font size
        self.qp.setFont(font)

        # altitude tape
        currentTape = int(self._altitude + altTapeScale / 2)

        while currentTape > self._altitude - altTapeScale / 2:
            if (currentTape % 20) == 0:

                tapeHeight = (
                    1 - 2 * (currentTape - self._altitude) / altTapeScale
                ) * g5CenterY
                self.qp.drawLine(
                    QPointF(altTapeLeftAlign - 1.5 * altBoxSpikedimension, tapeHeight),
                    QPointF(altTapeLeftAlign - altBoxSpikedimension / 2, tapeHeight),
                )
                if (currentTape % 100) == 0:

                    self.qp.drawText(
                        QRectF(
                            altTapeLeftAlign,
                            tapeHeight - speedBoxHeight / 2,
                            speedBoxWdith,
                            speedBoxHeight,
                        ),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        "{:d}".format(int(currentTape)),
                    )

            currentTape -= 1

        altBox = QPolygonF(
            [
                QPointF(g5Width - altBoxRightAlign, g5CenterY - altBoxHeight / 2),
                QPointF(
                    altTapeLeftAlign,
                    g5CenterY - altBoxHeight / 2,
                ),
                QPointF(
                    altTapeLeftAlign,
                    g5CenterY - altBoxSpikedimension,
                ),
                QPointF(
                    altTapeLeftAlign - altBoxSpikedimension,
                    g5CenterY,
                ),
                QPointF(
                    altTapeLeftAlign,
                    g5CenterY + altBoxSpikedimension,
                ),
                QPointF(
                    altTapeLeftAlign,
                    g5CenterY + altBoxHeight / 2,
                ),
                QPointF(g5Width - altBoxRightAlign, g5CenterY + altBoxHeight / 2),
            ]
        )

        brush = QBrush(QColor(0, 0, 0, 255))
        self.qp.setBrush(brush)

        self.qp.drawPolygon(altBox)

        self.qp.drawText(
            QRectF(
                altTapeLeftAlign,
                g5CenterY - altBoxHeight / 2,
                altBoxWdith,
                altBoxHeight,
            ),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "{:05d}".format(int(self._altitude)),
        )

        pen = self.qp.pen()
        pen.setColor(Qt.GlobalColor.cyan)
        pen.setWidth(2)
        self.qp.setPen(pen)
        leftAlign = altTapeLeftAlign - 1.5 * altBoxSpikedimension
        rect = QRectF(
            leftAlign,
            g5Height - altSettingHeight,
            g5Width - leftAlign,
            altSettingHeight,
        )
        self.qp.drawRect(rect)
        self.qp.drawText(
            rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "{:02.02f}".format(self._alt_setting),
        )

        #################################################
        # Turn coordinator
        #################################################

        turnrateHalfWidth = 62
        turnrateHeight = 15
        slipballHeigh = 320
        slipballRadius = 15
        slipballMarkeWidth = 6
        slipballMovementMax = 1
        slipballMovementWdith = 15

        self.setPen(1, QColor(0, 0, 0, 127))

        self.qp.drawLine(
            QPointF(g5CenterX, g5Height - turnrateHeight),
            QPointF(g5CenterX, g5Height),
        )
        self.qp.drawLine(
            QPointF(g5CenterX - turnrateHalfWidth, g5Height - turnrateHeight),
            QPointF(g5CenterX + turnrateHalfWidth, g5Height - turnrateHeight),
        )

        self.setPen(0, Qt.GlobalColor.transparent)

        brush = QBrush(QColor(Qt.GlobalColor.magenta))
        self.qp.setBrush(brush)
        rect = QRectF(
            g5CenterX,
            g5Height - turnrateHeight + 1,
            min(max(self._turnRate, -73), 73) / 32 * turnrateHalfWidth,
            turnrateHeight - 2,
        )
        self.qp.drawRect(rect)

        self.setPen(1, QColor(255, 255, 255, 128))

        self.qp.drawLine(
            QPointF(g5CenterX - turnrateHalfWidth, g5Height - turnrateHeight),
            QPointF(g5CenterX - turnrateHalfWidth, g5Height),
        )
        self.qp.drawLine(
            QPointF(g5CenterX + turnrateHalfWidth, g5Height - turnrateHeight),
            QPointF(g5CenterX + turnrateHalfWidth, g5Height),
        )

        # slip ball
        # draw the static roll arc
        self.setPen(2, QColor(0, 0, 0, 128))

        self.qp.setBrush(QBrush(QColor(220, 220, 220)))

        self.qp.drawRect(
            QRectF(
                g5CenterX - slipballRadius,
                slipballHeigh - slipballRadius,
                -slipballMarkeWidth,
                2 * slipballRadius,
            )
        )
        self.qp.drawRect(
            QRectF(
                g5CenterX + slipballRadius,
                slipballHeigh - slipballRadius,
                slipballMarkeWidth,
                2 * slipballRadius,
            )
        )
        # set slip ball gradian
        grad = QRadialGradient(
            g5CenterX - self._slip * slipballMovementMax * slipballMovementWdith,
            slipballHeigh,
            slipballRadius,
            g5CenterX - self._slip * slipballMovementMax * slipballMovementWdith,
            slipballHeigh,
        )
        grad.setColorAt(0, QColor(255, 255, 255, 200))
        grad.setColorAt(1, QColor(160, 160, 160, 200))
        self.qp.setBrush(grad)

        self.qp.drawEllipse(
            QPoint(
                int(
                    g5CenterX - self._slip * slipballMovementMax * slipballMovementWdith
                ),
                int(slipballHeigh),
            ),
            slipballRadius,
            slipballRadius,
        )

        self.qp.end()

    def pitchLine(self, offset, length):
        """Return a pitch line.

        As the pitch line is drawn using translate and rotate
        align the pitch line around the center

        Args:
            angle: in degrees
            length: in pixel

        Returns:
            Qline
        """
        pass

    def alongRadiusCoord(self, angle, length):
        """Return a line along the radius of the circle.

        Args:
            angle: in degrees
            length: in pixel

        Returns:
            Qline
        """
        startPoint = QPoint(
            int(self.rollArcRadius * cos(radians(angle))),
            int(self.rollArcRadius * sin(radians(angle))),
        )
        endPoint = QPoint(
            int((self.rollArcRadius + length) * cos(radians(angle))),
            int((self.rollArcRadius + length) * sin(radians(angle))),
        )

        return QLine(startPoint, endPoint)
