from flask import jsonify, request
from DB.User import User
from main import app, db
from DB.Reservation import Reservation
from dateutil.parser import parse
from flask_jwt_extended import jwt_required, get_jwt_identity
import pytz

@app.route('/reservations', methods=["GET"])
def get_reservations():
    all_reservations = Reservation.query.all()
    reservation_dict = []
    for reservation in all_reservations:
        reservation_dict.append(reservation.to_dict())
    return jsonify(reservation_dict)


@app.route('/reservations/<int:id>', methods=["GET"])
@jwt_required
def show_reservation(id):
    reservation = Reservation.query.get(id)
    if reservation is not None:
        return jsonify(reservation.to_dict())
    else:
        return jsonify({'error': 'Event not found'})


@app.route('/reservations', methods=["POST"])
@jwt_required
def post_reservations():
    for attribute in Reservation.get_required_attributes():
        if not attribute in request.json:
            return jsonify({'error': '\'' + attribute + '\' is required'}), 400
    data = request.json
    user_id = get_jwt_identity()

    try:
        start_date = parse(data['startTime'])
    except ValueError:
        return jsonify({"error" : "Invalid date format for startTime"}), 400

    try:
        end_date = parse(data['endTime'])
    except ValueError:
        return jsonify({"error" : "Invalid date format for endTime"}), 400

    description = ""
    if 'description' in data:
        description = data['description']

    try:
        reservation = Reservation(data['title'], start_date, end_date, data['allDay'], user_id, description)
    except ValueError as error:
        if error.message == Reservation.END_BEFORE_START_ERROR_MESSAGE:
            return jsonify({"error" : "Start date cannot be after end date"}), 409
        else:
            # Log error
            print error
            return jsonify({"error" : "Cannot create reservation"}), 400

    try:
        db.session.add(reservation)
        db.session.commit()
        return jsonify({"id": reservation.id}), 201
    except Exception as error:
        db.session.rollback()
        # Log error
        return jsonify({"error": "Failed to add reservation"}), 500


@app.route('/reservations/<int:id>', methods=["PUT", "PATCH"])
@jwt_required
def update_reservation(id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    reservation = Reservation.query.get(id)

    if not current_user.admin or reservation.userId != user_id_from_token:
        return jsonify({'error': 'Operation not permitted'}), 403

    if not reservation:
        return jsonify({'error': 'Reservation with id ' + id + ' not found'}), 404

    if 'endTime' in request.json and 'startTime' in request.json:
        start_time = parse(request.json["startTime"])
        end_time = parse(request.json["endTime"])
        if end_time < start_time:
            return jsonify({"error" : Reservation.END_BEFORE_START_ERROR_MESSAGE}), 409

    try:
        for attribute in request.json:
            if attribute in Reservation.get_all_attributes():
                if attribute == "endTime" or attribute == "startTime":
                    try:
                        date_value = parse(request.json[attribute])

                        if date_value.tzinfo is None or date_value.tzinfo.utcoffset(date_value) is None:
                            date_value = pytz.utc.localize(date_value)
                        elif date_value.tzinfo != pytz.utc:
                            date_value = date_value.replace(tzinfo=date_value.tzinfo).astimezone(pytz.utc)

                        if attribute == "endTime" and not 'startTime' in request.json:
                            if date_value < reservation.startTime:
                                return jsonify({"error" : Reservation.END_BEFORE_START_ERROR_MESSAGE}), 409

                        if attribute == "startTime" and not 'endTime' in request.json:
                            if reservation.endTime < date_value:
                                return jsonify({"error" : Reservation.END_BEFORE_START_ERROR_MESSAGE}), 409

                        setattr(reservation, attribute, date_value)
                    except ValueError:
                        return jsonify({"error" : "Invalid date format for " + attribute}), 400
                else:
                    setattr(reservation, attribute, request.json[attribute])
        db.session.commit()
        return '', 204
    except Exception as error:
        db.session.rollback()
        # Log erro
        print error
        return jsonify({"error": "Failed to update reservation"}), 500


@app.route('/reservations/<int:id>', methods=["DELETE"])
@jwt_required
def remove_reservation(id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    reservation = Reservation.query.get(id)

    if not current_user.admin or reservation.userId != user_id_from_token:
        return jsonify({'error': 'Operation not permitted'}), 403

    if not reservation:
        return jsonify({'error': 'Reservation with id ' + id + ' not found'}), 404

    try:
        db.session.delete(reservation)
        db.session.commit()
        return '', 204
    except Exception as error:
        db.session.rollback()
        print error
        return jsonify({"error": "Failed to delete reservation"}), 500

