import hid
import logging
import random

from future.utils import iteritems
from tinydb import Query, TinyDB

from chromarestserver.effect import (
    matrix_effect_custom_frame,
    matrix_effect_static,
    matrix_effect_none,
    set_custom_frame,
    VARSTORE
)


class Color():

    def __init__(self, r, g, b):
        """Create a color from three integers r, g, b

        Args:
            r (int): red value 0-255
            g (int): green value 0-255
            b (int): blue value 0-255
        """
        self.r = r
        self.g = g
        self.b = b

    @staticmethod
    def from_hex(x):
        r, g, b = [ord(c) for c in x.lstrip('#').decode('hex')]
        return Color(r, g, b)

    @staticmethod
    def from_long(x):
        r = (x >> 16) & 255
        g = (x >> 8) & 255
        b = x & 255
        return Color(r, g, b)

    @staticmethod
    def from_long_bgr(x):
        r = x & 255
        g = (x >> 8) & 255
        b = (x >> 16) & 255
        return Color(r, g, b)

    def to_rgb(self):
        return [self.r, self.g, self.b]


class SessionModel():
    def __init__(self):
        self.logger = logging.getLogger()
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self.logger.debug('creating tinydb connection')
            self._db = TinyDB('chromarestserver.json')
        return self._db

    def create(self, data):
        self.logger.info('creating session')
        session_id = random.randint(100, 10000000)

        record = {
            'id': session_id,
            'app': data
        }

        self.db.insert(record)

        return record

    def load(self, session_id):
        self.logger.info('loading session_id="%s"', session_id)
        db = self.db
        Session = Query()
        found = db.search(Session.id == session_id)
        if found:
            return found[0]
        return None

    def delete(self, session_id):
        self.logger.info('deleting session_id="%s"', session_id)
        db = self.db
        Session = Query()
        db.remove(Session.id == session_id)


class USBModel():

    RAZER_VENDOR_ID = 0x1532

    def __init__(self):
        self.logger = logging.getLogger()
        self._device = None

    @property
    def device(self):
        if self._device is None:
            self.logger.info('Looking for Razer device')
            for info in hid.enumerate():
                self.logger.debug('Considering device info="%s"', info)
                if (info['vendor_id'] == USBModel.RAZER_VENDOR_ID
                        and self.is_product_supported(info['product_id'])):
                    self.logger.info('Found device info="%s"', info)
                    device = hid.device()
                    device.open(
                        vendor_id=info['vendor_id'],
                        product_id=info['product_id']
                    )
                    self._device = device
                    break

        if self._device is None:
            raise RuntimeError('No Razer device found')

        return self._device

    @device.setter
    def device(self, value):
        self._device = value

    def effect(self, name, params=None):
        self.logger.info('effect name="%s", params="%s"',
                         name, params)
        device = self.device
        if 'CHROMA_NONE' == name:
            effect = matrix_effect_none(device)
            effect.run()
        elif 'CHROMA_STATIC' == name:
            r, g, b = Color.from_long_bgr(params['color']).to_rgb()
            effect = matrix_effect_static(device, r, g, b)
            effect.run()
        elif 'CHROMA_CUSTOM' == name:
            rows = params
            effect = matrix_effect_custom_frame(device, VARSTORE)
            effect.run()
            for idx, row in enumerate(rows):

                rgbs = [
                    x
                    for col in row
                    for x in Color.from_long_bgr(col).to_rgb()
                ]
                effect = set_custom_frame(device, idx, 0, len(row), rgbs=rgbs)
                effect.run()

    def is_product_supported(self, product_id):
        raise NotImplementedError("Subclass missing 'is_product_supported()'")


class KeyboardModel(USBModel):

    RAZER_BLACKWIDOW_ULTIMATE_2012 = 0x010D
    RAZER_ANANSI = 0x010F
    RAZER_NOSTROMO = 0x0111
    RAZER_ORBWEAVER = 0x0113
    RAZER_ORBWEAVER_CHROMA = 0x0207
    RAZER_BLACKWIDOW_ULTIMATE_2013 = 0x011A
    RAZER_BLACKWIDOW_ORIGINAL = 0x011B
    RAZER_BLACKWIDOW_ORIGINAL_ALT = 0x010E
    RAZER_TARTARUS = 0x0201
    RAZER_DEATHSTALKER_EXPERT = 0x0202
    RAZER_BLACKWIDOW_CHROMA = 0x0203
    RAZER_DEATHSTALKER_CHROMA = 0x0204
    RAZER_BLADE_STEALTH = 0x0205
    RAZER_TARTARUS_CHROMA = 0x0208
    RAZER_BLACKWIDOW_CHROMA_TE = 0x0209
    RAZER_BLADE_QHD = 0x020F
    RAZER_BLADE_PRO_LATE_2016 = 0x0210
    RAZER_BLACKWIDOW_OVERWATCH = 0x0211
    RAZER_BLACKWIDOW_ULTIMATE_2016 = 0x0214
    RAZER_BLACKWIDOW_X_CHROMA = 0x0216
    RAZER_BLACKWIDOW_X_ULTIMATE = 0x0217
    RAZER_BLACKWIDOW_X_CHROMA_TE = 0x021A
    RAZER_ORNATA_CHROMA = 0x021E
    RAZER_ORNATA = 0x021F
    RAZER_BLADE_STEALTH_LATE_2016 = 0x0220
    RAZER_BLACKWIDOW_CHROMA_V2 = 0x0221
    RAZER_BLADE_LATE_2016 = 0x0224
    RAZER_BLADE_STEALTH_MID_2017 = 0x022D
    RAZER_BLADE_PRO_2017 = 0x0225
    RAZER_BLADE_PRO_2017_FULLHD = 0x022F
    RAZER_BLADE_STEALTH_LATE_2017 = 0x0232

    def __init__(self):
        super(KeyboardModel, self).__init__()

    def is_product_supported(self, product_id):
        for name, value in iteritems(vars(KeyboardModel)):
            if not name.startswith('RAZER_'):
                continue
            self.logger.debug('value="%s", name="%s"', value, name)
            if int(product_id) == int(value):
                return True
        return False
