import argparse
import logging

import trio

from .config import load_manager_config
from .manager import Manager


def main():
    parser = argparse.ArgumentParser(
        "redpepper-manager", description="RedPepper Manager"
    )
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

    config = load_manager_config(args.config_file)
    for kv in args.config:
        key, value = kv.split("=", 1)
        config[key] = value
    m = Manager(config=config)

    try:
        trio.run(m.run)
    except* KeyboardInterrupt:
        logging.info("Interrupted")
    logging.info("Exiting")


if __name__ == "__main__":
    main()
