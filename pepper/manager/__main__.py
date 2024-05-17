import argparse
import asyncio
import logging

from pepper.manager.config import DEFAULT_CONFIG_FILE
from pepper.manager.manager import Manager

parser = argparse.ArgumentParser("pepper-manager", description="Pepper Manager")
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
try:
    asyncio.run(m.run())
except KeyboardInterrupt:
    print("Exiting.")
