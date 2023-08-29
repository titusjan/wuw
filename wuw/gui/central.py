""" The central widget in the main window
"""

from PySide6 import QtWidgets


from docx.document import Document

from wuw.gui.tables import DocumentTableViewer, DocumentTableModel


class CentralWidget(QtWidgets.QWidget):

    def __init__(self, document: Document=None, parent=None):

        super().__init__(parent=parent)

        self.tableModel = DocumentTableModel(document=document)

        self.mainLayout = QtWidgets.QVBoxLayout()
        #self.mainLayout.setContentsMargins(0, 0, 0, 0)
        #self.mainLayout.setSpacing(0)
        self.setLayout(self.mainLayout)

        self.tableViewer = DocumentTableViewer(model=self.tableModel)
        self.mainLayout.addWidget(self.tableViewer)


    def finalize(self):
        """ Clean up resources.
        """
        self.tableModel.finalize()


    def setDocument(self, document: Document) -> None:
        self.tableModel.document = document

