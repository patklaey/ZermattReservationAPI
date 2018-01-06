import atexit
from flask import Flask, jsonify, g, request, make_response
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, set_access_cookies, jwt_required, unset_jwt_cookies
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logging.basicConfig()

app = Flask(__name__)
app.config.from_pyfile('./config/config.py')
db = SQLAlchemy(app)
CORS(app, supports_credentials=True)
migrate = Migrate(app, db)

jwt = JWTManager(app)

from tasks.next_reservation_check import check_all_users
from DB.User import User
from endpoints import reservation, user

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(check_all_users,'interval', hours=4)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def index():
    return "Hello, this is an API, Swagger documentation will follow here..."


@app.route('/token')
def get_auth_token():
    if not request.authorization:
        response = make_response(jsonify({'error':'Login required'}))
        response.headers.set('WWW-Authenticate', 'Basic realm="patklaey.ch"')
        return response, 401

    if not verify_password(request.authorization.username, request.authorization.password):
        response = jsonify({'error':'Invalid username or password'})
        return response, 401

    token = g.user.generate_auth_token()
    response = jsonify({'token': token})
    set_access_cookies(response, token)
    return response, 200


def verify_password(username, password):
    user = User.query.filter_by(username=username, active=True).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


@app.route('/logout', methods=['POST'])
def logout():
    resp = jsonify({'logout': True})
    unset_jwt_cookies(resp)
    return resp, 200
