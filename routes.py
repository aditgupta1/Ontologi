from flask import flask
app = Flask(__name__)

from app import app

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"
