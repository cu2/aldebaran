class Log(object):

    def __init__(self):
        self.term_colors = True
        self.part_colors = {
            'aldebaran': self.col('0;31'),
            'clock': self.col('1;30'),
            'cpu': self.col('0;32'),
            'ram': self.col('0;36'),
            'print': self.col('37;1'),
        }

    def col(self, colstr=None):
        if not self.term_colors:
            return ''
        if colstr:
            return '\033[%sm' % colstr
        else:
            return '\033[0m'

    def log(self, part, msg):
        print '%s[%s] %s%s' % (
            self.part_colors.get(part, ''),
            part,
            msg,
            self.col(),
        )


class SilentLog(object):

    def log(self, part, msg):
        pass


class Hardware(object):

    def __init__(self, log=None):
        if log:
            self.log = log
        else:
            self.log = SilentLog()


def bytes_to_word(high, low):
    return 256 * high + low


def word_to_bytes(word):
    if word > 65535:
        raise Exception('Word out of range: %s' % word)
    return (
        word / 256,
        word % 256,
    )


def byte_to_str(byte):
    return hex(byte)[2:].zfill(2).upper()


def word_to_str(word):
    return hex(word)[2:].zfill(4).upper()


def str_to_int(str):
    return int(str, 16)
