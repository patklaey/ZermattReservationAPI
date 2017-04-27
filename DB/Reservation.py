from main import db
from datetime import datetime
import pytz
from sqlalchemy import orm

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
        self.allDay = all_day
        self.userId = uesr_id

        if not type(start_date) is datetime:
            raise ValueError("start_date must be a datetime object")

        if not type(end_date) is datetime:
            raise ValueError("end_date must be a datetime object")

        if start_date.tzinfo is None or start_date.tzinfo.utcoffset(start_date) is None:
            start_date = pytz.utc.localize(start_date)

        if end_date.tzinfo is None or end_date.tzinfo.utcoffset(end_date) is None:
            end_date = pytz.utc.localize(end_date)
            
        self.startTime = start_date
        self.endTime = end_date

    @orm.reconstructor
    def init_on_load(self):
        if self.startTime.tzinfo is None or self.startTime.tzinfo.utcoffset(self.startTime) is None:
            self.startTime = pytz.utc.localize(self.startTime)

        if self.endTime.tzinfo is None or self.endTime.tzinfo.utcoffset(self.endTime) is None:
            self.endTime = pytz.utc.localize(self.endTime)

    def to_dict(self):
        dict = self.__dict__
        del dict['_sa_instance_state']
        return dict

    @staticmethod
    def get_required_attributes():
        return ['title', 'startTime', 'endTime', 'allDay']

    @staticmethod
    def get_all_attributes():
        return ['title', 'startTime', 'endTime', 'allDay', 'description']
