# Copyright 2016-2021 Spectral Industries
# This software is the proprietary information of Spectral Industries
# All rights Reserved

# This module was originally forked with permission from Argos.
# Pepijn Kenter (2023-06-05)

""" Defines ToggleColumnMixIn class
"""

import base64
import logging

from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup

from wuw.gui.misc import getWidgetState

logger = logging.getLogger(__name__)

# Qt classes have many ancestors
#pylint: disable=too-many-ancestors

# Don't want to create constructors for this mixin just to satisfy Pylint so
# we disable attribute-defined-outside-init (attribute-defined-outside-init)
#pylint: disable=attribute-defined-outside-init


class ToggleColumnMixIn(object):
    """ Adds actions to a QTableView that can show/hide columns
        by right clicking on the header.

        Has functionality for reading/writing from persitent settings.
    """

    def addHeaderContextMenu(self, checked = None, checkable = None, enabled = None):
        """ Adds the context menu from using header information

            checked can be a header_name -> boolean dictionary. If given, headers
            with the key name will get the checked value from the dictionary.
            The corresponding column will be hidden if checked is False.

            checkable can be a header_name -> boolean dictionary. If given, header actions
            with the key name will get the checkable value from the dictionary. (Default True)

            enabled can be a header_name -> boolean dictionary. If given, header actions
            with the key name will get the enabled value from the dictionary. (Default True)
        """
        logger.debug(f"Calling addHeaderContextMenu of {self}", stack_info=False)

        checked = checked if checked is not None else {}
        checkable = checkable if checkable is not None else {}
        enabled = enabled if enabled is not None else {}

        horizontal_header = self.horizontalHeader()
        horizontal_header.setContextMenuPolicy(Qt.ActionsContextMenu)

        assert not hasattr(self, "toggleColumnActionsGroup"), "Action group already defined."
        self.toggleColumnActionsGroup = QActionGroup(self)
        self.toggleColumnActionsGroup.setExclusive(False)
        #self.__toggle_functions = []  # for keeping references

        for col in range(horizontal_header.count()):
            column_label = self.model().headerData(col, Qt.Horizontal, Qt.DisplayRole)
            #logger.debug("Adding: col {}: {}".format(col, column_label))
            action = QAction(str(column_label),
                             self.toggleColumnActionsGroup,
                             checkable = checkable.get(column_label, True),
                             enabled = enabled.get(column_label, True),
                             toolTip = "Shows or hides the {} column".format(column_label))
            func = self.__makeShowColumnFunction(col)
            #self.__toggle_functions.append(func) # keep reference
            horizontal_header.addAction(action)
            is_checked = checked.get(column_label, not horizontal_header.isSectionHidden(col))
            logger.debug(f"    CHECKED  {column_label:15s}: {is_checked}")
            horizontal_header.setSectionHidden(col, not is_checked)
            action.setChecked(is_checked)
            action.toggled.connect(func)


    def __makeShowColumnFunction(self, column_idx):
        """ Creates a function that shows or hides a column."""
        show_column = lambda checked: self.setColumnHidden(column_idx, not checked)
        return show_column


    def showHeaderSection(self, sectionNr: int, show: bool) -> None:
        """ Shows/hides the column of the table with section number sectioNr
        """
        # Use actios so that the menu is updated as well.
        action = self.toggleColumnActionsGroup.actions()[sectionNr]
        action.setChecked(show)


    def getHeaderContextMenuActions(self):
        """ Returns the actions of the context menu of the header
        """
        return self.horizontalHeader().actions()


    def createTableHeadersMenu(self, menuTitle: str) -> QtWidgets.QMenu:
        """ Creates a submenu to show/hide table headers.

            Args:
                menuTitle: Menu title. If None, the panel title will be used.
        """
        menu = QtWidgets.QMenu(menuTitle, parent=self)
        for action in self.getHeaderContextMenuActions():
            menu.addAction(action)
        return menu


    def marshall(self) -> str:
        """ Returns an ascii string with the base64 encoded tree header state.
        """
        return base64.b64encode(getWidgetState(self.horizontalHeader())).decode('ascii')


    def unmarshall(self, dataStr: str) -> None:
        """ Initializes itself from a config dict form the persistent settings.
        """
        if dataStr is None:
            logger.debug("Tree headers state empty, so not restored: {}".format(self))
            return

        headerBytes = base64.b64decode(dataStr)
        horizontal_header = self.horizontalHeader()
        header_restored = horizontal_header.restoreState(headerBytes)
        if not header_restored:
            logger.warning("Tree headers state not restored: {}".format(self))

        # update actions so context menus are (un)checked properly
        for col, action in enumerate(horizontal_header.actions()):
            isChecked = not horizontal_header.isSectionHidden(col)
            action.setChecked(isChecked)


class ToggleColumnTableWidget(QtWidgets.QTableWidget, ToggleColumnMixIn):
    """ A QTableWidget where right clicking on the header allows the user to show/hide columns
    """
    pass



class ToggleColumnTableView(QtWidgets.QTableView, ToggleColumnMixIn):
    """ A QTableView where right clicking on the header allows the user to show/hide columns
    """
    pass



class ToggleColumnTreeWidget(QtWidgets.QTreeWidget, ToggleColumnMixIn):
    """ A QTreeWidget where right clicking on the header allows the user to show/hide columns
    """
    def horizontalHeader(self):
        """ Returns the horizontal header (of type QHeaderView).

            Override this if the horizontalHeader() function does not exist.
        """
        return self.header()



class ToggleColumnTreeView(QtWidgets.QTreeView, ToggleColumnMixIn):
    """ A QTreeView where right clicking on the header allows the user to show/hide columns
    """
    def horizontalHeader(self):
        """ Returns the horizontal header (of type QHeaderView).

            Override this if the horizontalHeader() function does not exist.
        """
        return self.header()


#pylint: enable=too-many-ancestors


