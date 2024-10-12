import argparse
import logging
import time
import traceback

import exceptiongroup
import trio

from .agent import Agent
from .config import load_agent_config


def main():
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

    backoff = 1
    q = False
    while not q:
        a = Agent(config=config)

        def stop(e):
            nonlocal q
            q = True

        def retry(e):
            nonlocal backoff
            traceback.print_exc()
            backoff = min(2 * backoff, 64)
            logging.error(f"Retrying in {backoff} seconds")
            time.sleep(backoff)

        # NOTE: change to except* when using Python 3.11
        with exceptiongroup.catch({KeyboardInterrupt: stop, Exception: retry}):
            trio.run(a.run)
            backoff = 1

    logging.info("Exiting")


if __name__ == "__main__":
    main()
