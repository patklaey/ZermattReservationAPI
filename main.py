from flask import Flask, session, escape, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_envvar('APPLICATION_SETTINGS')
db = SQLAlchemy(app)

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


@app.route('/reservations', methods=["GET", "POST"])
def reservations():
    if request.method == "GET":
        return show_reservations()
    elif request.method == "POST":
        for attribute in Reservation.get_required_attributes():
            if not attribute in request.json:
                return jsonify({'error': attribute + ' is required'}), 400
        data = request.json
        reservation = Reservation(data['title'], data['description'], data['start_date'], data['end_date'],
                                  data['all_day'], data['user_id'])
        db.session.add(reservation)
        db.session.commit()
        return jsonify({"id": reservation.id}), 201
    else:
        return jsonify({"error": "method not allowed"})


def show_reservations():
    all_reservations = Reservation.query.all()
    reservation_dict = []
    for reservation in all_reservations:
        reservation_dict.append(reservation.to_dict())
    return jsonify(reservation_dict)


@app.route('/reservations/<int:id>')
def show_reservation(id):
    reservation = Reservation.query.get(id)
    if reservation is not None:
        return jsonify(reservation.to_dict())
    else:
        return jsonify({'error': 'notFound'})
