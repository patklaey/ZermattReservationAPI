# coding=utf-8
import smtplib
import copy
from email.mime.text import MIMEText
from main import app, db
from flask import jsonify, request
from DB.User import User
from flask_jwt_extended import jwt_required, get_jwt_identity

MAIL_MESSAGES = {
    'de': {
        'registration' : {
            'subject': "Registration auf zermatt.patklaey.ch",
            'message': "Hallo {}\n\nVielen Dank für die Registrierung, dein Konto wird bald aktiviert. Du wirst ein weiteres Mail mit der Aktivierungsbestäting für dein Konto erhalten.\n\nZermatt Reservationen"
        },
        'activation' : {
            'subject' : "Konto auf zermatt.patklaey.ch aktiviert",
            'message' : "Hallo {}\n\nDein Konto wurde soeben von einem Administrator aktiviert. Du kannst dich ab sofort auf https://zermatt.patklaey.ch einloggen und reservationen tätigen.\n\nViel Spass.\n\nZermatt Reservationen"
        }
    },
    'de-be': {
        'registration' : {
            'subject': "Registration uf zermatt.patklaey.ch",
            'message': "Hallo {}\n\nMerci viu mau für d Registrierig, dis Konto wird gli aktiviert. Du wirsch es witers Mail mit dr Aktivierigsbestätigung für dis Konto becho.\n\nZermatt Reservatione"
        },
        'activation' : {
            'subject' : "Konto uf zermatt.patklaey.ch isch aktiviert",
            'message' : "Hallo {}\n\nDis Konto isch grad vomene Administrator aktiviert worde. Du chasch di ab sofort uf https://zermatt.patklaey.ch ilogge u reservatione tätige.\n\nViu Spass.\n\nZermatt Reservatione"
        }
    },
    'en': {
        'registration' : {
            'subject': "SignUp on zermatt.patklaey.ch",
            'message': "Hello {}\n\nThank you for signing up, your account will be activated soon. You will get another mail confirming the account activation.\n\nZermatt Reservations"
        },
        'activation' : {
            'subject' : "Account on zermatt.patklaey.ch activated",
            'message' : "Hello {}\n\nYour account has just been activated. You can now login on https://zermatt.patklaey.ch and add reservations.\n\nHave fun\n\nZermatt Reservations"
        }
    }
}


@app.route('/users')
@jwt_required
def show_users():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user or not current_user.admin:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403
    db_users = User.query.all()
    users = copy.deepcopy(db_users)
    userDict = []
    for user in users:
        userDict.append(user.to_dict())
    return jsonify(userDict)


@app.route('/users/<int:id>', methods=["GET"])
@jwt_required
def show_user(id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    if not current_user.admin and id != user_id_from_token:
        return jsonify({"error": {'msg': 'Operation not permitted', 'code': 14}}), 403
    user = User.query.get(id)
    if user is not None:
        return jsonify(copy.deepcopy(user).to_dict())
    else:
        return jsonify({'error': {'msg': 'User not found', 'code': 16, 'info': id}}), 404


@app.route('/users/<int:user_id>', methods=["PUT", "PATCH"])
@jwt_required
def edit_user(user_id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    if not current_user.admin and user_id != user_id_from_token:
        return jsonify({'error': {'msg': 'Operation not permitted', 'code': 14}}), 403
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': {'msg': 'User not found', 'code': 16, 'info': user_id}}), 404

    if "password" in request.json and not current_user.admin:
        if not "oldPassword" in request.json:
            return jsonify({'error': {'msg': 'Current password must be provided as "oldPassword" within the request body', 'code': 21}}), 400
        if not user.verify_password(request.json["oldPassword"]):
            return jsonify({'error': {'msg': 'Password missmatch for user', 'code': 22}}), 401

    try:
        if "password" in request.json:
            user.hash_password(request.json["password"])
            del request.json["password"]
        for attribute in request.json:
            if attribute in User.get_protected_attributes() and not current_user.admin:
                db.session.rollback()
                return jsonify({'error': {'msg': 'Attribute protected', 'code': 23}}), 400
            if attribute in User.get_all_attributes():
                setattr(user, attribute, request.json[attribute])
                if attribute == "active" and request.json[attribute] == 1:
                    send_activation_mail(user)
        db.session.commit()
        return '', 204
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": {'msg': "Failed to update user", 'code': 17}}), 500


@app.route('/users', methods=["POST"])
def add_user():
    for attribute in User.get_required_attributes():
        if not attribute in request.json:
            return jsonify({'error': {'msg': '\'' + attribute + '\' is required', 'code': 2, 'info': attribute}}), 400
    data = request.json
    new_user = User(data['username'], data['password'], data['email'], data['language'])
    db.session.add(new_user)
    db.session.commit()
    send_new_user_mail(new_user)
    return '', 201


@app.route('/users/<int:user_id>', methods=["DELETE"])
@jwt_required
def delete_user(user_id):
    user_id_from_token = get_jwt_identity()
    current_user = User.query.get(user_id_from_token)
    if not current_user.admin:
        return jsonify({'error': {'msg': 'Operation not permitted', 'code': 14}}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': {'msg': 'User not found', 'code': 16, 'info': id}}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return '', 204
    except Exception as error:
        # Log error
        print error
        return jsonify({"error": {'msg': "Cannot delete user", 'code': 18}}), 500


@app.route('/users/checkUnique', methods=["GET"])
def check_unique_attribute():
    arguments = request.args
    possible_keys = ['username', 'email']
    if not 'key' in arguments or not 'value' in arguments:
        return jsonify({'error': {'msg': '"key" and "value" must be given as query parameters', 'code': 19}}), 400
    if not arguments['key'] in possible_keys:
        return jsonify({'error': {'msg': '"key" can be one of the following: ' + ",".join(possible_keys), 'code': 20,
                                  'info': ",".join(possible_keys)}}), 400
    kwargs = {arguments['key']: arguments['value']}
    user = User.query.filter_by(**kwargs).first()
    if not user:
        return jsonify({'unique': True}), 200
    else:
        return jsonify({'unique': False}), 200


def send_new_user_mail(user):
    mail_host = app.config['MAIL_HOST']
    mail_port = app.config['MAIL_PORT']
    mail_user = app.config['MAIL_LOGIN_USER']
    mail_pass = app.config['MAIL_LOGIN_PASS']
    mailer = smtplib.SMTP_SSL(mail_host, mail_port)
    mailer.login(mail_user, mail_pass)
    send_new_user_information_mail(user, mailer)
    send_new_user_activation_request(user, mailer)
    mailer.quit()


def send_new_user_information_mail(user, mailer):
    mail_to = user.email
    mail_from = app.config['MAIL_FROM']
    mail_messaage = MAIL_MESSAGES[user.language]['registration']['message'].format(user.username)
    message = MIMEText(mail_messaage)
    message["Subject"] = MAIL_MESSAGES[user.language]['registration']['subject']
    message["From"] = mail_from
    message["To"] = mail_to
    mailer.sendmail(mail_from, mail_to, message.as_string())


def send_new_user_activation_request(user, mailer):
    mail_to = map(lambda admin_account: admin_account.email, User.get_admin_accounts())
    mail_from = app.config['MAIL_FROM']
    mail_messaage = "Hello admins\n\nA new user with username {} just signed up at zermatt.patklaey.ch. Please verify he is allowed to and activate it's account accordingly.".format(
        user.username)
    message = MIMEText(mail_messaage)
    message["Subject"] = "New user on zermatt.patklaey.ch"
    message["From"] = mail_from
    message["To"] = ", ".join(mail_to)
    mailer.sendmail(mail_from, mail_to, message.as_string())


def send_activation_mail(user):
    mail_host = app.config['MAIL_HOST']
    mail_port = app.config['MAIL_PORT']
    mail_user = app.config['MAIL_LOGIN_USER']
    mail_pass = app.config['MAIL_LOGIN_PASS']
    mailer = smtplib.SMTP_SSL(mail_host, mail_port)
    mailer.login(mail_user, mail_pass)
    mail_to = user.email
    mail_from = app.config['MAIL_FROM']
    mail_messaage = MAIL_MESSAGES[user.language]['activation']['message'].format(user.username)
    message = MIMEText(mail_messaage)
    message["Subject"] = MAIL_MESSAGES[user.language]['activation']['subject']
    message["From"] = mail_from
    message["To"] = mail_to
    mailer.sendmail(mail_from, mail_to, message.as_string())
