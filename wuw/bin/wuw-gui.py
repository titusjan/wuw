""" Starts graphical user inteface that displayed the structure of a Word document.
"""
import argparse
import logging
import os.path
import sys

from wuw.be.doc import read_document
from wuw.be.info import PROJECT_NAME, VERSION
from wuw.gui.mainapp import MainApp, qApplicationSingleton
from wuw.gui.misc import safeSetApplicationStyleSheet, safeSetApplicationQtStyle
from wuw.utils.dirs import resource_directory

logger = logging.getLogger()


def browse_structure(file_name:str) -> None:
    """ Uses the object browser to brawse the document.
    """
    from objbrowser import browse
    document = read_document(file_name)
    browse({'document': document})


def startGui(args: argparse.Namespace):
    """ Creates the main app and start the Qt GUI
    """
    file_name = os.path.normpath(os.path.abspath(args.file_name))

    # Apparently, in Qt6 you need to create the QApplication before you can create a widget.
    qApp = qApplicationSingleton()

    qtStyle = args.qtStyle if args.qtStyle else os.environ.get("QT_STYLE_OVERRIDE", 'Fusion')
    styleSheet = args.styleSheet if args.styleSheet else os.environ.get("WUW_STYLE_SHEET", '')

    if not styleSheet:
        styleSheet = os.path.join(resource_directory(), "app.css")
        logger.debug("Using default style sheet: {}".format(styleSheet))
    else:
        styleSheet = os.path.abspath(styleSheet)

    mainApp = MainApp(settingsFile=None)
    mainApp.loadSettings()

    safeSetApplicationQtStyle(qtStyle)
    safeSetApplicationStyleSheet(styleSheet)

    logger.debug("Starting mainApp")
    exitCode = mainApp.execute()
    logger.info(f"{PROJECT_NAME} finished with exit code: {exitCode}")
    sys.exit(exitCode)


def main():
    """ Main entry point
    """
    # "D:\OneDrive - SPECTRAL Industries\Data\wuw_docs\simple.docx"
    aboutStr = "{} version: {}".format("argos_make_wrappers", VERSION)
    logger.info(aboutStr)

    parser = argparse.ArgumentParser(description = __doc__)

    parser.add_argument('-v', '--version', action = 'store_true',
        help="Prints the program version and exits")

    parser.add_argument(dest='file_name', metavar='FILE', nargs='?',
        help="""File that will be opened.""")

    parser.add_argument('-b', '--browse', action = 'store_true',
        help="Uses Object Browser to browse the word document."
             "See https://github.com/titusjan/objbrowser.")

    cfgGroup = parser.add_argument_group(
        "config options", description="Options related to style and configuration.")

    cfgGroup.add_argument('--qt-style', dest='qtStyle', help='Qt style. E.g.: fusion')

    cfgGroup.add_argument('--qss', dest='styleSheet',
                        help="Name of Qt Style Sheet file. If not set, the Argos default style "
                             "sheet will be used.")

    devGroup = parser.add_argument_group(
        "developer options", description="Options that are mainly useful for the app developers.")

    devGroup.add_argument('-d', '--debugging-mode', dest='debugging', action = 'store_true',
        help="Run Argos in debugging mode. Useful during development.")



    args = parser.parse_args()

    if args.version:
        print(aboutStr)
        sys.exit(0)

    if args.file_name is None:
        print("Please give a file name as the command line argument.", file=sys.stderr)
        sys.exit(2)


    if args.browse:
        file_name = os.path.normpath(os.path.abspath(args.file_name))
        browse_structure(file_name)
        sys.exit(0)

    startGui(args)



if __name__ == "__main__":
    LOG_FMT = '%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: %(message)s'
    logging.basicConfig(level='DEBUG', stream=sys.stderr, format=LOG_FMT)
    main()
