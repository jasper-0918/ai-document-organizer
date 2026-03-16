"""
Scheduler
=========
Wraps the `schedule` library to run periodic folder scans.
Runs the first scan immediately on start, then every N minutes.
"""

import logging
import signal
import time

import schedule

from organizer.scanner import Scanner

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, scanner: Scanner, interval_minutes: int = 5):
        self.scanner = scanner
        self.interval_minutes = max(1, interval_minutes)
        self._running = False

    def _job(self):
        logger.info(f"⏰ Scheduled scan triggered.")
        try:
            self.scanner.run()
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)

    def run(self):
        """Start the scheduler loop. Blocks until Ctrl+C."""
        self._running = True

        # Graceful shutdown on SIGINT / SIGTERM
        def _handle_stop(sig, frame):
            logger.info("Stop signal received — shutting down scheduler.")
            self._running = False

        signal.signal(signal.SIGINT, _handle_stop)
        signal.signal(signal.SIGTERM, _handle_stop)

        # Run immediately, then on the schedule
        self._job()
        schedule.every(self.interval_minutes).minutes.do(self._job)

        while self._running:
            schedule.run_pending()
            time.sleep(1)

        schedule.clear()
        logger.info("Scheduler stopped.")
