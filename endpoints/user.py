from main import app, multi_auth
from flask import jsonify
from DB.User import User

@app.route('/users')
@multi_auth.login_required
def show_entries():
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