# -*- coding: utf-8 -*-
"""Falcon REST server resources."""
import falcon
import logging
import time

from chromarestserver.model import Color


class ChromaSdkResource():

    def __init__(self, session):
        """Falcon resource for session management.

        Args:
            session (:obj:`chromarestserver.model.SessionModel`): The
                model implementing how to handle session management
                details.
        """
        self.logger = logging.getLogger()
        self.session = session

    def on_get(self, req, resp):
        """Emulate version information."""
        resp.media = {
            'version': '2.7'
        }
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp):
        """Emulate session creation."""
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
        """Falcon resource for session heartbeat.

        Args:
            session (:obj:`chromarestserver.model.SessionModel`): The
                model implementing how to handle session management
                details.
        """
        self.logger = logging.getLogger()
        self.session = session

    def on_post(self, req, resp, session_id):
        """Emulate heartbeat for session keepalive."""
        resp.media = {
            'tick': time.time()
        }
        resp.status = falcon.HTTP_200

    def on_put(self, req, resp, session_id):
        """Emulate heartbeat for session keepalive."""
        return self.on_post(req, resp, session_id)


class SessionRootResource():

    def __init__(self, session):
        """Falcon resource for instances of application sessions.

        Args:
            session (:obj:`chromarestserver.model.SessionModel`): The
                model implementing how to handle session management
                details.
        """
        self.logger = logging.getLogger()
        self.session = session

    def on_get(self, req, resp, session_id):
        """Emulate session info retrieval."""
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
        """Emulate session deletion."""
        self.session.delete(session_id)
        resp.media = {'result': 0}
        resp.status = 200


class KeyboardResource():

    def __init__(self, session, usb):
        """Falcon resource for keyboard effects

        Args:
            session (:obj:`chromarestserver.model.SessionModel`): Handler
                for managing session managent.
            usb (:obj:`chromarestserver.model.KeyboardModel`): Handler
                for communicating effects to Razer Chroma USB keyboards.
        """
        self.logger = logging.getLogger()
        self.session = session
        self.usb = usb

    def on_post(self, req, resp, session_id):
        """Create a keyboard effect for later use."""
        data = req.media

        # coerce the may-be-a-list data structure into a list
        # to make processing unified
        effects = data.get('effects', [data])

        for item in effects:
            name = item.get('effect')
            params = item.get('param')

            try:
                self.logger.debug('effect name="%s", params="%s"',
                                  name, params)
                if 'CHROMA_NONE' == name:
                    self.usb.set_matrix_none()
                elif 'CHROMA_STATIC' == name:
                    color = Color.from_long_bgr(params['color'])
                    self.usb.set_matrix_static(color)
                elif 'CHROMA_CUSTOM' == name:
                    matrix = [
                        list(map(Color.from_long_bgr, row))
                        for row in params
                    ]
                    self.usb.set_custom_frame(matrix)
                resp.media = {'result': 0}
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
        """Execute a keyboard effect immediately."""
        return self.on_post(req, resp, session_id)
