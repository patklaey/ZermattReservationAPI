from main import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    admin = db.Column(db.Boolean)

    def __init__(self, username, email, admin):
        self.username = username
        self.email = email
        self.admin = admin

    def to_dict(self):
        dict = self.__dict__
        del dict['_sa_instance_state']
        return dict
