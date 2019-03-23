from kivy.config import Config
Config.set('graphics', 'width', 600)
Config.set('graphics', 'height', 430)

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color
from kivy.logger import Logger
from kivy.uix.label import Label
from kivy.uix.widget import Widget

import aux
from . import device


DEVICE_TYPE = 0x05
DEVICE_ID = 0x000000
DEVICE_CLASS = 'PongMonitor'


class PongMonitorWidget(Widget):

    def __init__(self, game_state, device):
        super(PongMonitorWidget, self).__init__()
        self.game_state = game_state
        self.device = device
        self.game_elements = {}
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'w':
            self.device.send_data(b'LU')
        elif keycode[1] == 's':
            self.device.send_data(b'LD')
        elif keycode[1] == 'up':
            self.device.send_data(b'RU')
        elif keycode[1] == 'down':
            self.device.send_data(b'RD')
        elif keycode[1] == 'escape':
            App.get_running_app().stop()
        return True

    def build(self):
        with self.canvas:
            Color(0.2, 0.2, 0.2)
            self.game_elements['background'] = Rectangle(
                pos=(0, 0)
            )
            Color(1, 1, 1)
            self.game_elements['top_wall'] = Rectangle()
            self.game_elements['bottom_wall'] = Rectangle()
            self.game_elements['net'] = Rectangle()
            self.game_elements['ball'] = Rectangle(
                size=(10, 10)
            )
            self.game_elements['left_paddle'] = Rectangle()
            self.game_elements['right_paddle'] = Rectangle()
            self.game_elements['left_score'] = Label(
                text='L',
                font_size='16pt',
                bold=True,
            )
            self.game_elements['right_score'] = Label(
                text='R',
                font_size='16pt',
                bold=True,
            )
        self.paint()

    def update(self, dt):
        self.paint()

    def paint(self):
        self.game_elements['background'].size = (self.width, self.height)
        self.game_elements['top_wall'].pos = (0, self.height - 10)
        self.game_elements['top_wall'].size = (self.width, 10)
        self.game_elements['bottom_wall'].pos = (0, 0)
        self.game_elements['bottom_wall'].size = (self.width, 10)
        self.game_elements['net'].pos = (self.width / 2, 0)
        self.game_elements['net'].size = (1, self.height)
        self.game_elements['ball'].pos = (
            self.width/2 + 1.0 * self.game_state['ball_x'] * self.game_state['zoom'] - 5,
            self.height/2 - 1.0 * self.game_state['ball_y'] * self.game_state['zoom'] - 5
        )
        self.game_elements['left_paddle'].size = (
            5,
            2.0 * self.game_state['paddle_size'] * self.game_state['zoom']
        )
        self.game_elements['left_paddle'].pos = (
            self.width/2 + 1.0 * self.game_state['left_paddle_x'] * self.game_state['zoom'] - 10,
            self.height/2 - 1.0 * self.game_state['left_paddle_y'] * self.game_state['zoom'] - self.game_state['paddle_size'] * self.game_state['zoom']
        )
        self.game_elements['right_paddle'].size = (
            5,
            2.0 * self.game_state['paddle_size'] * self.game_state['zoom']
        )
        self.game_elements['right_paddle'].pos = (
            self.width/2 + 1.0 * self.game_state['right_paddle_x'] * self.game_state['zoom'] + 0,
            self.height/2 - 1.0 * self.game_state['right_paddle_y'] * self.game_state['zoom'] - self.game_state['paddle_size'] * self.game_state['zoom']
        )
        self.game_elements['left_score'].pos = (
            0.4 * self.width - self.game_elements['left_score'].width / 2,
            self.height - self.game_elements['left_score'].height / 2 - 20,
        )
        self.game_elements['right_score'].pos = (
            0.6 * self.width - self.game_elements['right_score'].width / 2,
            self.height - self.game_elements['right_score'].height / 2 - 20,
        )
        self.game_elements['left_score'].text = str(self.game_state['left_score'])
        self.game_elements['right_score'].text = str(self.game_state['right_score'])


class PongMonitorApp(App):

    def __init__(self, game_state, device):
        super(PongMonitorApp, self).__init__()
        self.game_state = game_state
        self.device = device

    def build(self):
        widget = PongMonitorWidget(self.game_state, self.device)
        widget.build()
        self.widget = widget
        Clock.schedule_interval(widget.update, 1 / self.game_state['fps'])
        return widget


class PongMonitor(device.Device):

    game_state = {
        'fps': 20,
        'zoom': 0.5,
        'ball_x': 0,
        'ball_y': 0,
        'left_paddle_x': 0,
        'left_paddle_y': 0,
        'right_paddle_x': 0,
        'right_paddle_y': 0,
        'paddle_size': 0,
        'left_score': 0,
        'right_score': 0,
    }

    def handle_data(self, data):
        # Logger.debug('data=[%s]' % aux.binary_to_str(data))
        for idx, name in enumerate([
            'ball_x', 'ball_y',
            'left_paddle_x', 'left_paddle_y',
            'right_paddle_x', 'right_paddle_y',
            'paddle_size',
            'left_score', 'right_score',
        ]):
            self.game_state[name] = aux.word_to_signed((data[2 * idx] << 8) + data[2 * idx + 1])
        return 200, 'Ok\n'

    def run(self, args):
        self.app = PongMonitorApp(self.game_state, self).run()
        return 0
