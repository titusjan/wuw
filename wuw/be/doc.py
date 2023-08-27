""" PyDocX related stuf.
"""
import logging
import os.path

from io import BytesIO

from docx import Document as createDocument
from docx.document import Document

logger = logging.getLogger(__name__)

def read_document(file_name: str) -> Document:
    """ Opens the file read-only as a Python-docx document.

        It seems that you can't open a Word document on the OneDrive readonly if it is also opened
        in Word itself. When the document is saved only locally, you can.
    """
    logger.info(f"Opening {file_name}")
    assert os.path.exists(file_name), f"File does not exist: {file_name}"
    with open(file_name, 'rb') as file:
        source_stream = BytesIO(file.read())
    document = createDocument(source_stream)
    source_stream.close()
    return document