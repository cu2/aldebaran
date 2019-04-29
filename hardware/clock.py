'''
Clock that drives the CPU
'''

import logging
import time

from utils.errors import ArchitectureError


logger = logging.getLogger(__name__)


class Clock:
    '''
    Clock
    '''

    def __init__(self, freq=0):
        if freq:
            self.period = 1 / freq
        else:
            self.period = None
        self.start_time = None
        self.cycle_count = 0
        self.sleep_time = 0
        self.cpu = None
        self.architecture_registered = False

    def register_architecture(self, cpu):
        '''
        Register other internal devices
        '''
        self.cpu = cpu
        self.architecture_registered = True

    def run(self):
        '''
        Main loop: signal CPU and sleep periodically
        '''
        if not self.architecture_registered:
            raise ArchitectureError('Clock cannot run without registering architecture')
        if not self.cpu.architecture_registered:
            raise ArchitectureError('CPU cannot run without registering architecture')
        logger.info('Started.')
        self.start_time = time.time()
        try:
            while True:
                self.cycle_count += 1
                logger.debug('Cycle %d', self.cycle_count)
                self.cpu.step()
                self._sleep()
                if self.cpu.shutdown:
                    break
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            logger.info('Stopped.')

    def _sleep(self):
        '''
        Sleep enough so that the average cycle period converges to `Clock.period`
        '''
        if self.period is None:
            return
        sleep_time = self.start_time + self.cycle_count * self.period - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
            self.sleep_time += sleep_time
