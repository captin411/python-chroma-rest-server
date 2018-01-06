from flask import Flask
app = Flask(__name__)

import chromarestserver.model
import chromarestserver.views
