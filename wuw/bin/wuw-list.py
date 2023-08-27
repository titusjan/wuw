""" Lists the contents of a Word document.
"""
import argparse
import logging
import os.path
import sys
from io import BytesIO

from docx import Document
from wuw.be.info import VERSION

logger = logging.getLogger()

def read_document(file_name: str) -> Document:
    """ Opens the file read-only as a Python-docx document.

        It seems that you can't open a Word document on the OneDrive readonly if it is also opened
        in Word itself. When the document is saved only locally, you can.
    """
    logger.info(f"Opening {file_name}")
    assert os.path.exists(file_name), f"File does not exist: {file_name}"
    with open(file_name, 'rb') as file:
        source_stream = BytesIO(file.read())
    document = Document(source_stream)
    source_stream.close()
    return document


def list_structure(file_name:str) -> None:
    """ Lists the structure of a Word file.
    """
    document = read_document(file_name)
    for paragraph in document.paragraphs:
        print(repr(paragraph.text))




def main():
    # "D:\OneDrive - SPECTRAL Industries\Data\wuw_docs\simple.docx"
    aboutStr = "{} version: {}".format("argos_make_wrappers", VERSION)
    logger.info(aboutStr)

    parser = argparse.ArgumentParser(description = __doc__)

    parser.add_argument('-v', '--version', action = 'store_true',
        help="Prints the program version and exits")

    parser.add_argument(dest='file_name', metavar='FILE', nargs='?',
        help="""File that will be opened.""")

    args = parser.parse_args()

    if args.version:
        print(aboutStr)
        sys.exit(0)

    if args.file_name is None:
        print("Please give a file name as the command line argument.", file=sys.stderr)
        sys.exit(2)

    file_name = os.path.normpath(os.path.abspath(args.file_name))
    list_structure(file_name)



if __name__ == "__main__":
    LOG_FMT = '%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: %(message)s'
    logging.basicConfig(level='DEBUG', stream=sys.stderr, format=LOG_FMT)
    main()
