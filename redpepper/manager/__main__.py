import argparse
import logging

import exceptiongroup
import trio

from redpepper.manager.apiserver import APIServer
from redpepper.manager.config import DEFAULT_CONFIG_FILE
from redpepper.manager.manager import Manager

parser = argparse.ArgumentParser("redpepper-manager", description="RedPepper Manager")
parser.add_argument("--config-file", default=None, help="Configuration file")
parser.add_argument(
    "--log-level",
    "-l",
    default="INFO",
    help="Logging level",
    choices=["TRACE", "DEBUG", "INFO", "WARN", "ERROR"],
)
args = parser.parse_args()

format = "{levelname:<8} {name:<32} {message}"
if args.log_level == "DEBUG" or args.log_level == "TRACE":
    format = "{levelname:<8} {name:<32} {filename:<20} line {lineno:>3}  {message}"

logging.addLevelName(5, "TRACE")
logging.basicConfig(level=args.log_level, style="{", format=format)

m = Manager(config_file=args.config_file)

# NOTE: change to except* when using Python 3.11
with exceptiongroup.catch({KeyboardInterrupt: lambda exc: None}):
    trio.run(m.run)
logging.info("Exiting")