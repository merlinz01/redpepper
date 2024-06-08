import argparse
import logging

import exceptiongroup
import trio

from redpepper.agent.agent import Agent
from redpepper.agent.config import load_agent_config

parser = argparse.ArgumentParser("redpepper-agent", description="RedPepper Agent")
parser.add_argument("--config-file", default=None, help="Configuration file")
parser.add_argument(
    "-l",
    "--log-level",
    default="INFO",
    help="Logging level",
    choices=["TRACE", "DEBUG", "INFO", "WARN", "ERROR"],
)
parser.add_argument(
    "-c",
    "--config",
    help="Set config values",
    action="append",
    metavar="KEY=VALUE",
    default=[],
)
args = parser.parse_args()

format = "{levelname:<8} {name:<32} {message}"
if args.log_level == "DEBUG" or args.log_level == "TRACE":
    format = "{levelname:<8} {name:<32} {filename:<20} line {lineno:>3}  {message}"

logging.addLevelName(5, "TRACE")
logging.basicConfig(level=args.log_level, style="{", format=format)

config = load_agent_config(args.config_file)
for kv in args.config:
    key, value = kv.split("=", 1)
    config[key] = value
a = Agent(config=config)

# NOTE: change to except* when using Python 3.11
with exceptiongroup.catch({KeyboardInterrupt: lambda exc: None}):
    trio.run(a.run)
logging.info("Exiting")
