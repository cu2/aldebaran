import datetime
import logging
import threading
import time

from utils import config, utils


logger = logging.getLogger(__name__)


TIMER_MODE_OFF = 0
TIMER_MODE_ONESHOT = 1
TIMER_MODE_PERIODIC = 2


class Timer:

    def __init__(self, freq):
        if freq:
            self.speed = 1 / freq
        else:
            self.speed = 0
        self.start_time = None
        self.step_count = 0
        self.stop_event = threading.Event()
        self.subtimers = [{
            'mode': TIMER_MODE_OFF,
            'speed': 1,
            'phase': 0,
            'interrupt_number': 0,
        } for _ in range(config.number_of_timers)]
        self.interrupt_controller = None

    def register_architecture(self, interrupt_controller):
        self.interrupt_controller = interrupt_controller

    def timer_thread_run(self):
        self.start_time = time.time()
        while True:
            logger.debug('Beat %s', datetime.datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S.%f')[:11])
            for subtimer_number, subtimer in enumerate(self.subtimers):
                if subtimer['mode'] == TIMER_MODE_OFF:
                    continue
                if subtimer['speed'] > 1:
                    if self.step_count % subtimer['speed'] != subtimer['phase']:
                        continue
                logger.info('Subtimer %s called IRQ %s.', utils.byte_to_str(subtimer_number), utils.byte_to_str(subtimer['interrupt_number']))
                self.interrupt_controller.send(subtimer['interrupt_number'])
                if subtimer['mode'] == TIMER_MODE_ONESHOT:
                    subtimer['mode'] = TIMER_MODE_OFF
            self.step_count += 1
            if self.stop_event.wait(0):
                break
            self.sleep()

    def sleep(self):
        sleep_time = self.start_time + self.speed - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.start_time = time.time()

    def start(self):
        logger.info('Starting...')
        self.timer_thread = threading.Thread(target=self.timer_thread_run)
        self.timer_thread.start()
        logger.info('Started.')
        return 0

    def stop(self):
        logger.info('Stopping...')
        self.stop_event.set()
        self.timer_thread.join()
        logger.info('Stopped.')

    def set_subtimer(self, subtimer_number, subtimer_config):
        self.subtimers[subtimer_number] = subtimer_config
        logger.info('Subtimer %s set.', utils.byte_to_str(subtimer_number))
