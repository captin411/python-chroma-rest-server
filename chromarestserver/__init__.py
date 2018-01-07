import falcon

from chromarestserver.resource import (
    ChromaSdkResource,
    SessionRootResource,
    HeartBeatResource,
    KeyboardResource
)
from chromarestserver.model import (
    KeyboardModel,
    SessionModel
)

app = falcon.API()

usb_keyboard = KeyboardModel()
session = SessionModel()

chromasdk = ChromaSdkResource(session=session)
session = SessionRootResource(session=session)
heartbeat = HeartBeatResource(session=session)
keyboard = KeyboardResource(session=session, usb=usb_keyboard)

app.add_route('/razer/chromasdk', chromasdk)
app.add_route('/{session_id}/chromasdk', session)
app.add_route('/{session_id}/chromasdk/heartbeat', heartbeat)
app.add_route('/{session_id}/chromasdk/keyboard', keyboard)
