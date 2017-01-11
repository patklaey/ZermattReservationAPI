from flask import jsonify, request

from main import app, db, multi_auth
from DB.Reservation import Reservation

@app.route('/reservations', methods=["POST"])
@multi_auth.login_required
def post_reservations():
    for attribute in Reservation.get_required_attributes():
        if not attribute in request.json:
            return jsonify({'error': attribute + ' is required'}), 400
    data = request.json
    if 'description' in data:
        reservation = Reservation(data['title'], data['startTime'], data['endTime'],
                                  data['allDay'], data['userId'], data['description'])
    else:
        reservation = Reservation(data['title'], data['startTime'], data['endTime'],
                                  data['allDay'], data['userId'])
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
@multi_auth.login_required
def show_reservation(id):
    reservation = Reservation.query.get(id)
    if reservation is not None:
        return jsonify(reservation.to_dict())
    else:
        return jsonify({'error': 'notFound'})