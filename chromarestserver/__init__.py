import falcon

import chromarestserver.views as views

app = falcon.API()

usb_engine = views.DeviceEngine()
session_engine = views.SessionEngine()

chromasdk = views.ChromaSdkResource(session=session_engine)
session = views.SessionRootResource(session=session_engine)
heartbeat = views.HeartBeatResource(session=session_engine)
keyboard = views.KeyboardResource(session=session_engine, usb=usb_engine)

app.add_route('/razer/chromasdk', chromasdk)
app.add_route('/{session_id}/chromasdk', session)
app.add_route('/{session_id}/chromasdk/heartbeat', heartbeat)
app.add_route('/{session_id}/chromasdk/keyboard', keyboard)
