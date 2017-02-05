from main import db, jwt, g
from passlib.apps import custom_app_context as pwd_context
from flask_jwt_extended import create_access_token

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True)
    admin = db.Column(db.Boolean)
    active = db.Column(db.Boolean)

    def __init__(self, username, password, email, admin=False, active=False):
        self.username = username
        self.email = email
        self.admin = admin
        self.hash_password(password)
        self.active = active

    def to_dict(self):
        dict = self.__dict__
        del dict['_sa_instance_state']
        del dict['password_hash']
        return dict

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self):
        token = create_access_token(identity=self.id)
        return token

    @jwt.user_claims_loader
    def add_claims_to_access_token(user_id):
        return {
            'admin': g.user.admin,
            'username': g.user.username
        }

    @staticmethod
    def get_required_attributes():
        return ['username', 'password', 'email']


    @staticmethod
    def get_all_attributes():
        return ['username', 'password', 'email', 'admin', 'active']


    @staticmethod
    def get_admin_accounts():
        return User.query.filter_by(admin=True).all()
