# -*- coding: utf-8 -*-
"""Models module

This module contains classes that hide the implementation details of
Razer Chroma effect dispatch, USB device connectivity, and Chroma SDK session
management.
"""
import codecs
import hid
import logging
import random

from future.utils import iteritems
from tinydb import Query, TinyDB

from chromarestserver.effect import (
    matrix_effect_custom_frame,
    matrix_effect_static,
    matrix_effect_spectrum,
    matrix_effect_none,
    matrix_effect_wave,
    set_custom_frame,
    set_led_effect
)


class RGB():

    def __init__(self, r=0, g=0, b=0):
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
        """Create `RGB` object from a hex string.

        Args:
            x (str): hex string such as 'FF0000' or '#FF0000'

        Returns:
            :obj:`chromarestserver.model.RGB` instance

        Example:
            >>> RGB.from_hex("#FF0000")
        """
        r, g, b = [c for c in codecs.decode(x.lstrip('#'), 'hex')]
        return RGB(r, g, b)

    @staticmethod
    def from_long(x):
        """Create `RGB` object from a long int (RGB ordered)

        Args:
            x (int): RGB ordered integer such as 65280

        Returns:
            :obj:`chromarestserver.model.RGB` instance

        Example:
            >>> RGB.from_long(65280)
        """
        x = int(x)
        r = (x >> 16) & 255
        g = (x >> 8) & 255
        b = x & 255
        return RGB(r, g, b)

    @staticmethod
    def from_long_bgr(x):
        """Create `RGB` object from a long int (BGR ordered)

        Args:
            x (int): BGR ordered integer such as 65280

        Returns:
            :obj:`chromarestserver.model.RGB` instance

        Example:
            >>> RGB.from_long(65280)
        """
        r = x & 255
        g = (x >> 8) & 255
        b = (x >> 16) & 255
        return RGB(r, g, b)

    def to_rgb(self):
        """Get a list of R, G, B integer values.

        Returns:
            :obj:`list` of :obj:`int` with 3 elements; R, G, and B

        Example:
            >>> RGB.from_hex('#FF0000').to_rgb()
            [255, 0, 0]
        """
        return [self.r, self.g, self.b]

    def __repr__(self):
        return 'RGB(r={}, g={}, b={})'.format(self.r, self.g, self.b)


class Color(RGB):

    RED = RGB.from_hex('FF0000')
    ORANGE = RGB.from_hex('FFA500')
    YELLOW = RGB.from_hex('FFFF00')
    GREEN = RGB.from_hex('00FF00')
    BLUE = RGB.from_hex('0000FF')
    PURPLE = RGB.from_hex('A020F0')
    WHITE = RGB.from_hex('FFFFFF')
    BLACK = RGB.from_hex('000000')
    CYAN = RGB.from_hex('00FFFF')
    MAGENTA = RGB.from_hex('FF00FF')
    BROWN = RGB.from_hex('A52A2A')
    PINK = RGB.from_hex('FFC0CB')

    def __init__(self, r=0, g=0, b=0):
        """Create a color from three integers r, g, b

        Args:
            r (int): red value 0-255
            g (int): green value 0-255
            b (int): blue value 0-255
        """
        super(Color, self).__init__(r, g, b)

    @staticmethod
    def random():
        return Color(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )


class SessionModel():

    def __init__(self):
        """Management of Chroma SDK REST sessions.

        The Chroma SDK REST server asks the developer to create, update,
        and delete application sessions with the API.

        Attrbutes:
            logger (:obj:`logging.Logger`): Python logger for this class.
        """

        self.logger = logging.getLogger()
        self._db = None

    @property
    def db(self):
        """:obj:`tinydb.TinyDB`: Connection to the session storage database.

        This is cached within the same process and will only attempt
        connection the first time you call it.
        """
        if self._db is None:
            self.logger.debug('creating tinydb connection')
            self._db = TinyDB('chromarestserver.json')
        return self._db

    def create(self, data):
        """Create a session.

        Args:
            data (dict): Information about the application.  See the
                official Chroma SDK REST Documentation for the expected
                format of this data.

        Returns:
            dict
        """
        self.logger.info('creating session')
        session_id = random.randint(100, 10000000)

        record = {
            'id': session_id,
            'app': data
        }

        self.db.insert(record)

        return record

    def load(self, session_id):
        """Load a session.

        Args:
            session_id (str): the session id to lookup

        Returns:
            dict: if a session with that id is found
            None: no session was found
        """
        self.logger.info('loading session_id="%s"', session_id)
        db = self.db
        Session = Query()
        found = db.search(Session.id == session_id)
        if found:
            return found[0]
        return None

    def delete(self, session_id):
        """Delete a session.

        Args:
            session_id (str): the session id to delete
        """
        self.logger.info('deleting session_id="%s"', session_id)
        db = self.db
        Session = Query()
        db.remove(Session.id == session_id)


class USBModel():

    RAZER_VENDOR_ID = 0x1532

    def __init__(self):
        """Base class for device categories that do USB communication.

        Attributes:
            logger (:obj:`logging.Logger`): Python logger for this class.
"""

        self.logger = logging.getLogger()
        self._device = None

    @property
    def device(self):
        """Find and connect a supported Razer USB device

        This will call out to a method called `is_product_supported`
        in order to determine if the device should be selected for
        a particular subclass.

        Sub classes need to implement a `is_product_supported` method
        which takes an HID `product_id`, returning True or False.

        Raises:
            RuntimeError: If unable to find a device

        Returns:
            :obj:`hid.device` that has been connected to
        """
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

    def set_custom_frame(self, matrix, store=True, force_custom_effect=True):
        # TODO: enforce row/column lengths to  6 x 22 matrix
        """Set a custom frame on the device with a matrix of Colors.

        Args:
            matrix (:obj:`list` of :obj:`list` of
                  :obj:`chromarestserver.model.Color`): 6 x 22 matrix
                  of Color objects.
        """
        self.logger.debug('set_custom_frame matrix="%s"', matrix)

        if force_custom_effect:
            effect = matrix_effect_custom_frame(self.device, int(store))
            effect.run()

        for idx, row in enumerate(matrix):
            rgbs = [
                x
                for color in row
                for x in color.to_rgb()
            ]
            effect = set_custom_frame(self.device, idx, 0, len(row), rgbs=rgbs)
            effect.run()

    def set_custom_fill(self, color):
        """Set a custom frame of all one color.

        Args:
            color (:obj:`chromarestserver.model.Color`): Color object
        """
        matrix = [
            [color for i in range(22)]
            for j in range(6)
        ]
        return self.set_custom_frame(matrix)

    def set_led_effect(self, led, effect, persist=True):
        """Set effect for led type. This does not work on individual keys."""
        self.logger.debug('set_led_effect led="%s", effect="%s"', led, effect)
        effect = set_led_effect(self.device, int(persist), led, effect)
        effect.run()

    def set_matrix_none(self):
        """Clear out all LEDs for the device."""
        self.logger.debug('set_matrix_none')
        effect = matrix_effect_none(self.device)
        effect.run()

    def set_matrix_static(self, color):
        """Set the entire device to one color.

        Args:
            color (:obj:`chromarestserver.model.Color`): Color object
        """
        self.logger.debug('set_matrix_static color="%s"', color)

        r, g, b = color.to_rgb()
        effect = matrix_effect_static(self.device, r, g, b)
        effect.run()

    def set_matrix_spectrum(self):
        """Cycle through colors."""
        self.logger.debug('set_matrix_spectrum')
        effect = matrix_effect_spectrum(self.device)
        effect.run()

    def set_matrix_wave(self, left_to_right=True):
        """Rainbow wave."""
        self.logger.debug('set_matrix_wave left_to_right="%s"', left_to_right)
        if left_to_right:
            direction = 1
        else:
            direction = 2
        effect = matrix_effect_wave(self.device, direction)
        effect.run()

    def is_product_supported(self, product_id):
        """Abstract method that subclasses need to implement.

        Sub classes need to implement a `is_product_supported` method
        which takes an HID `product_id`, returning True if the product_id
        can be handled by the subclass or False if it can not.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("Subclass missing 'is_product_supported()'")


class KeyboardModel(USBModel):

    # list of all keyboard product_ids
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
        """Handler for Razer keyboard effects."""
        super(KeyboardModel, self).__init__()

    def is_product_supported(self, product_id):
        """Indicate if a Razer keyboard is supported or not.

        Args:
            product_id (int): The USB/HID product_id of the USB device
                being tested against.

        Returns:
            bool: True if `product_id` is supported or False
        """
        for name, value in iteritems(vars(KeyboardModel)):
            if not name.startswith('RAZER_'):
                continue
            self.logger.debug('value="%s", name="%s"', value, name)
            if int(product_id) == int(value):
                return True
        return False
