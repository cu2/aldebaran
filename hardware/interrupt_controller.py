import queue

from utils import utils


class InterruptController(utils.Hardware):
    '''
    Interrupt Controller

    Currently a simple FIFO queue. Later it can change to something that handles e.g. priorities.
    '''

    def __init__(self, log=None):
        utils.Hardware.__init__(self, log)
        self.interrupt_queue = queue.Queue()

    def check(self):
        interrupt_number = None
        try:
            interrupt_number = self.interrupt_queue.get_nowait()
        except queue.Empty:
            pass
        if interrupt_number is not None:
            self.log.log('interrupt_controller', 'Forwarded IRQ: %s' % utils.byte_to_str(interrupt_number))
        return interrupt_number

    def send(self, interrupt_number):
        try:
            interrupt_number = int(interrupt_number)
            if interrupt_number < 0 or interrupt_number > 255:
                raise ValueError()
        except ValueError:
            self.log.log('interrupt_controller', 'Illegal IRQ: %s' % interrupt_number)
            return
        self.interrupt_queue.put(interrupt_number)
        self.log.log('interrupt_controller', 'Received IRQ: %s' % utils.byte_to_str(interrupt_number))
