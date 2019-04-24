import datetime
import time

from utils import utils


class Clock(utils.Hardware):

    def __init__(self, freq, log=None):
        utils.Hardware.__init__(self, log)
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
            self.log.log('clock', 'ERROR: Cannot run without CPU.')
            return 1
        self.log.log('clock', 'Started.')
        self.start_time = time.time()
        shutdown = False
        try:
            while not shutdown:
                self.log.log('clock', 'Beat %s' % datetime.datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S.%f')[:11])
                shutdown = self.cpu.step()
                self.cycle_count += 1
                self.sleep()
        except (KeyboardInterrupt, SystemExit):
            self.log.log('clock', 'Stopped.')
        return 0

    def sleep(self):
        sleep_time = self.start_time + self.speed - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.start_time = time.time()
