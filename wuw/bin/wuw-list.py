""" Lists the contents of a Word document.
"""
import argparse
import logging
import os.path
import sys

logger = logging.getLogger()

VERSION = '0.0.1dev'

def list_structure(file_name:str) -> None:
    """ Lists the structure of a Word file.
    """
    logger.info(f"Opening {file_name}")

def main():

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
    else:
        list_structure(os.path.normpath(os.path.abspath(args.file_name)))



if __name__ == "__main__":
    LOG_FMT = '%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: %(message)s'
    logging.basicConfig(level='DEBUG', stream=sys.stderr, format=LOG_FMT)
    main()
