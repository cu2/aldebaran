import datetime
import threading
import time

from utils import utils


TIMER_MODE_OFF = 0
TIMER_MODE_ONESHOT = 1
TIMER_MODE_PERIODIC = 2


class Timer(utils.Hardware):

    def __init__(self, freq, log=None):
        utils.Hardware.__init__(self, log)
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
        } for _ in range(8)]
        self.interrupt_controller = None

    def register_architecture(self, interrupt_controller):
        self.interrupt_controller = interrupt_controller

    def timer_thread_run(self):
        self.start_time = time.time()
        while True:
            self.log.log('timer', 'Beat %s' % datetime.datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S.%f')[:11])
            for subtimer in self.subtimers:
                if subtimer['mode'] == TIMER_MODE_OFF:
                    continue
                if subtimer['speed'] > 1:
                    if self.step_count % subtimer['speed'] != subtimer['phase']:
                        continue
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
        self.log.log('timer', 'Starting...')
        self.timer_thread = threading.Thread(target=self.timer_thread_run)
        self.timer_thread.start()
        self.log.log('timer', 'Started.')
        return 0

    def stop(self):
        self.log.log('timer', 'Stopping...')
        self.stop_event.set()
        self.timer_thread.join()
        self.log.log('timer', 'Stopped.')

    def set_subtimer(self, subtimer_number, subtimer_config):
        self.subtimers[subtimer_number] = subtimer_config
        self.log.log('timer', 'Subtimer %s set.' % utils.byte_to_str(subtimer_number))
