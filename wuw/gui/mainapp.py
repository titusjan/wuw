""" Version and other info for this program
"""
import json
import logging
import os.path
import pprint
import shutil
import sys


from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Slot, QtMsgType

import wuw.be.info as info

from wuw.be.info import DEBUGGING, EXIT_CODE_SUCCESS, KEY_PROGRAM, PROJECT_NAME, VERSION, KEY_VERSION
from wuw.gui.mainwindow import MainWindow

from wuw.utils.dirs import normRealPath, ensureFileExists, appConfigDirectory


from wuw.gui.misc import handleException

logger = logging.getLogger(__name__)



_Q_APP = None # Keep reference to QApplication instance to prevent garbage collection

def qApplicationSingleton():
    """ Returns the QApplication object. Creates it if it doesn't exist.

        :rtype QtWidgets.QApplication:
    """
    global _Q_APP

    qApp = QtWidgets.QApplication.instance()
    if qApp is None:
        logger.debug("Creating the QApplication")
        _Q_APP = qApp = QtWidgets.QApplication([])

        qApp.setApplicationName(info.REPO_NAME)
        qApp.setApplicationVersion(info.VERSION)
        qApp.setOrganizationName(info.ORGANIZATION_NAME)
        qApp.setOrganizationDomain(info.ORGANIZATION_DOMAIN)

    return qApp



class MainApp(QtCore.QObject):
    """ The application singleton which holds global state.
    """
    def __init__(self, settingsFile=None, setExceptHook=True):
        """ Constructor
            
            Args:
                settingsFile: Config file from which the persistent settings are loaded.

                setExceptHook: Sets the global sys.except hook so that Qt shows a dialog box
                    when an exception is raised.
        """
        super().__init__()

        if not settingsFile:
            settingsFile = MainApp.defaultSettingsFile()
            logger.debug("No config file specified. Using default: {}".format(settingsFile))

        self._settingsFile = MainApp.userConfirmedSettingsFile(
            settingsFile, createWithoutConfirm=MainApp.defaultSettingsFile())

        if setExceptHook:
            logger.debug("Setting sys.excepthook to app-specific exception handling")
            sys.excepthook = handleException

        QtCore.qInstallMessageHandler(self.handleQtLogMessages)

        self._mainWindows = []
        self._settingsSaved = False  # boolean to prevent saving settings twice
        self._recentFiles = []    # list of recently opened files ([timeStampe, fileName] per file).
        self._maxRecentFiles = 10  # Maximum size of recent file

        #self.qApplication.aboutToQuit.connect(self.aboutToQuitHandler)

        # Activate-actions for all windows
        self.windowActionGroup = QtGui.QActionGroup(self)
        self.windowActionGroup.setExclusive(True)

        # Call setup when the event loop starts.
        QtCore.QTimer.singleShot(0, self.onEventLoopStarted)

        logger.debug("MainApp.__init__ finished")


    def onEventLoopStarted(self):
        """ Is called as soon as the event loop has started.
        """
        logger.debug("MainApp.onEventLoopStarted called")

        # Raising all window because in OS-X window 0 is not shown.
        #self.raiseAllWindows()
        # activateWindow also solves the issue but doesn't work with the --inspector option.
        actions = self.windowActionGroup.actions()
        if actions:
            actions[0].trigger()


    @classmethod
    def defaultSettingsFile(cls):
        """ Returns the path to the default settings file
        """
        return normRealPath(os.path.join(appConfigDirectory(), 'settings.json'))


    @classmethod
    def userConfirmedSettingsFile(cls, settingsFile, createWithoutConfirm=None):
        """ Asks the user to confirm creating the settings file if it does not exist and is not
            in the createWithoutConfirm list.

            If settingsFile is a relative path it will be concatenated to the app config dir.

            Returns: The path of the setting file.
        """
        settingsFile = os.path.join(appConfigDirectory(), settingsFile)
        logger.debug("Testing if settings file exists: {}".format(settingsFile))
        if os.path.exists(settingsFile):
            return settingsFile
        else:
            if settingsFile in createWithoutConfirm:
                return ensureFileExists(settingsFile)
            else:
                _app = qApplicationSingleton() # make sure QApplication exists.
                button = QtWidgets.QMessageBox.question(
                    None, "Create settings file?",
                    "The setting file cannot be found: {} \n\nCreate new config file?"
                                                        .format(settingsFile))

                if button == QtWidgets.QMessageBox.Yes:
                    return ensureFileExists(settingsFile)
                else:
                    logger.warning("No settings file created. App won't save persistent settings.")
                    return None


    ##############
    # Properties #
    ##############

    @property
    def qApplication(self):
        """ Returns the QApplication object. Equivalent to QtWidgets.qApp.
        """
        return qApplicationSingleton()


    @property
    def mainWindows(self):
        """ Returns the list of MainWindows. For read-only purposes only.
        """
        return self._mainWindows


    @property
    def settingsFile(self):
        """ Returns the name of the settings file
        """
        return self._settingsFile


    ###########
    # Methods #
    ###########


    @classmethod
    def handleQtLogMessages(cls, qMsgType, context, msg):
        """ Forwards Qt log messages to the python log system.

            This ensures that they end up in application log files instead of just being printed to
            stderr at application exit.

            This function must be installed with QtCore.qInstallMessageHandler.
            See https://doc.qt.io/qt-5/qtglobal.html#qInstallMessageHandler
        """
        # Still print the message to stderr, just like Qt does by default.
        print(msg, file=sys.stderr, flush=True)

        if qMsgType == QtMsgType.QtDebugMsg:
            logger.debug(msg)
        elif qMsgType == QtMsgType.QtInfoMsg:
            logger.info(msg)
        elif qMsgType == QtMsgType.QtWarningMsg:
            logger.warning(msg)
        elif qMsgType == QtMsgType.QtCriticalMsg:
            logger.error(msg)
        elif qMsgType == QtMsgType.QtFatalMsg:
            logger.error(msg)
        else:
            logger.critical("Qt message of unknown type {}: {}".format(qMsgType, msg))


    def _makeConfigBackup(self, cfg):
        """ Creates a backup of the config file if the application version is not the same
            as the version from the config file.
        """
        if not cfg: # The config may be empty, e.g. when the first time the application is started
            return cfg

        cfgVersion = cfg.get(KEY_VERSION, '0.0.1')

        if cfgVersion != VERSION:
            logger.info("Config file version {} differs from application version {}."
                        .format(cfgVersion, VERSION))

            cfgBackup = "{}.v{}.backup".format(self._settingsFile, cfgVersion)
            logger.info("Making a backup to: {}".format(os.path.abspath(cfgBackup)))
            shutil.copy2(self._settingsFile, cfgBackup)

        return cfg


    def marshall(self):
        """ Returns a dictionary to save in the persistent settings
        """
        cfg = {}

        cfg[KEY_PROGRAM] = PROJECT_NAME
        cfg[KEY_VERSION] = VERSION

        cfg['recent_files'] = self._recentFiles

        # Save windows as a dict instead of a list to improve readability of the resulting JSON
        cfg['windows'] = {}
        for winNr, mainWindow in enumerate(self.mainWindows):
            key = "win-{:d}".format(winNr)
            cfg['windows'][key] = mainWindow.marshall()

        return cfg


    def unmarshall(self, cfg):
        """ Initializes itself from a config dict form the persistent settings.
        """
        self._recentFiles = cfg.get('recent_files', [])

        for winId, winCfg in cfg.get('windows', {}).items():
            assert winId.startswith('win-'), "Win ID doesn't start with 'win-': {}".format(winId)
            self.addNewMainWindow(cfg=winCfg)

        if len(self.mainWindows) == 0:
            logger.info("No open windows in settings or command line (creating one).")
            self.addNewMainWindow()


    def saveSettings(self):
        """ Saves the persistent settings to file.
        """
        try:
            if not self._settingsFile:
                logger.info("No settings file specified. Not saving persistent state.")
            else:
                logger.info("Saving settings to: {}".format(self._settingsFile))
                settings = self.marshall()
                try:
                    jsonStr = json.dumps(settings, sort_keys=True, indent=4)
                except Exception as ex:
                    logger.error("Failed to serialize settings to JSON: {}".format(ex))
                    logger.error("Settings: ...\n" + pprint.pformat(settings, width=100))
                    raise
                else:
                    with open(self._settingsFile, 'w') as settingsFile:
                        settingsFile.write(jsonStr)

        except Exception as ex:
            # Continue, even if saving the settings fails.
            logger.exception(ex)
            if DEBUGGING:
                raise
        finally:
            self._settingsSaved = True


    def loadSettings(self):
        """ Loads the settings from file and populates the application object from it.

            Will update the config (and make a backup of the config file) if the version number
            has changed.
        """
        if not os.path.exists(self._settingsFile):
            logger.warning("Settings file does not exist: {}".format(self._settingsFile))

        try:
            with open(self._settingsFile, 'r') as settingsFile:
                jsonStr = settingsFile.read()

            if jsonStr:
                cfg = json.loads(jsonStr)
            else:
                cfg = {}
        except Exception as ex:
            logger.error("Error {} while reading settings file: {}"
                           .format(ex, self._settingsFile))
            raise # in case of a syntax error it's probably best to exit.

        self._makeConfigBackup(cfg)  # If the version has changed.
        #cfg = _updateConfig(cfg)     # If the version has changed.

        self.unmarshall(cfg)  # Always call unmarshall.


    def saveSettingsIfLastWindow(self):
        """ Writes the persistent settings if this is the last window and the settings have not yet
            been saved.
        """
        if not self._settingsSaved and len(self.mainWindows) <= 1:
            self.saveSettings()


    def repopulateAllWindowMenus(self):
        """ Repopulates the Window menu of all main windows from scratch.

            To be called when a main window is created or removed.
        """
        for win in self.mainWindows:
            win.repopulateWindowMenu(self.windowActionGroup)


    @Slot()
    def addNewMainWindow(self, cfg=None, inspectorFullName=None):
        """ Creates and shows a new MainWindow.

            If inspectorFullName is set, it will set the identifier from that name.
            If the inspector identifier is not found in the registry, a KeyError is raised.
        """
        mainWindow = MainWindow(self)
        self.mainWindows.append(mainWindow)

        self.windowActionGroup.addAction(mainWindow.activateWindowAction)
        self.repopulateAllWindowMenus()

        if cfg:
            mainWindow.unmarshall(cfg)

        mainWindow.show()

        if sys.platform.startswith('darwin'):
            mainWindow.raise_()

        return mainWindow


    def removeMainWindow(self, mainWindow):
        """ Removes the mainWindow from the list of windows. Saves the settings
        """
        logger.debug("removeMainWindow called")

        self.windowActionGroup.removeAction(mainWindow.activateWindowAction)
        self.repopulateAllWindowMenus()

        self.mainWindows.remove(mainWindow)


    def raiseAllWindows(self):
        """ Raises all application windows.
        """
        logger.debug("raiseAllWindows called")
        for mainWindow in self.mainWindows:
            logger.debug("Raising {}".format(mainWindow._instanceNr))
            mainWindow.raise_()


    def exit(self, exitCode):
        """ Saves settings and exits the program with a certain exit code.
        """
        self.saveSettings()
        self.qApplication.closeAllWindows()
        self.qApplication.exit(exitCode)


    def quit(self):
        """ Saves settings and exits the program with exit code 0 (success).
        """
        self.exit(EXIT_CODE_SUCCESS)


    def execute(self):
        """ Executes all main windows by starting the Qt main application
        """
        logger.info("Starting the event loop...")
        exitCode = self.qApplication.exec_()
        logger.info("Event loop finished with exit code: {}".format(exitCode))
        return exitCode

