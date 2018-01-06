import hid
import random

from future.utils import raise_from

from flask import g
from tinydb import Query, TinyDB

from chromarestserver import app
import chromarestserver.driver as driver


def bgr_to_rgb_list(bgr):
    """Convert a Blue Greed Red long integer (BGR) into an RGB list.

    Args:
        bgr (long): long integer representing a BGR color

    Returns:
        list of int: [r, g, b]
    """
    r = bgr & 255
    g = (bgr >> 8) & 255
    b = (bgr >> 16) & 255
    return [r, g, b]


def get_keyboard():
    """Open a handle to the USB keyboard.

    This caches the connection for the life of the flask request.

    Returns:
        Instance of an :obj:`hid.device` connected to a Razer keyboard.
    """

    device = getattr(g, '_usb_keyboard', None)
    if device is None:
        app.logger.info('opening usb keyboard')
        device = hid.device()
        # TODO: make the product programmable or dynamic based on
        # the 'usage' or something.
        try:
            device.open(vendor_id=0x1532, product_id=0x0209)
        except IOError as exc:
            if 'open failed' in str(exc):
                raise_from(
                    Exception(
                        ('Unable to open device: Make sure you run with'
                         ' privileges ex: "sudo -E flask run"')
                    ),
                    exc
                )
            raise

        g._usb_keyboard = device
    return device


def get_db():
    """Get a connection (cached) to a local database.

    Returns:
        Connection to local :obj:`tinydb.TinyDB` NoSQL database.
    """
    db = getattr(g, '_database', None)
    if db is None:
        app.logger.debug('opening database')
        db = g._database = TinyDB('chromarestserver.json')
    return db


def create_session(data):
    """Store a session in TinyDB based on a Razer SDK REST initialization.

    Args:
        data (dict): deserialized data from the initialization request.
            see: https://assets.razerzone.com/dev_portal/REST/html/index.html

    Returns:
        dict: dictionary that was written to :obj:`tinydb.TinyDB`
    """
    session_id = random.randint(100, 10000000)

    record = {
        'id': session_id,
        'app': data
    }

    db = get_db()
    db.insert(record)

    return record


def get_session(session_id):
    """Load a session from the local NoSQL database by id.

    Args:
        session_id (str): the session id

    Returns:
        dict: the session record stored in the TinyDB.
        None: if no session by that name exists
    """
    db = get_db()
    Session = Query()
    found = db.search(Session.id == session_id)
    if found:
        return found[0]
    return None


def delete_session(session_id):
    """Delete a session from the local NoSQL database by id.

    Args:
        session_id (str): the session id
    """
    db = get_db()
    Session = Query()
    db.remove(Session.id == session_id)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # ensure any (optional) caching middleware flushes changes
        app.logger.debug('closing tinydb database connection')
        db.close()

    kb = getattr(g, '_usb_keyboard', None)
    if kb is not None:
        app.logger.debug('closing usb keyboard connection')
        kb.close()


def create_effect(device, name, params=None):
    """Create and execute an effect on a Razer USB device.

    Args:
        device (:obj:`hid.device`): the USB device
        name (str): the effect name. ex: 'CHROMA_STATIC'
            see: https://assets.razerzone.com/dev_portal/REST/html/index.html
        params(list or dict or None): parameters for the effect
            see: https://assets.razerzone.com/dev_portal/REST/html/index.html
    """
    if 'CHROMA_NONE' == name:
        effect = driver.matrix_effect_none(device)
        effect.run()
    elif 'CHROMA_STATIC' == name:
        r, g, b = bgr_to_rgb_list(params['color'])
        effect = driver.matrix_effect_static(device, r, g, b)
        effect.run()
    elif 'CHROMA_CUSTOM' == name:
        rows = params
        effect = driver.matrix_effect_custom_frame(device, driver.NOSTORE)
        effect.run()
        for idx, row in enumerate(rows):

            rgbs = [
                x
                for col in row
                for x in bgr_to_rgb_list(col)
            ]
            effect = driver.set_custom_frame(
                        device, idx, 0, len(row), rgbs=rgbs)
            effect.run()
