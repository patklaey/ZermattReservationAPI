from main import db


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    all_day = db.Column(db.Boolean)
    title = db.Column(db.String(80))
    description = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, description, start_date, end_date, all_day, uesr_id):
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.all_day = all_day
        self.user_id = uesr_id

    def to_dict(self):
        dict = self.__dict__
        del dict['_sa_instance_state']
        return dict
