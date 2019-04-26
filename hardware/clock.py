import datetime
import logging
import time

from utils import utils


logger = logging.getLogger(__name__)


class Clock:

    def __init__(self, freq):
        if freq:
            self.speed = 1 / freq
        else:
            self.speed = 0
        self.start_time = None
        self.cpu = None
        self.cycle_count = 0

    def register_architecture(self, cpu):
        self.cpu = cpu

    def run(self):
        if not self.cpu:
            logger.info('ERROR: Cannot run without CPU.')
            return 1
        logger.info('Started.')
        self.start_time = time.time()
        shutdown = False
        try:
            while not shutdown:
                logger.debug(
                    'Cycle %d @ %s',
                    self.cycle_count + 1,
                    datetime.datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S.%f')[:11],
                )
                shutdown = self.cpu.step()
                self.cycle_count += 1
                self.sleep()
        except (KeyboardInterrupt, SystemExit):
            logger.info('Stopped.')
        return 0

    def sleep(self):
        sleep_time = self.start_time + self.speed - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.start_time = time.time()
