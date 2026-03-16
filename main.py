"""
AI Document Organizer - Entry Point
Run with: python main.py [--watch] [--folder /path/to/folder]
"""

import argparse
import logging
from pathlib import Path

from organizer.scheduler import Scheduler
from organizer.scanner import Scanner
from organizer.database import Database
from organizer.utils import setup_logging, load_config

def parse_args():
    parser = argparse.ArgumentParser(
        description="🤖 AI Document Organizer - Automatically sort files using NLP & Computer Vision"
    )
    parser.add_argument(
        "--folder", "-f",
        type=str,
        default=None,
        help="Target folder to organize (overrides config.yaml)"
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Keep running and scan on schedule (uses interval from config.yaml)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Simulate organization without moving files"
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Clear the SQLite database before running"
    )
    return parser.parse_args()


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    args = parse_args()
    config = load_config()

    target_folder = Path(args.folder) if args.folder else Path(config["target_folder"])
    if not target_folder.exists():
        logger.error(f"Target folder does not exist: {target_folder}")
        raise SystemExit(1)

    db = Database(config["database"]["path"])
    if args.reset_db:
        db.reset()
        logger.info("Database reset.")

    scanner = Scanner(
        target_folder=target_folder,
        config=config,
        db=db,
        dry_run=args.dry_run,
    )

    if args.watch:
        scheduler = Scheduler(scanner=scanner, interval_minutes=config["schedule"]["interval_minutes"])
        logger.info(f"👁  Watching '{target_folder}' every {config['schedule']['interval_minutes']} minute(s). Press Ctrl+C to stop.")
        scheduler.run()
    else:
        logger.info(f"🔍 Running one-time scan on: {target_folder}")
        scanner.run()
        logger.info("✅ Done.")


if __name__ == "__main__":
    main()
