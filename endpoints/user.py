import smtplib
from email.mime.text import MIMEText
from main import app, db
from flask import jsonify, request, g
from DB.User import User
from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route('/users')
@jwt_required
def show_users():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user or not current_user.admin:
        return jsonify({"error": "Operation not permitted"}), 403
    users = User.query.all()
    userDict = []
    for user in users:
        userDict.append(user.to_dict())
    return jsonify(userDict)


@app.route('/users/<int:id>', methods=["GET"])
@jwt_required
def show_user(id):
    user = User.query.get(id)
    if user is not None:
        return jsonify(user.to_dict())
    else:
        return jsonify({'error': 'User not found'})


@app.route('/users/<int:id>', methods=["PUT","PATCH"])
@jwt_required
def edit_user(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    if not current_user.admin:
        return jsonify({'error': 'Operation not permitted'}), 403

    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    for attribute in request.data:
        if attribute in User.get_all_attributes():
            setattr(user, attribute, getattr(request.data, attribute))
    db.session.commit()
    return '', 200


@app.route('/users', methods=["POST"])
def add_user():
    for attribute in User.get_required_attributes():
        if not attribute in request.json:
            return jsonify({'error': attribute + ' is required'}), 400
    data = request.json
    new_user = User(data['username'], data['password'], data['email'])
    db.session.add(new_user)
    db.session.commit()
    send_new_user_mail(new_user)
    return '', 201


@app.route('/users/checkUnique', methods=["GET"])
def check_unique_attribute():
    arguments = request.args
    possible_keys = ['username','email']
    if not 'key' in arguments or not 'value' in arguments:
        return jsonify({'error':'"key" and "value" must be given as query parameters'}), 400
    if not arguments['key'] in possible_keys:
        return jsonify({'error':'"key" can be one of the following: ' + ",".join(possible_keys)}), 400
    kwargs = {arguments['key'] : arguments['value']}
    user = User.query.filter_by(**kwargs).first()
    if not user:
        return jsonify({'unique':True}), 200
    else:
        return jsonify({'unique':False}), 200


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
    mail_messaage = "Hello {}\n\nThank you for signing up, your account will be activated soon. You will get another mail confirming the account activation.".format(
        user.username)
    message = MIMEText(mail_messaage)
    message["Subject"] = "SignUp on zermatt.patklaey.ch"
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
