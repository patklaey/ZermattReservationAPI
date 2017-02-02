from flask import Flask, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_jwt_extended import JWTManager, set_access_cookies

app = Flask(__name__)
app.config.from_pyfile('./config/config.py')
db = SQLAlchemy(app)
CORS(app, supports_credentials=True)

basic_auth = HTTPBasicAuth()
jwt = JWTManager(app)

from DB.User import User
from endpoints import reservation, user

@app.route('/')
def index():
    return "Hello, this is an API, Swagger documentation will follow here..."


@app.route('/token')
@basic_auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    response = jsonify({'token': token})
    set_access_cookies(response, token)
    return response, 200


@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username, active=True).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True