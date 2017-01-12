from main import app, multi_auth, db
from flask import jsonify, request
from DB.User import User

@app.route('/users')
@multi_auth.login_required
def show_users():
    users = User.query.all()
    userDict = []
    for user in users:
        userDict.append(user.to_dict())
    return jsonify(userDict)


@app.route('/users/<int:id>')
@multi_auth.login_required
def show_user(id):
    user = User.query.get(id)
    if user is not None:
        return jsonify(user.to_dict())
    else:
        return jsonify({'error': 'notFound'})


@app.route('/users', methods=["POST"])
def add_user():
    for attribute in User.get_required_attributes():
        if not attribute in request.json:
            return jsonify({'error': attribute + ' is required'}), 400
    data = request.json
    new_user = User(data['username'], data['password'], data['email'])
    db.session.add(new_user)
    db.session.commit()
    userDict = new_user.to_dict()
    return jsonify(userDict), 201
