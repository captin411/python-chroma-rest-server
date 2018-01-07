import falcon
import hid
import logging
import time
import random

from tinydb import Query, TinyDB

from chromarestserver.model import bgr_to_rgb_list
import chromarestserver.driver as driver


class SessionEngine():
    def __init__(self):
        self.logger = logging.getLogger()
        self._db = None

    @property
    def connection(self):
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

        self.connection.insert(record)

        return record

    def load(self, session_id):
        self.logger.info('loading session_id="%s"', session_id)
        db = self.connection
        Session = Query()
        found = db.search(Session.id == session_id)
        if found:
            return found[0]
        return None

    def delete(self, session_id):
        self.logger.info('deleting session_id="%s"', session_id)
        db = self.connection
        Session = Query()
        db.remove(Session.id == session_id)


class DeviceEngine():

    RAZER_VENDOR_ID = 0x1532

    def __init__(self):
        self.logger = logging.getLogger()
        self._keyboard = None

    @property
    def keyboard(self):
        if self._keyboard is None:
            self.logger.debug('connecting to USB keyboard')
            for info in hid.enumerate():
                if (info['vendor_id'] == DeviceEngine.RAZER_VENDOR_ID
                        and info['usage'] == 6):
                    self.logger.info('found keyboard info="%s"', info)
                    device = hid.device()
                    device.open(
                        vendor_id=info['vendor_id'],
                        product_id=info['product_id']
                    )
                    self._keyboard = device
                    break

        if self._keyboard is None:
            raise RuntimeError('No Razer keyboards found')

        return self._keyboard

    def keyboard_effect(self, name, params=None):
        device = self.keyboard
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


class ChromaSdkResource():

    def __init__(self, session):
        self.logger = logging.getLogger()
        self.session = session

    def on_get(self, req, resp):
        resp.media = {
            'version': '2.7'
        }
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp):
        data = req.media

        session = self.session.create(data)

        resp.media = {
            'sessionid': session['id'],
            'session': session['id'],
            'uri': '{}://{}:{}/{}/chromasdk'.format(
                req.scheme,
                req.host,
                req.port,
                falcon.uri.encode_value(str(session['id']))
            )
        }
        resp.status = falcon.HTTP_200


class HeartBeatResource():

    def __init__(self, session):
        self.logger = logging.getLogger()
        self.session = session

    def on_post(self, req, resp, session_id):
        resp.media = {
            'tick': time.time()
        }
        resp.status = falcon.HTTP_200

    def on_put(self, req, resp, session_id):
        return self.on_post(req, resp, session_id)


class SessionRootResource():

    def __init__(self, session):
        self.logger = logging.getLogger()
        self.session = session

    def on_get(self, req, resp, session_id):
        session = self.session.load(session_id)
        if session:
            resp.media = {
                'result': 0,
                'info': session
            }
            resp.status = falcon.HTTP_200
        else:
            resp.media = {
                'result': 1168
            }
            resp.status = falcon.HTTP_404

    def on_delete(self, req, resp, session_id):
        self.session.delete(session_id)
        resp.media = {'result': 0}
        resp.status = 200


class KeyboardResource():

    def __init__(self, session, usb):
        self.logger = logging.getLogger()
        self.session = session
        self.usb = usb

    def on_post(self, req, resp, session_id):
        data = req.media

        # coerce the may-be-a-list data structure into a list
        # to make processing unified
        effects = data.get('effects', [data])

        for item in effects:
            name = item.get('effect')
            params = item.get('param')

            try:
                self.usb.keyboard_effect(name, params)
                resp.media = {
                    'result': 0
                }
                resp.status = falcon.HTTP_200
            except IOError as exc:
                # device must have disconnected
                # https://assets.razerzone.com/dev_portal/REST/html/_rz_errors_8h.html
                self.usb._keyboard = None
                resp.media = {
                    'result': 1167
                }
            except RuntimeError as exc:
                # no device found
                # https://assets.razerzone.com/dev_portal/REST/html/_rz_errors_8h.html
                self.usb._keyboard = None
                resp.media = {
                    'result': 4319
                }

    def on_put(self, req, resp, session_id):
        return self.on_post(req, resp, session_id)
