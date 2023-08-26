""" Miscellaneous Qt routines.
"""
import os.path
import logging
import sys
import traceback

from PySide6 import QtCore, QtWidgets

from wuw.be.info import DEBUGGING

logger = logging.getLogger(__name__)



def processEvents():
    """ Processes all pending events for the calling thread until there are no more events to
        process.
    """
    QtWidgets.QApplication.instance().processEvents()


def safeSetApplicationQtStyle(styleName):
    """ Sets the Qt style (e.g. to 'fusion')

        Does nothing is the styleName is None
        Logs a warning if the style does not exist.
    """
    if styleName:
        availableStyles = QtWidgets.QStyleFactory.keys()
        if  styleName not in availableStyles:
            logger.warning("Qt style '{}' is not available on this computer. Use one of: {}"
                           .format(styleName, availableStyles))
        else:
            setApplicationQtStyle(styleName)


def setApplicationQtStyle(styleName):
    """ Sets the Qt style (e.g. to 'fusion')
    """
    qApp = QtWidgets.QApplication.instance()
    logger.debug("Setting Qt style to: {}".format(styleName))
    qApp.setStyle(QtWidgets.QStyleFactory.create(styleName))
    if qApp.style().objectName().lower() != styleName.lower():
        logger.warning(
            "Setting style failed: actual style {!r} is not the specified style {!r}"
            .format(qApp.style().objectName(), styleName))


def safeSetApplicationStyleSheet(fileName):
    """ Reads the style sheet from file and set it as application style sheet.

        Logs warning if the style sheet does not exist.
    """
    if not os.path.exists(fileName):
        msg = "Stylesheet not found: {}".format(fileName)
        print(msg, file=sys.stderr)
        logger.warning(msg)
    else:
        setApplicationStyleSheet(fileName)

def setApplicationStyleSheet(fileName):

    fileName = os.path.abspath(fileName)
    logger.debug("Reading qss from: {}".format(fileName))
    try:
        with open(fileName) as input:
            qss = input.read()
    except Exception as ex:
        logger.warning("Unable to read style sheet from '{}'. Reason: {}".format(fileName, ex))
        return

    QtWidgets.QApplication.instance().setStyleSheet(qss)


######################
# Exception Handling #
######################

class ResizeDetailsMessageBox(QtWidgets.QMessageBox):
    """ Message box that enlarges when the 'Show Details' button is clicked.
        Can be used to better view stack traces. I could't find how to make a resizeable message
        box but this it the next best thing.

        Taken from:
        http://stackoverflow.com/questions/2655354/how-to-allow-resizing-of-qmessagebox-in-pyqt4
    """
    def __init__(self, detailsBoxWidth=700, detailBoxHeight=300, *args, **kwargs):
        """ Constructor
            :param detailsBoxWidht: The width of the details text box (default=700)
            :param detailBoxHeight: The heights of the details text box (default=700)
        """
        super(ResizeDetailsMessageBox, self).__init__(*args, **kwargs)
        self.detailsBoxWidth = detailsBoxWidth
        self.detailBoxHeight = detailBoxHeight


    def resizeEvent(self, event):
        """ Resizes the details box if present (i.e. when 'Show Details' button was clicked)
        """
        result = super(ResizeDetailsMessageBox, self).resizeEvent(event)

        details_box = self.findChild(QtWidgets.QTextEdit)
        if details_box is not None:
            #details_box.setFixedSize(details_box.sizeHint())
            details_box.setFixedSize(QtCore.QSize(self.detailsBoxWidth, self.detailBoxHeight))

        return result



def handleException(exc_type, exc_value, exc_traceback):

    traceback.format_exception(exc_type, exc_value, exc_traceback)

    logger.critical("Bug: uncaught {}".format(exc_type.__name__),
                    exc_info=(exc_type, exc_value, exc_traceback))
    if DEBUGGING:
        logger.info("Quitting application with exit code 1")
        sys.exit(1)
    else:
        # Constructing a QApplication in case this hasn't been done yet.
        if not QtWidgets.QApplication.instance():
            _app = QtWidgets.QApplication()

        msgBox = ResizeDetailsMessageBox()
        msgBox.setText("Bug: uncaught {}".format(exc_type.__name__))
        msgBox.setInformativeText(str(exc_value))
        lst = traceback.format_exception(exc_type, exc_value, exc_traceback)
        msgBox.setDetailedText("".join(lst))
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.exec_()
        logger.info("Quitting application with exit code 1")
        sys.exit(1)



######################
# QSettings routines #
######################


def getWidgetGeom(widget):
    """ Gets the QWindow or QWidget geometry as a QByteArray.

        Since Qt does not provide this directly we hack this by saving it to the QSettings
        in a temporary location and then reading it from the QSettings.

        :param widget: A QWidget that has a saveGeometry() methods
    """
    settings = QtCore.QSettings()
    settings.beginGroup('temp_conversion')
    try:
        settings.setValue("winGeom", widget.saveGeometry())
        return bytes(settings.value("winGeom"))
    finally:
        settings.endGroup()


def getWidgetState(qWindow):
    """ Gets the QWindow or QWidget state as a QByteArray.

        Since Qt does not provide this directly we hack this by saving it to the QSettings
        in a temporary location and then reading it from the QSettings.

        :param widget: A QWidget that has a saveState() methods
    """
    settings = QtCore.QSettings()
    settings.beginGroup('temp_conversion')
    try:
        settings.setValue("winState", qWindow.saveState())
        return bytes(settings.value("winState"))
    finally:
        settings.endGroup()


def setWidgetSizePolicy(widget, hor=None, ver=None):
    """ Sets horizontal and/or vertical size policy on a widget
    """
    sizePolicy = widget.sizePolicy()
    logger.debug("widget {} size policy Befor: {} {}"
                 .format(widget, sizePolicy.horizontalPolicy(), sizePolicy.verticalPolicy()))

    if hor is not None:
        sizePolicy.setHorizontalPolicy(hor)

    if ver is not None:
        sizePolicy.setVerticalPolicy(ver)

    widget.setSizePolicy(sizePolicy)

    sizePolicy = widget.sizePolicy()
    logger.debug("widget {} size policy AFTER: {} {}"
                 .format(widget, sizePolicy.horizontalPolicy(), sizePolicy.verticalPolicy()))

