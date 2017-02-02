from flask import jsonify, request, g

from main import app, db
from DB.Reservation import Reservation

from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route('/reservations', methods=["POST"])
@jwt_required
def post_reservations():
    for attribute in Reservation.get_required_attributes():
        if not attribute in request.json:
            return jsonify({'error': attribute + ' is required'}), 400
    data = request.json
    user_id = get_jwt_identity()
    if 'description' in data:
        reservation = Reservation(data['title'], data['startTime'], data['endTime'],
                                  data['allDay'], user_id, data['description'])
    else:
        reservation = Reservation(data['title'], data['startTime'], data['endTime'],
                                  data['allDay'], user_id)
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
@jwt_required
def show_reservation(id):
    reservation = Reservation.query.get(id)
    if reservation is not None:
        return jsonify(reservation.to_dict())
    else:
        return jsonify({'error': 'Event not found'})
