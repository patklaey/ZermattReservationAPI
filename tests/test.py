import base64

import sys
sys.path.insert(0, '/Users/tgdklpa4/IdeaProjects/ZermattReservationAPI')

from main import app, db
from flask_testing import LiveServerTestCase
import unittest
import json
from DB.User import User

# Testing with LiveServer
class MyTest(LiveServerTestCase):

    SQLALCHEMY_DATABASE_URI = "sqlite://"
    RESERVATION_URL = "/reservations"
    USER_URL = "/users"

    # if the create_app is not implemented NotImplementedError will be raised
    def create_app(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def assert_unauthorized(self, method):
        result = method
        self.assertEqual(result.status_code, 401)

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
        user = User('user', 'password', 'kly7@247.ch', "en", True, True)
        db.session.add(user)
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
        not_active_user = User('notActive', 'password', 'pat@247.ch', "en", False, False)
        db.session.add(not_active_user)
        not_active_auth = "Basic " + base64.b64encode("notActive:password")
        result = self.client.get("/token", None, headers={'Authorization': not_active_auth})
        self.assertEqual(result.status_code, 401)
        not_active_response = json.loads(result.data)
        self.assertEqual(not_active_response["error"],"Invalid username or password")


if __name__ == '__main__':
    unittest.main()