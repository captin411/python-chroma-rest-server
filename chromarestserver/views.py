import time

from flask import jsonify, request, url_for

from chromarestserver import app
import chromarestserver.model as model


@app.route('/razer/chromasdk', methods=['POST'])
def initialize():
    """Initialize a Chroma SDK for a spefic custom app.

    See: https://assets.razerzone.com/dev_portal/REST/html/index.html
    """
    data = request.get_json(force=True)
    session = model.create_session(data)

    resp = jsonify({
        'sessionid': session['id'],
        'session': session['id'],
        'uri': url_for(
                    'session_root',
                    session_id=session['id'],
                    _external=True)
    })
    resp.status_code = 200
    return resp


@app.route('/razer/chromasdk', methods=['GET'])
def info():
    # TODO: find out what actually goes here -- not in the docs
    resp = jsonify({
        'version': '2.7'
    })
    resp.status_code = 200
    return resp


@app.route('/<int:session_id>/chromasdk/heartbeat', methods=['PUT', 'POST'])
def heartbeat(session_id):
    resp = jsonify({
        'tick': time.time()
    })
    resp.status_code = 200
    return resp


@app.route('/<int:session_id>/chromasdk', methods=['GET'])
def session_root(session_id):
    app.logger.info('loading session_id="%s"', session_id)

    session = model.get_session(session_id)
    if session:
        resp = jsonify({
            'result': 0,
            'info': session
        })
        resp.status_code = 200
    else:
        resp = jsonify({
            'result': 1168
        })
        resp.status_code = 404
    return resp


@app.route('/<int:session_id>/chromasdk', methods=['DELETE'])
def uninitialize(session_id):
    app.logger.info('deleting session_id="%s"', session_id)

    model.delete_session(session_id)

    resp = jsonify({'result': 0})
    resp.status_code = 200
    return resp


@app.route('/<int:session_id>/chromasdk/keyboard', methods=['PUT', 'POST'])
def keyboard(session_id):

    ## 0.5 seconds on high throughput animation
    # session = model.get_session(session_id)
    # if not session:
    #     resp = jsonify({
    #         'result': 1168,
    #         'info': session
    #     })
    #     resp.status_code = 404

    data = request.get_json(force=True)

    # coerce the may-be-a-list data structure into a list
    # to make processing unified
    effects = data.get('effects', [data])

    device = model.get_keyboard()

    for item in effects:
        name = item.get('effect')
        params = item.get('param')
      
        model.create_effect(device, name, params)

    resp = jsonify({'result': 0})
    resp.status_code = 200
    return resp
