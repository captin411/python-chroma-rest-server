# thanks to the openrazer project for most of this information!
# https://github.com/openrazer/openrazer/tree/master/driver
import functools
import random
import time
import logging

logger = logging.getLogger()

REPORT_ID = 0x00

# led state
OFF = 0x00
ON = 0x01

# led storage options
NOSTORE = 0x00
VARSTORE = 0x01

# led definitions
SCROLL_WHEEL_LED = 0x01
BATTERY_LED = 0x03
LOGO_LED = 0x04
BACKLIGHT_LED = 0x05
MACRO_LED = 0x07
GAME_LED = 0x08
RED_PROFILE_LED = 0x0C
GREEN_PROFILE_LED = 0x0D
BLUE_PROFILE_LED = 0x0E

# led effect definitions
LED_STATIC = 0x00
LED_BLINKING = 0x01
LED_PULSATING = 0x02
LED_SPECTRUM_CYCLING = 0x04

# report responses
RAZER_CMD_BUSY = 0x01
RAZER_CMD_SUCCESSFUL = 0x02
RAZER_CMD_FAILURE = 0x03
RAZER_CMD_TIMEOUT = 0x04
RAZER_CMD_NOT_SUPPORTED = 0x05


def usleep_range(min_usec, max_usec):
    """Sleep randomly between min/max microseconds.

    Args:
        min_usec (int): minimum number of microseconds to sleep
        max_usec (int): maximum number of microseconds to sleep
    """
    sec = random.randint(min_usec, max_usec) / 1000000.0
    logger.debug('sleeping for sec="%s"', sec)
    time.sleep(sec)


def clamp(n, smallest, largest):
    """Ensure 'n' is no smaller or larger then a certain range.

    If the number is smaller than the range it will be returned as
    the smallest.

    If the number is larger than largest it will be returned as the
    largest.

    Args:
        n (int): integer to inspect
        smallest (int): no smaller than this is allowed
        largest (int): no larger than this is allowed

    Returns:
        int: the "clamped" input
    """
    return max(smallest, min(n, largest))


def clamp255(n):
    """Ensure a number is between 0-255 (inclusive).

    Args:
        n (int): integer to inspect

    Returns:
        int: the "clamped" input
    """
    return clamp(n, 0, 255)


class RzEffect():

    REPORT_LEN = 90

    def __init__(self, device, command, subcommand, tx_id=0x3F, args=None):
        """Information for the creation of a Razer Chroma USB wire command.

        Args:
            device (:obj:`hid.device`): the connected USB device
            command (int): the Razer protocol command as an integer
            subcommand (int): the Razer protocol subcommand as an integer
            tx_id (optional, int): the transaction id
            args (optional, list): any parameters needed for the `command`
        """
        if args is None:
            args = []

        self.device = device
        self.command = clamp255(command)
        self.subcommand = clamp255(subcommand)
        self.tx_id = clamp255(tx_id)
        self.args = [clamp255(x) for x in args]

    def run(self):
        """Send the command the the USB device."""
        logger.debug('Running command="%s"', repr(self))

        request = self.to_feature_report()
        logger.debug(
            'request="%s", length="%s"',
            ' '.join(['%0.2X' % x for x in request]), len(request))

        written = self.device.send_feature_report([REPORT_ID] + request)
        logger.debug('bytes written="%s"', written)
        if written == -1:
            raise IOError('Unable to write to USB device')

        if written != len(request)+1:
            raise ValueError('Invalid request: {}'.format(repr(self)))

        usleep_range(900, 1000)

        response = self.device.get_feature_report(REPORT_ID, written)
        logger.debug(
            'response="%s", length="%s"',
            ' '.join(['%0.2X' % x for x in response]), len(response))

        if request[:90] != response[:90]:
            raise ValueError('Invalid response: {}'.format(repr(response)))

        if response[-1] != 2:
            logger.error('response is {}'.format(response[0]))

    def to_feature_report(self):
        """Turn this into a list of ints to send over the USB connection.

        Returns: list of int suitable to send to the HID
                 send_feature_report method
        """

        arg_count = len(self.args)

        # https://github.com/openrazer/openrazer/wiki/Reverse-Engineering-USB-Protocol
        command_bytes = [0] * RzEffect.REPORT_LEN
        command_bytes[0] = 0x00  # PC -> device
        command_bytes[2:5] = [0x00, 0x00, 0x00]  # reserved bytes (idx 2-4)
        command_bytes[5] = arg_count
        command_bytes[6] = self.command
        command_bytes[7] = self.subcommand
        command_bytes[8:8+arg_count] = self.args

        crc_of = command_bytes[2:88]
        logger.debug('calculating crc_of="%s"', crc_of)
        crc = [functools.reduce(int.__xor__, command_bytes[2:88])]
        command_bytes[-2] = crc[0]

        return command_bytes

    def __repr__(self):
        return ('RzEffect(device={}, command={}, subcommand={}, tx_id={}, '
                'args={})').format(
            repr(self.device), repr(self.command), repr(self.subcommand),
            repr(self.tx_id), repr(self.args)
        )


def set_custom_frame(dev, row, col_start=0, col_end=21, rgbs=None):
    if rgbs is None:
        rgbs = []

    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x0B,
        args=[
            0xFF,
            clamp(row, 0, 6),
            clamp(col_start, 0, 21),
            clamp(col_end, 0, 21)
        ] + rgbs
    )


def set_led_blinking(dev, variable_storage, led_id):
    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x04,
        args=[
            variable_storage,
            led_id,
            0x05,
            0x05
        ]
    )


def set_led_brightness(dev, storage, led, level):
    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x03,
        args=[
            storage,
            led,
            level
        ]
    )


def set_led_effect(dev, variable_storage, led_id, effect):
    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x02,
        args=[
            variable_storage,
            led_id,
            clamp(effect, 0, 5)
        ]
    )


def set_led_state(dev, variable_storage, led_id, led_state):
    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x00,
        args=[
            variable_storage,
            led_id,
            led_state
        ]
    )


def matrix_effect_none(dev):
    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x0A,
        args=[
            0x00
        ]
    )


def matrix_effect_custom_frame(dev, variable_storage):
    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x0A,
        args=[
            0x05,
            variable_storage
        ]
    )


def matrix_effect_wave(dev, direction=1):
    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x0A,
        args=[
            0x01,
            clamp(direction, 1, 2)
        ]
    )


def matrix_effect_spectrum(dev):
    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x0A,
        args=[LED_SPECTRUM_CYCLING]
    )


def matrix_effect_static(dev, r=0, g=0, b=0):
    return RzEffect(
        device=dev,
        command=0x03,
        subcommand=0x0A,
        args=[0x06, clamp255(r), clamp255(g), clamp255(b)]
    )


def extended_matrix_brightness(dev, storage, led, level):
    return RzEffect(
        device=dev,
        command=0x0f,
        subcommand=0x04,
        args=[
            storage,
            led,
            level
        ]
    )
