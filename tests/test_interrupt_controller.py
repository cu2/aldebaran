import logging
import unittest

from hardware import interrupt_controller


class TestInterruptController(unittest.TestCase):

    def setUp(self):
        self.int_cont = interrupt_controller.InterruptController()
        logging.getLogger('hardware.interrupt_controller').setLevel(logging.ERROR)

    def test_send_error(self):
        with self.assertRaises(interrupt_controller.InvalidInterruptError):
            self.int_cont.send('non-integer')
        with self.assertRaises(interrupt_controller.InvalidInterruptError):
            self.int_cont.send(-1)
        with self.assertRaises(interrupt_controller.InvalidInterruptError):
            self.int_cont.send(256)

    def test_send_ok(self):
        self.assertEqual(self.int_cont._interrupt_queue.qsize(), 0)
        self.int_cont.send(15)
        self.assertEqual(self.int_cont._interrupt_queue.qsize(), 1)
        self.int_cont.send(25)
        self.assertEqual(self.int_cont._interrupt_queue.qsize(), 2)
        self.assertEqual(self.int_cont._interrupt_queue.get(), 15)
        self.assertEqual(self.int_cont._interrupt_queue.get(), 25)

    def test_check_empty(self):
        self.assertIsNone(self.int_cont.check())

    def test_check_non_empty(self):
        self.int_cont._interrupt_queue.put(15)
        self.int_cont._interrupt_queue.put(25)
        self.assertEqual(self.int_cont.check(), 15)
        self.assertEqual(self.int_cont.check(), 25)
