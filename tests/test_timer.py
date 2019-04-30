import logging
import unittest
from unittest.mock import Mock

from hardware import timer


class TestSubtimer(unittest.TestCase):

    def test_valid_config(self):
        subtimer = timer.Subtimer()
        self.assertEqual(subtimer.mode, timer.SubtimerMode.OFF)
        self.assertEqual(subtimer.speed, 0)
        self.assertEqual(subtimer.phase, 0)
        self.assertEqual(subtimer.interrupt_number, 0)
        subtimer.set_config(1, 10, 5, 255)
        self.assertEqual(subtimer.mode, timer.SubtimerMode.ONESHOT)
        self.assertEqual(subtimer.speed, 10)
        self.assertEqual(subtimer.phase, 5)
        self.assertEqual(subtimer.interrupt_number, 255)

    def test_invalid_config(self):
        subtimer = timer.Subtimer()
        with self.assertRaises(timer.InvalidSubtimerModeError):
            subtimer.set_config(10, 0, 0, 0)
        with self.assertRaises(timer.InvalidSubtimerSpeedError):
            subtimer.set_config(0, -1, 0, 0)
        with self.assertRaises(timer.InvalidSubtimerPhaseError):
            subtimer.set_config(0, 0, -1, 0)
        with self.assertRaises(timer.InvalidSubtimerPhaseError):
            subtimer.set_config(0, 0, 5, 0)
        with self.assertRaises(timer.InvalidSubtimerPhaseError):
            subtimer.set_config(0, 1, 5, 0)
        with self.assertRaises(timer.InvalidSubtimerPhaseError):
            subtimer.set_config(0, 2, 5, 0)
        with self.assertRaises(timer.InvalidSubtimerInterruptNumberError):
            subtimer.set_config(0, 0, 0, -1)
        with self.assertRaises(timer.InvalidSubtimerInterruptNumberError):
            subtimer.set_config(0, 0, 0, 256)


class TestTimer(unittest.TestCase):

    def setUp(self):
        self.speed = 7
        self.phase = 3
        self.int_num = 0x80
        self.runtime = self.speed * 10
        self.tmr = timer.Timer(10, 1)
        logging.getLogger('hardware.timer').setLevel(logging.ERROR)
        self.tmr._interrupt_controller = Mock()

    def test_off(self):
        self.tmr.set_subtimer(0, 0, self.speed, self.phase, self.int_num)
        modes, int_calls = self._run_timer()
        for mode in modes:
            self.assertEqual(mode, timer.SubtimerMode.OFF)
        for int_call in int_calls:
            self.assertIsNone(int_call)

    def test_oneshot(self):
        self.tmr.set_subtimer(0, 1, self.speed, self.phase, self.int_num)
        modes, int_calls = self._run_timer()
        for cnt in range(self.phase):
            self.assertEqual(modes[cnt], timer.SubtimerMode.ONESHOT)
            self.assertIsNone(int_calls[cnt])
        for cnt in range(self.phase, self.phase + 1):
            self.assertEqual(modes[cnt], timer.SubtimerMode.OFF)
            self.assertEqual(int_calls[cnt][0][0], self.int_num)
        for cnt in range(self.phase + 1, self.runtime):
            self.assertEqual(modes[cnt], timer.SubtimerMode.OFF)
            self.assertIsNone(int_calls[cnt])

    def test_periodic(self):
        self.tmr.set_subtimer(0, 2, self.speed, self.phase, self.int_num)
        modes, int_calls = self._run_timer()
        for mode in modes:
            self.assertEqual(mode, timer.SubtimerMode.PERIODIC)
        for cnt, int_call in enumerate(int_calls):
            if cnt % self.speed == self.phase:
                self.assertEqual(int_call[0][0], self.int_num)
            else:
                self.assertIsNone(int_call)

    def _run_timer(self):
        modes = []
        int_calls = []
        subtimer = self.tmr._subtimers[0]
        for cnt in range(self.runtime):
            self.tmr._step_count = cnt
            self.tmr._check_subtimer(0, subtimer)
            modes.append(subtimer.mode)
            int_calls.append(self.tmr._interrupt_controller.send.call_args)
            self.tmr._interrupt_controller.reset_mock()
        return modes, int_calls
