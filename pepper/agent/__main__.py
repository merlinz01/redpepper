import argparse
import asyncio
import logging

from pepper.agent.agent import Agent

parser = argparse.ArgumentParser("pepper-agent", description="Pepper Agent")
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
if args.log_level == "DEBUG":
    format = "{levelname:<8} {name:<32} {filename:<20} line {lineno:>3}  {message}"

logging.addLevelName(5, "TRACE")
logging.basicConfig(level=args.log_level, style="{", format=format)

a = Agent(config_file=args.config_file)
try:
    asyncio.run(a.run())
except KeyboardInterrupt:
    print("Exiting.")
    pass
