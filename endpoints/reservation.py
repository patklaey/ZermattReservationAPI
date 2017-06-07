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
    return jsonify(reservation_dict), 200


@app.route('/reservations/<int:id>', methods=["GET"])
@jwt_required
def show_reservation(id):
    reservation = Reservation.query.get(id)
    if reservation is not None:
        return jsonify(reservation.to_dict()), 200
    else:
        return jsonify({'error': {'msg' : 'Event not found', 'code' : 1, 'info' : id }}), 404


@app.route('/reservations', methods=["POST"])
@jwt_required
def post_reservations():
    for attribute in Reservation.get_required_attributes():
        if not attribute in request.json:
            return jsonify({'error': {'msg' : '\'' + attribute + '\' is required', 'code' : 2, 'info' : attribute}}), 400
    data = request.json
    user_id = get_jwt_identity()

    try:
        start_date = parse(data['startTime'])
    except ValueError:
        return jsonify({"error" : { 'msg' : "Invalid date format for startTime", 'code' : 3 }}), 400

    try:
        end_date = parse(data['endTime'])
    except ValueError:
        return jsonify({"error" : { 'msg' : "Invalid date format for endTime", 'code' : 4 }}), 400

    description = ""
    if 'description' in data:
        description = data['description']

    all_current_events = Reservation.query.all()
    if is_overlapping(start_date, end_date, all_current_events):
        return jsonify({"error": { 'msg' : "Overlapping dates", 'code' : 5 }}), 409


    try:
        reservation = Reservation(data['title'], start_date, end_date, data['allDay'], user_id, description)
    except ValueError as error:
        if error.message == Reservation.END_BEFORE_START_ERROR_MESSAGE:
            return jsonify({"error" : { 'msg' : "Start date cannot be after end date", 'code' : 6 }}), 409
        else:
            # Log error
            print error
            return jsonify({"error" : { 'msg' : "Cannot create reservation", 'code' : 7 }}), 400

    try:
        db.session.add(reservation)
        db.session.commit()
        return jsonify({"id": reservation.id, "userId": user_id}), 201
    except Exception as error:
        db.session.rollback()
        # Log error
        return jsonify({"error": { 'msg' : 'Failed to add reservation', 'code' : 8 }}), 500


@app.route('/reservations/<int:id>', methods=["PUT", "PATCH"])
@jwt_required
def update_reservation(id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    reservation = Reservation.query.get(id)

    if not current_user.admin and reservation.userId != user_id_from_token:
        return jsonify({'error': { 'msg' : 'Operation not permitted', 'code' : 9 }}), 403

    if not reservation:
        return jsonify({'error': { 'msg' : 'Reservation with id ' + id + ' not found', 'code' : 10 }}), 404

    if 'endTime' in request.json and 'startTime' in request.json:
        start_time = parse(request.json["startTime"])
        end_time = parse(request.json["endTime"])
        if end_time < start_time:
            return jsonify({"error" : { 'msg' : Reservation.END_BEFORE_START_ERROR_MESSAGE, 'code' : 11 }}), 409

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
                                return jsonify({"error" : { 'msg' : Reservation.END_BEFORE_START_ERROR_MESSAGE, 'code' : 11 }}), 409

                        if attribute == "startTime" and not 'endTime' in request.json:
                            if reservation.endTime < date_value:
                                return jsonify({"error" : { 'msg' : Reservation.END_BEFORE_START_ERROR_MESSAGE, 'code' : 11 }}), 409

                        setattr(reservation, attribute, date_value)
                    except ValueError:
                        return jsonify({"error" : { 'msg' : "Invalid date format for " + attribute, 'code' : 12, 'info' : attribute }}), 400
                else:
                    setattr(reservation, attribute, request.json[attribute])
        db.session.commit()
        return '', 204
    except Exception as error:
        db.session.rollback()
        # Log erro
        print error
        return jsonify({"error": { 'msg' : "Failed to update reservation", 'code' : 13 }}), 500


@app.route('/reservations/<int:id>', methods=["DELETE"])
@jwt_required
def remove_reservation(id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    reservation = Reservation.query.get(id)

    if not current_user.admin and reservation.userId != user_id_from_token:
        return jsonify({'error': { 'msg' : 'Operation not permitted', 'code' : 14 }}), 403

    if not reservation:
        return jsonify({'error': { 'msg' : 'Reservation with id ' + id + ' not found', 'code' : 15, 'info' : id }}), 404

    try:
        db.session.delete(reservation)
        db.session.commit()
        return '', 204
    except Exception as error:
        db.session.rollback()
        print error
        return jsonify({"error": { 'msg' : "Failed to delete reservation", 'code' : 16 }}), 500


def is_overlapping(start_date, end_date, all_events):
    for event in all_events:
        if overlaps_with_event(start_date, end_date, event) or wraps_event(start_date, end_date, event):
            return True

    return False


def overlaps_with_event(start_date, end_date, event):
    if start_date > event.startTime and start_date < event.endTime:
        return True
    if end_date > event.startTime and end_date < event.endTime:
        return True
    if start_date == event.startTime or end_date == event.endTime:
        return True
    return False


def wraps_event(start_date, end_date, event):
    if start_date < event.startTime and end_date > event.endTime:
        return True
    return False
