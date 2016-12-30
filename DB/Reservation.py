from main import db


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    startTime = db.Column(db.DateTime)
    endTime = db.Column(db.DateTime)
    allDay = db.Column(db.Boolean)
    title = db.Column(db.String(80))
    description = db.Column(db.String(256))
    userId = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, title, start_date, end_date, all_day, uesr_id, description=""):
        self.title = title
        self.description = description
        self.startTime = start_date
        self.endTime = end_date
        self.allDay = all_day
        self.userId = uesr_id

    def to_dict(self):
        dict = self.__dict__
        del dict['_sa_instance_state']
        return dict

    @staticmethod
    def get_required_attributes():
        return ['title', 'startTime', 'endTime', 'allDay', 'description', 'userId']
