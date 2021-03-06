from ccinput import ButtonReader, DialReader, Press
import cctime
from mode import Mode
import sys


class MenuMode(Mode):
    def __init__(self, app, button_map, dial_map):
        super().__init__(app)
        self.cv = self.frame.pack(0x80, 0x80, 0x80)
        self.cursor_cv = self.frame.pack(0x00, 0xff, 0x00)
        self.cursor_label = self.frame.new_label('>', 'kairon-10')

        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'PREV_OPTION',
                Press.LONG: 'BACK',
            },
            button_map['DOWN']: {
                Press.SHORT: 'NEXT_OPTION',
                Press.LONG: 'PROCEED',
            },
            button_map['ENTER']: {
                Press.SHORT: 'PROCEED',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.frame.clear()
        wifi_ssid = self.app.prefs.get('wifi_ssid')
        updater = self.app.clock_mode.updater
        index_updated = updater.index_updated or 'None'
        index_fetched = (updater.index_fetched and
            updater.index_fetched.isoformat() or 'Not yet')
        software_version = sys.path[0]
        esp_firmware_version = self.app.network.get_firmware_version()
        esp_hardware_address = self.app.network.get_hardware_address()
        sec = self.app.prefs.get('auto_cycling_sec')
        auto_cycling = sec and f'{sec} seconds' or 'Off'

        # Each node has the form (title, value, command, arg, children).
        self.tree = ('Settings', None, None, None, [
            ('Wi-Fi setup', None, None, None, [
                ('Network', wifi_ssid, 'WIFI_SSID_MODE', None, []),
                ('Password', None, 'WIFI_PASSWORD_MODE', None, []),
                ('Back', None, 'BACK', None, [])
            ]),
            (f'Auto cycling', auto_cycling, None, None, [
                ('Off', None, 'SET_CYCLING', 0, []),
                ('15 seconds', None, 'SET_CYCLING', 15, []),
                ('60 seconds', None, 'SET_CYCLING', 60, []),
                ('Back', None, 'BACK', None, [])
            ]),
            ('System info', None, None, None, [
                (updater.index_name or 'Climate Clock', None, None, None, []),
                (f'Version', software_version, None, None, []),
                (f'Time', cctime.get_datetime().isoformat(), None, None, []),
                (f'Index version', index_updated, None, None, []),
                (f'Index fetched', index_fetched, None, None, []),
                (f'ESP firmware', esp_firmware_version, None, None, []),
                (f'MAC ID', esp_hardware_address, None, None, []),
                ('Back', None, 'BACK', None, [])
            ]),
            ('Exit', None, 'CLOCK_MODE', None, [])
        ])
        self.node = None
        self.crumbs = []
        self.proceed(self.tree)

    def proceed(self, node):
        title, value, command, arg, children = node
        if command:
            self.app.receive(command, arg)
        else:
            if self.node:
                self.crumbs.append((self.node, self.top, self.index))
            self.node = node
            self.top = self.index = self.offset = 0
            self.draw()

    def draw(self):
        title, value, command, arg, children = self.node
        self.frame.clear()
        if value and not children:
            title += ': ' + value
        label = self.frame.new_label(title, 'kairon-10')
        self.frame.paste(1 - self.offset, 0, label, cv=self.cv)
        y = 0
        for index in range(self.top, self.top + 3):
            if index >= len(children):
                break
            child_title, child_value, _, _, _ = children[index]
            if child_value:
                child_title += ': ' + child_value
            label = self.frame.new_label(child_title, 'kairon-10')
            self.frame.paste(64, y, label, cv=self.cv)
            if index == self.index:
                self.frame.paste(58, y, self.cursor_label, cv=self.cursor_cv)
            y += 11
        self.frame.send()

    def step(self):
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)
        # TODO: Currently every mode's step() method must call self.frame.send()
        # in order for sdl_frame to detect events; fix this leaky abstraction.
        self.frame.send()

    def receive(self, command, arg=None):
        if command == 'SELECTOR':
            delta, value = arg
            self.move_cursor(delta)
        if command == 'PREV_OPTION':
            self.move_cursor(-1)
        if command == 'NEXT_OPTION':
            self.move_cursor(1)
        if command == 'SET_CYCLING':
            self.app.prefs.set('auto_cycling_sec', arg)
            self.app.receive('MENU_MODE')  # reformat the menu strings
        if command == 'PROCEED':
            title, value, command, arg, children = self.node
            if children:
                self.proceed(children[self.index])
            else:
                command = 'BACK'
        if command == 'BACK':
            self.node, self.top, self.index = self.crumbs.pop()
            self.offset = 0
            self.draw()

    def move_cursor(self, delta):
        title, value, command, arg, children = self.node
        if children:
            self.index = max(0, min(len(children) - 1, self.index + delta))
            self.top = max(self.index - 2, min(self.index, self.top))
        else:
            self.offset = max(0, self.offset + delta * 12)
        self.draw()



