# python-chroma-rest-server

The official Chroma SDK REST server does not run on OSX or Linux.

This one does.

So far only tested with the Razer BlackWidow Chroma V2 on OSX

# install

```
git clone https://github.com/captin411/python-chroma-rest-server.git
cd python-chroma-rest-server
pip install -e .
```

# run

```
# run with wsgiref
sudo python run.py

# or run with gunicorn if you have that installed
sudo gunicorn chromarestserver:app --bind 127.0.0.1:54235
```

# use

```
curl -X PUT \
  -H 'Content-type: application/json'
  -d '{"effect":"CHROMA_NONE"}' \
  http://127.0.0.1:54235/1234/chromasdk/keyboard

curl -X PUT \
  -H 'Content-type: application/json'
  -d '{"effect":"CHROMA_STATIC","param":{"color":255}}' \
  http://127.0.0.1:54235/1234/chromasdk/keyboard
```

# links

## official API docs

https://assets.razerzone.com/dev_portal/REST/html/index.html

## low level details of the razer protocol

https://github.com/openrazer/openrazer/tree/master/driver

## client for rest api

https://github.com/chroma-sdk/chroma-python
