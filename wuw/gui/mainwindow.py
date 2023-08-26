""" Main window functionality
"""

import base64
import cProfile
import logging
import os.path
import pstats
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtGui import QAction

from wuw.be.info import DEBUGGING, PROJECT_NAME, VERSION
from wuw.gui.misc import getWidgetGeom, getWidgetState
from wuw.utils.dirs import appLogDirectory
from wuw.utils.misc import stringToIdentifier

logger = logging.getLogger(__name__)

# The main window inherits from a Qt class, therefore it has many
# ancestors public methods and attributes.
# pylint: disable=too-many-ancestors, too-many-instance-attributes, too-many-public-methods, attribute-defined-outside-init


class MainWindow(QtWidgets.QMainWindow):
    """ Main application window.
    """
    __numInstances = 0

    def __init__(self, argosApplication):
        """ Constructor
            :param reset: If true the persistent settings, such as column widths, are reset.
        """
        super(MainWindow, self).__init__()
        self._windowNumber = MainWindow.__numInstances # Used only for debugging
        MainWindow.__numInstances += 1

        self._argosApplication = argosApplication

        self.setDockNestingEnabled(False)

        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.TopDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.BottomDockWidgetArea)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setUnifiedTitleAndToolBarOnMac(True)
        #self.setDocumentMode(True) # Look of tabs as Safari on OS-X (disabled, ugly)
        self.resize(1300, 700)  # Assumes minimal resolution of 1366 x 768

        # Move window to the center of the screen
        desktopRect = QtWidgets.QApplication.primaryScreen().availableGeometry()
        center = desktopRect.center()
        self.move(round(center.x() - self.width () * 0.5), round(center.y() - self.height() * 0.5))

        self.__setupActions()
        self.__setupMenus()
        self.__setupViews()
        self.__setupDockWidgets()
        self.updateWindowTitle()


    def finalize(self):
        """ Is called before destruction (when closing).
            Can be used to clean-up resources.
        """
        logger.debug("Finalizing: {}".format(self))


    def __setupViews(self):
        """ Creates the UI widgets.
        """
        self.mainWidget = QtWidgets.QWidget()
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setCentralWidget(self.mainWidget)


    def __addTableHeadersSubMenu(self, menuTitle, treeView):
        """ Adds a sub menu to the View | Table Headers menu with actions to show/hide columns
        """
        subMenu = self.tableHeadersMenu.addMenu(menuTitle)
        for action in treeView.getHeaderContextMenuActions():
            subMenu.addAction(action)


    def __setupActions(self):
        """ Creates actions that are always usable, even if they are not added to the main menu.

            Some actions are only added to the menu in debugging mode.
        """
        # The action added to the menu in the repopulateWindowMenu method, which is called by
        # the ArgosApplication object every time a window is added or removed.
        self.activateWindowAction = QAction("Window #{}".format(self.windowNumber), self)
        self.activateWindowAction.triggered.connect(self.activateAndRaise)
        self.activateWindowAction.setCheckable(True)
        #self.addAction(self.activateWindowAction)

        if self.windowNumber <= 9:
            self.activateWindowAction.setShortcut(QtGui.QKeySequence(
                "Alt+{}".format(self.windowNumber)))

        self.myTestAction = QAction("My Test", self)
        self.myTestAction.setToolTip("Ad-hoc test procedure for debugging.")
        self.myTestAction.setShortcut("Meta+T")
        self.myTestAction.triggered.connect(self.myTest)
        self.addAction(self.myTestAction)


    def __setupMenus(self):
        """ Sets up the main menu.
        """
        # Don't use self.menuBar(), on OS-X this is not shared across windows.
        # See: http://qt-project.org/doc/qt-4.8/qmenubar.html#details
        # And:http://qt-project.org/doc/qt-4.8/qmainwindow.html#menuBar
        menuBar = QtWidgets.QMenuBar() # Make a menu without parent.
        self.setMenuBar(menuBar)

        ### File Menu ###

        fileMenu = menuBar.addMenu("&File")
        fileMenu.addAction("Close &Window", self.close, QtGui.QKeySequence.Close)

        fileMenu.addSeparator()

        self.openRecentMenu = fileMenu.addMenu("Open Recent")
        self.openRecentMenu.aboutToShow.connect(self._repopulateOpenRecentMenu)

        fileMenu.addSeparator()

        fileMenu.addSeparator()
        fileMenu.addAction("E&xit", self.argosApplication.quit, 'Ctrl+Q')

        ### View Menu ###

        self.viewMenu = menuBar.addMenu("&View")

        self.viewMenu.addSeparator()
        self.panelsMenu = self.viewMenu.addMenu("&Panels")
        self.tableHeadersMenu = self.viewMenu.addMenu("&Table Headers")

        self.viewMenu.addSeparator()

        ### Window Menu ###

        # Will be populated in repopulateWindowMenu
        self.windowMenu = menuBar.addMenu("&Window")

        ### Help Menu ###
        menuBar.addSeparator()
        helpMenu = menuBar.addMenu("&Help")

        helpMenu.addSeparator()

        helpMenu.addAction(
            "Show Log Files...",
            lambda: self.openInExternalApp(appLogDirectory()))

        helpMenu.addAction('&About...', self.about)

        if DEBUGGING:
            helpMenu.addSeparator()
            helpMenu.addAction(self.myTestAction)


    def __setupDockWidgets(self):
        """ Sets up the dock widgets. Must be called after the menu is setup.
        """
        pass


    ##############
    # Properties #
    ##############

    @property
    def windowNumber(self):
        """ The instance number of this window.
        """
        return self._windowNumber

    @property
    def argosApplication(self):
        """ The ArgosApplication to which this window belongs.
        """
        return self._argosApplication

    ###########
    # Methods #
    ###########

    def _repopulateOpenRecentMenu(self, *args, **kwargs):
        """ Clear the window menu and fills it with the actions of the actionGroup
        """
        pass


    def repopulateWindowMenu(self, actionGroup):
        """ Clear the window menu and fills it with the actions of the actionGroup
        """
        for action in self.windowMenu.actions():
            self.windowMenu.removeAction(action)

        for action in actionGroup.actions():
            self.windowMenu.addAction(action)


    def dockWidget(self, widget, title, area):
        """ Adds a widget as a docked widget.
            Returns the added dockWidget
        """
        assert widget.parent() is None, "Widget already has a parent"

        dockWidget = QtWidgets.QDockWidget(title, parent=self)
        # Use dock2 as name to reset at upgrade
        dockWidget.setObjectName("dock2_" + stringToIdentifier(title)) # Use doc
        dockWidget.setWidget(widget)
        self.addDockWidget(area, dockWidget)

        self.panelsMenu.addAction(dockWidget.toggleViewAction())
        return dockWidget


    def updateWindowTitle(self):
        """ Updates the window title frm the window number, inspector, etc
            Also updates the Window Menu
        """
        title = "{} #{}".format(PROJECT_NAME, self.windowNumber)

        # Display settings file name in title bar if it's not the default
        settingsFile = os.path.basename(self.argosApplication.settingsFile)
        if settingsFile != 'settings.json':
            title = "{} -- {}".format(title, settingsFile)

        self.setWindowTitle(title)
       
        self.activateWindowAction.setText("{} window".format('???'))


    def openInWebBrowser(self, url):
        """ Opens url or file in an external documentation.

            Regular URLs are opened in the web browser, Local URLs are opened in the application
            that is used to open that type of file by default.
        """
        try:
            logger.debug("Opening URL: {}".format(url))
            qUrl = QUrl(url)
            QtGui.QDesktopServices.openUrl(qUrl)
        except Exception as ex:
            msg = "Unable to open URL {}. \n\nDetails: {}".format(url, ex)
            QtWidgets.QMessageBox.warning(self, "Warning", msg)
            logger.error(msg.replace('\n', ' '))


    def openInExternalApp(self, fileName):
        """ Opens url or file in an external documentation.

            Regular URLs are opened in the web browser, Local URLs are opened in the application
            that is used to open that type of file by default.
        """
        try:
            logger.debug("Opening URL: {}".format(fileName))
            if not os.path.exists(fileName):
                raise OSError("File doesn't exist.")
            url = QUrl.fromLocalFile(fileName)
            QtGui.QDesktopServices.openUrl(url)
        except Exception as ex:
            msg = "Unable to open file '{}'. \n\nDetails: {}".format(fileName, ex)
            QtWidgets.QMessageBox.warning(self, "Warning", msg)
            logger.error(msg.strip('\n'))


    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        layoutCfg = dict(
            winGeom = base64.b64encode(getWidgetGeom(self)).decode('ascii'),
            winState = base64.b64encode(getWidgetState(self)).decode('ascii'),
        )

        cfg = dict(
            layout = layoutCfg,
        )
        return cfg


    def unmarshall(self, cfg):
        """ Initializes itself from a config dict form the persistent settings.
        """
        layoutCfg = cfg.get('layout', {})

        if 'winGeom' in layoutCfg:
            self.restoreGeometry(base64.b64decode(layoutCfg['winGeom']))
        if 'winState' in layoutCfg:
            self.restoreState(base64.b64decode(layoutCfg['winState']))


    @Slot()
    def activateAndRaise(self):
        """ Activates and raises the window.
        """
        logger.debug("Activate and raising window: {}".format(self.windowNumber))
        self.activateWindow()
        self.raise_()


    def event(self, ev):
        """ Detects the WindowActivate event. Pass all event through to the super class.
        """
        if ev.type() == QtCore.QEvent.WindowActivate:
            logger.debug("Window activated: {}".format(self.windowNumber))
            self.activateWindowAction.setChecked(True)

        return super(MainWindow, self).event(ev);


    def closeEvent(self, event):
        """ Called when closing this window.
        """
        logger.debug("closeEvent")

        # Save settings must be called here, at the point that there is still a windows open.
        # We can't use the QApplication.aboutToQuit signal because at that point the windows have
        # been closed
        self.argosApplication.saveSettingsIfLastWindow()
        self.finalize()
        self.argosApplication.removeMainWindow(self)
        event.accept()
        logger.debug("closeEvent accepted")


    @Slot()
    def about(self):
        """ Shows the about message window.
        """
        QtWidgets.QMessageBox.about(self, "About {}".format(PROJECT_NAME),
                                    f"{PROJECT_NAME} version: {VERSION}")


    @Slot()
    def myTest(self):
        """ Function for small ad-hoc tests that can be called from the menu.
        """
        logger.info("--------- myTest function called --------------------")


