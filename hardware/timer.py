'''
Timer related stuff
'''

import logging
import threading
import time
from enum import Enum

from utils import config
from utils import utils
from utils.errors import AldebaranError, ArchitectureError


logger = logging.getLogger(__name__)


class Timer:
    '''
    Timer running with a frequency, handling subtimers
    '''

    def __init__(self, freq, number_of_subtimers):
        if freq:
            self._period = 1 / freq
        else:
            self._period = None
        self._start_time = None
        self._step_count = 0
        self._stop_event = threading.Event()
        self._timer_thread = threading.Thread(target=self._timer_thread_run)
        self._subtimers = [Subtimer() for _ in range(number_of_subtimers)]
        self._interrupt_controller = None
        self._architecture_registered = False

    def register_architecture(self, interrupt_controller):
        '''
        Register other internal devices
        '''
        self._interrupt_controller = interrupt_controller
        self._architecture_registered = True

    def start(self):
        '''
        Start thread
        '''
        if not self._architecture_registered:
            raise ArchitectureError('Timer cannot run without registering architecture')
        logger.info('Starting...')
        self._timer_thread.start()
        logger.info('Started.')

    def stop(self):
        '''
        Set stop event and wait for thread to terminate
        '''
        logger.info('Stopping...')
        self._stop_event.set()
        self._timer_thread.join()
        logger.info('Stopped.')

    def is_alive(self):
        '''
        Check if thread is alive
        '''
        return self._timer_thread.is_alive()

    def set_subtimer(self, subtimer_number, raw_mode, speed, phase, interrupt_number):
        '''
        Set subtimer's config
        '''
        try:
            self._subtimers[subtimer_number].set_config(raw_mode, speed, phase, interrupt_number)
        except IndexError:
            raise NoSubtimerError('No subtimer with number: {}'.format(subtimer_number))
        logger.info('Subtimer %s set.', utils.byte_to_str(subtimer_number))

    def _timer_thread_run(self):
        try:
            self._start_time = time.time()
            while True:
                logger.debug('Beat %s', self._step_count)
                for subtimer_number, subtimer in enumerate(self._subtimers):
                    self._check_subtimer(subtimer_number, subtimer)
                self._step_count += 1
                if self._stop_event.wait(0):
                    break
                self._sleep()
        except AldebaranError as ex:
            logger.error('Crashed: {}({})'.format(
                ex.__class__.__name__,
                str(ex),
            ))
        except (KeyboardInterrupt, SystemExit) as ex:
            logger.error('Stopped: {}({})'.format(
                ex.__class__.__name__,
                str(ex),
            ))

    def _check_subtimer(self, subtimer_number, subtimer):
        if subtimer.mode == SubtimerMode.OFF:
            return
        if subtimer.speed > 1:
            if self._step_count % subtimer.speed != subtimer.phase:
                return
        logger.info(
            'Subtimer %s called IRQ %s.',
            utils.byte_to_str(subtimer_number),
            utils.byte_to_str(subtimer.interrupt_number),
        )
        self._interrupt_controller.send(subtimer.interrupt_number)
        if subtimer.mode == SubtimerMode.ONESHOT:
            subtimer.mode = SubtimerMode.OFF

    def _sleep(self):
        '''
        Sleep enough so that the average period converges to `Timer._period`
        '''
        if self._period is None:
            return
        sleep_time = self._start_time + self._step_count * self._period - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)


class Subtimer:
    '''
    Subtimer
    '''

    def __init__(self):
        self.mode = SubtimerMode.OFF
        self.speed = 0
        self.phase = 0
        self.interrupt_number = 0

    def set_config(self, raw_mode, speed, phase, interrupt_number):
        '''
        Set subtimer's config
        '''
        try:
            self.mode = SubtimerMode(raw_mode)
        except ValueError:
            raise InvalidSubtimerModeError('Invalid subtimer mode: {}'.format(raw_mode))

        if speed < 0:
            raise InvalidSubtimerSpeedError('Invalid subtimer speed: {}'.format(speed))
        self.speed = speed

        if phase < 0:
            raise InvalidSubtimerPhaseError('Invalid subtimer phase: {}'.format(phase))
        if speed < 1 and phase > 0:
            raise InvalidSubtimerPhaseError('Invalid subtimer phase: {}'.format(phase))
        if speed >= 1 and phase > speed - 1:
            raise InvalidSubtimerPhaseError('Invalid subtimer phase: {}'.format(phase))
        self.phase = phase

        if interrupt_number < 0 or interrupt_number > config.number_of_interrupts - 1:
            raise InvalidSubtimerInterruptNumberError('Invalid subtimer interrupt number: {}'.format(interrupt_number))
        self.interrupt_number = interrupt_number


class SubtimerMode(Enum):
    '''
    Mode of subtimer
    '''
    OFF = 0
    ONESHOT = 1
    PERIODIC = 2


# pylint: disable=missing-docstring

class TimerError(AldebaranError):
    pass


class InvalidSubtimerModeError(TimerError):
    pass


class InvalidSubtimerSpeedError(TimerError):
    pass


class InvalidSubtimerPhaseError(TimerError):
    pass


class InvalidSubtimerInterruptNumberError(TimerError):
    pass


class NoSubtimerError(TimerError):
    pass


class TimerCrashError(TimerError):
    pass
