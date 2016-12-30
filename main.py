from flask import Flask, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
app.config.from_envvar('APPLICATION_SETTINGS')
db = SQLAlchemy(app)
CORS(app)
auth = HTTPBasicAuth()

from DB.User import User
from DB.Reservation import Reservation


@app.route('/')
def index():
    return "Hello, this is an API, Swagger documentation will follow here..."


@app.route('/users')
@auth.login_required
def show_entries():
    users = User.query.all()
    userDict = []
    for user in users:
        userDict.append(user.to_dict())
    return jsonify(userDict)


@app.route('/users/<int:id>')
@auth.login_required
def show_user(id):
    user = User.query.get(id)
    if user is not None:
        return jsonify(user.to_dict())
    else:
        return jsonify({'error': 'notFound'})


@app.route('/reservations', methods=["POST"])
@auth.login_required
def post_reservations():
    for attribute in Reservation.get_required_attributes():
        if not attribute in request.json:
            return jsonify({'error': attribute + ' is required'}), 400
    data = request.json
    reservation = Reservation(data['title'], data['startTime'], data['endTime'],
                              data['allDay'], data['userId'], data['description'])
    db.session.add(reservation)
    db.session.commit()
    return jsonify({"id": reservation.id}), 201


@app.route('/reservations', methods=["GET"])
def get_reservations():
    all_reservations = Reservation.query.all()
    reservation_dict = []
    for reservation in all_reservations:
        reservation_dict.append(reservation.to_dict())
    return jsonify(reservation_dict)


@app.route('/reservations/<int:id>')
@auth.login_required
def show_reservation(id):
    reservation = Reservation.query.get(id)
    if reservation is not None:
        return jsonify(reservation.to_dict())
    else:
        return jsonify({'error': 'notFound'})


@app.route('/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True
