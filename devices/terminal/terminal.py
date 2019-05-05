'''
Primitive terminal device
'''

from http import HTTPStatus

from devices import device
from utils import utils


DEVICE_TYPE = 0x01
DEVICE_ID = 0xABCDEF
DEVICE_CLASS = 'Terminal'


class Terminal(device.Device):
    '''
    Terminal
    '''

    def run(self, args):
        while True:
            try:
                text = input('Type some text: ')
            except (KeyboardInterrupt, SystemExit, EOFError):
                print()
                break
            self.send_text(text)

    def handle_data(self, data):
        print('\033[0;36m%s\033[0m' % data.decode('utf-8'))
        return (
            HTTPStatus.OK,
            {
                'message': 'Received data: {}'.format(utils.binary_to_str(data)),
            }
        )
