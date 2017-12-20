import base64
import sys
sys.path.insert(0, '/Users/tgdklpa4/IdeaProjects/ZermattReservationAPI')

from main import app, db
from flask_testing import LiveServerTestCase
import unittest
import json
from DB.User import User
from DB.Reservation import Reservation
from datetime import datetime, timedelta

# Testing with LiveServer
class IntegrationTest(LiveServerTestCase):

    SQLALCHEMY_DATABASE_URI = "sqlite://"
    RESERVATION_URL = "/reservations"
    USER_URL = "/users"

    admin = None
    user = None

    # if the create_app is not implemented NotImplementedError will be raised
    def create_app(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        return app

    def setUp(self):
        db.create_all()
        self.admin = User('admin', 'password', 'kly7@247.ch', "en", True, True)
        db.session.add(self.admin)
        self.user = User('user', 'password', 'pat@247.ch', "de", False, True)
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @staticmethod
    def datetime_converter(object):
        if isinstance(object, datetime):
            return object.__str__()

    def assert_unauthorized(self, method):
        result = method
        self.assertEqual(result.status_code, 401)

    def login_as_admin(self):
        auth = "Basic " + base64.b64encode("admin:password")
        result = self.client.get("/token", None, headers={'Authorization': auth})
        self.assertEqual(result.status_code, 200, result.data)
        return json.loads(result.data)['token']

    def login_as_user(self):
        auth = "Basic " + base64.b64encode("user:password")
        result = self.client.get("/token", None, headers={'Authorization': auth})
        self.assertEqual(result.status_code, 200, result.data)
        return json.loads(result.data)['token']

    def get_reservation(self, reservation_id, status_code=200):
        read_response = self.client.get(self.RESERVATION_URL + "/" + str(reservation_id), headers={'accept': 'application/json'})
        self.assertEqual(read_response.status_code, status_code, read_response.data)
        return json.loads(read_response.data)

    def add_user_reservatio(self):
        start = datetime.now()
        end = datetime.now() + timedelta(hours=1)
        reservation = Reservation("User Reservation", start, end, False, self.user.id, "Description")
        db.session.add(reservation)

    def add_admin_reservatio(self):
        start = datetime.now() + timedelta(days=1)
        end = datetime.now() + timedelta(days=1, hours=1)
        reservation = Reservation("Admin Reservation", start, end, False, self.admin.id, "Description")
        db.session.add(reservation)

    def test_flask_application_is_up_and_running(self):
        result = self.client.get("/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, "Hello, this is an API, Swagger documentation will follow here...")

    def test_actions_when_not_logged_in(self):
        result = self.client.get(self.RESERVATION_URL)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), [])
        self.assert_unauthorized(self.client.get(self.USER_URL))
        self.assert_unauthorized(self.client.get(self.USER_URL + "/1"))
        self.assert_unauthorized(self.client.put(self.USER_URL + "/1"))
        self.assert_unauthorized(self.client.delete(self.USER_URL + "/1"))
        self.assert_unauthorized(self.client.post(self.RESERVATION_URL))
        self.assert_unauthorized(self.client.get(self.RESERVATION_URL + "/1"))
        self.assert_unauthorized(self.client.put(self.RESERVATION_URL + "/1"))
        self.assert_unauthorized(self.client.delete(self.RESERVATION_URL + "/1"))

    def test_login(self):
        bad_auth = "Basic " + base64.b64encode("user:asdf")
        result = self.client.get("/token", None, headers={'Authorization': bad_auth})
        self.assertEqual(result.status_code, 401)
        bad_auth_response = json.loads(result.data)
        self.assertEqual(bad_auth_response["error"],"Invalid username or password")
        good_auth = "Basic " + base64.b64encode("user:password")
        result = self.client.get("/token", None, headers={'Authorization': good_auth})
        self.assertEqual(result.status_code, 200)
        good_auth_response = json.loads(result.data)
        self.assertIsNotNone(good_auth_response["token"])
        not_active_user = User('notActive', 'password', 'not.active@247.ch', "en", False, False)
        db.session.add(not_active_user)
        not_active_auth = "Basic " + base64.b64encode("notActive:password")
        result = self.client.get("/token", None, headers={'Authorization': not_active_auth})
        self.assertEqual(result.status_code, 401)
        not_active_response = json.loads(result.data)
        self.assertEqual(not_active_response["error"],"Invalid username or password")

    def test_user_can_crud_reservation(self):
        self.login_as_user()
        start = datetime.now()
        start = start.replace(minute=0)
        start = start.replace(second=0)
        start = start.replace(microsecond=0)
        end = datetime.now()
        end = end + timedelta(hours=1)
        end = end.replace(minute=0)
        end = end.replace(second=0)
        end = end.replace(microsecond=0)
        # Create
        reservation = Reservation("Title", start, end, False, self.user.id, "Description")
        request_data = json.dumps(reservation.to_dict(), default=self.datetime_converter)
        result = self.client.post(self.RESERVATION_URL, data=request_data, headers={'accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(result.status_code, 201)
        response_data = json.loads(result.data)
        self.assertEqual(response_data['userId'], self.user.id)
        reservation_id = response_data['id']
        # Read
        read_response_data = self.get_reservation(reservation_id)
        self.assertEqual(read_response_data['title'], reservation.title)
        self.assertEqual(read_response_data['allDay'], reservation.allDay)
        self.assertEqual(read_response_data['description'], reservation.description)
        self.assertEqual(read_response_data['userId'], reservation.userId)
        self.assertEqual(read_response_data['startTime'], reservation.startTime.strftime("%a, %d %b %Y %X GMT"))
        original_end_time = read_response_data['endTime']
        self.assertEqual(original_end_time, reservation.endTime.strftime("%a, %d %b %Y %X GMT"))
        self.assertEqual(read_response_data['id'], reservation_id)
        # Update
        new_end = end + timedelta(hours=1)
        update_request = {"endTime": new_end}
        update_response = self.client.put(self.RESERVATION_URL + "/" + str(reservation_id), data=json.dumps(update_request, default=self.datetime_converter), headers={'accept': 'application/json', 'Content-Type': 'application/json'})
        self.assertEqual(update_response.status_code, 204)
        read_response_data = self.get_reservation(reservation_id)
        self.assertEqual(read_response_data['endTime'], new_end.strftime("%a, %d %b %Y %X GMT"))
        self.assertNotEqual(read_response_data['endTime'], reservation.endTime.strftime("%a, %d %b %Y %X GMT"))
        # Delete
        delete_response = self.client.delete(self.RESERVATION_URL + "/" + str(reservation_id))
        self.assertEqual(delete_response.status_code, 204)
        self.get_reservation(reservation_id, 404)


if __name__ == '__main__':
    unittest.main()