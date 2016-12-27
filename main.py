from flask import Flask, session, escape, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_envvar('APPLICATION_SETTINGS')
db = SQLAlchemy(app)

app.secret_key = '\x03D5\x0e\x89\xa2\xf3s\x13\xfa\x8b\x7f\x82\x16\x87_\xaf\x9c\x18\xb2G\x89\xfa^'

from DB.User import User
from DB.Reservation import Reservation


@app.route('/')
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'


@app.route('/users')
def show_entries():
    users = User.query.all()
    userDict = []
    for user in users:
        userDict.append(user.to_dict())
    return jsonify(userDict)


@app.route('/users/<int:id>')
def show_user(id):
    user = User.query.get(id)
    if user is not None:
        return jsonify(user.to_dict())
    else:
        return jsonify({'error': 'notFound'})


@app.route('/reservations')
def show_reservations():
    reservations = Reservation.query.all()
    reservatio_dict = []
    for reservation in reservations:
        reservatio_dict.append(reservation.to_dict())
    return jsonify(reservatio_dict)


@app.route('/reservations/<int:id>')
def show_reservation(id):
    reservation = Reservation.query.get(id)
    if reservation is not None:
        return jsonify(reservation.to_dict())
    else:
        return jsonify({'error': 'notFound'})
