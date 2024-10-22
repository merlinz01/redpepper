import argparse
import logging
import time
import traceback

import trio

from .agent import Agent
from .config import DEFAULT_CONFIG_FILE, AgentConfig


def main():
    parser = argparse.ArgumentParser("redpepper-agent", description="RedPepper Agent")
    parser.add_argument(
        "--config-file", default=DEFAULT_CONFIG_FILE, help="Configuration file"
    )
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

    overrides = {}
    for kv in args.config:
        key, value = kv.split("=", 1)
        overrides[key] = value
    config = AgentConfig.from_file(args.config_file, overrides)

    backoff = 1
    q = False
    while not q:
        a = Agent(config=config)

        try:
            trio.run(a.run)
            backoff = 1
        except* KeyboardInterrupt:
            logging.info("Interrupted")
            q = True
        except* Exception:
            traceback.print_exc()
            backoff = min(2 * backoff, 64)
            logging.error(f"Retrying in {backoff} seconds")
            time.sleep(backoff)

    logging.info("Exiting")


if __name__ == "__main__":
    main()
