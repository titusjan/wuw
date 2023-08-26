""" Version and other info for this program
"""
import sys

# We bypass the argparse mechanism in main.py because this import is executed before main.main()
DEBUGGING = ('-d' in sys.argv or '--debug' in sys.argv)
TESTING = True # add some test menu options
PROFILING = False# and DEBUGGING

VERSION = '0.1.0'
REPO_NAME = "wuw"
SCRIPT_NAME = "wuw"
PACKAGE_NAME = "wuw"
PROJECT_NAME = "Word under water"
SHORT_DESCRIPTION = "GUI to look at the structure of Word documents."
PROJECT_URL = "https://github.com/titusjan/wuw"
AUTHOR = "Pepijn Kenter"
EMAIL = "titusjan@gmail.com"
ORGANIZATION_NAME = "titusjan"
ORGANIZATION_DOMAIN = "titusjan.nl"

EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1
EXIT_CODE_COMMAND_ARGS = 2
EXIT_CODE_RESTART = 66 # Indicates the program is being 'restarted'

KEY_PROGRAM = '_program'
KEY_VERSION = '_version'



