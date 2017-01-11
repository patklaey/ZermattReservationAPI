from flask import Flask, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth

app = Flask(__name__)
app.config.from_pyfile('./config/config.py')
db = SQLAlchemy(app)
CORS(app)

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth('Bearer')
multi_auth = MultiAuth(basic_auth, token_auth)

from DB.User import User
from endpoints import reservation, user

@app.route('/')
def index():
    return "Hello, this is an API, Swagger documentation will follow here..."


@app.route('/token')
@basic_auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username, active=True).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


@token_auth.verify_token
def verify_token(token):
    user = User.verify_auth_token(token)
    if not user:
        return False
    g.user = user
    return True