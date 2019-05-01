'''
Boot related stuff: BootImage, BootLoader
'''

from . import utils


class BootImage:
    '''
    Image that can contain the BIOS
    '''

    def __init__(self, size=0):
        self.size = size
        self.content = [0] * self.size

    def write_byte(self, pos, value):
        '''
        Write byte to image at position `pos`
        '''
        self.content[pos] = value

    def write_word(self, pos, value):
        '''
        Write word to image at position `pos`
        '''
        self.content[pos] = utils.get_high(value)
        self.content[pos + 1] = utils.get_low(value)

    def save(self, filename):
        '''
        Save image to file
        '''
        with open(filename, 'wb') as output_file:
            output_file.write(bytes(self.content))

    def load(self, filename):
        '''
        Load image from file
        '''
        with open(filename, 'rb') as input_file:
            self.content = list(input_file.read())
        self.size = len(self.content)


class BootLoader:
    '''
    BootLoader to load image (BIOS) and executable (OS) into RAM
    '''

    def __init__(self, ram):
        self._ram = ram

    def load_image(self, pos, image):
        '''
        Load image into RAM at position `pos`
        '''
        for idx in range(image.size):
            self._ram.write_byte(pos + idx, image.content[idx], silent=True)

    def load_executable(self, pos, exe):
        '''
        Load executable into RAM at position `pos`
        '''
        for idx, opbyte in enumerate(exe.opcode):
            self._ram.write_byte(pos + idx, opbyte, silent=True)
