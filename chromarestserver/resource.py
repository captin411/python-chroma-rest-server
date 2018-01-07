import falcon
import logging
import time


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
                self.usb.effect(name, params)
                resp.media = {
                    'result': 0
                }
                resp.status = falcon.HTTP_200
            except IOError as exc:
                # device must have disconnected
                # https://assets.razerzone.com/dev_portal/REST/html/_rz_errors_8h.html
                self.usb.device = None
                resp.media = {
                    'result': 1167
                }
            except RuntimeError as exc:
                # no device found
                # https://assets.razerzone.com/dev_portal/REST/html/_rz_errors_8h.html
                self.usb.device = None
                resp.media = {
                    'result': 4319
                }

    def on_put(self, req, resp, session_id):
        return self.on_post(req, resp, session_id)
