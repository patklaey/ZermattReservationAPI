import base64
import sys
sys.path.insert(0, '/Users/tgdklpa4/IdeaProjects/ZermattReservationAPI')

from main import app, db
from flask_testing import LiveServerTestCase
import unittest
import json
import mock
from DB.User import User
from DB.Reservation import Reservation
from datetime import datetime, timedelta, tzinfo
from dateutil.parser import parse
from endpoints.user import send_new_user_mail

DEFAULT_HEADERS = {'accept': 'application/json', 'Content-Type': 'application/json'}
RESERVATION_URL = "/reservations"
USER_URL = "/users"
ADMIN_USER_ID = 1
USER_USER_ID = 2

# Testing with LiveServer
class IntegrationTest(LiveServerTestCase):

    admin = None
    user = None

    # if the create_app is not implemented NotImplementedError will be raised
    def create_app(self):
        app.config['DEBUG'] = False
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
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
        self.assertEqual(result.status_code, 401, result.data)

    def assert_not_allowed(self, method):
        result = method
        self.assertEqual(result.status_code, 403, result.data)

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

    def add_reservation(self, reservation, expected_status_code=201):
        request_data = json.dumps(reservation.to_dict(), default=self.datetime_converter)
        result = self.client.post(RESERVATION_URL, data=request_data,
                                  headers=DEFAULT_HEADERS)
        self.assertEqual(result.status_code, expected_status_code, result.data)

    def get_reservation(self, reservation_id, status_code=200):
        read_response = self.client.get(RESERVATION_URL + "/" + str(reservation_id), headers={'accept': 'application/json'})
        self.assertEqual(read_response.status_code, status_code, read_response.data)
        return json.loads(read_response.data)

    def delete_reservation(self, reservation_id, delete_status_code=204, get_status_code=404):
        delete_response = self.client.delete(RESERVATION_URL + "/" + str(reservation_id))
        self.assertEqual(delete_response.status_code, delete_status_code, delete_response.data)
        self.get_reservation(reservation_id, get_status_code)

    def update_reservation(self, update_request, expected_status_code=400):
        update_result = self.client.put(RESERVATION_URL + "/1", data=json.dumps(update_request),
                                        headers=DEFAULT_HEADERS)
        self.assertEqual(update_result.status_code, expected_status_code)


    def add_user_reservation(self):
        start = datetime.now()
        end = datetime.now() + timedelta(hours=1)
        reservation = Reservation("User Reservation", start, end, False, self.user.id, "Description")
        self.login_as_user()
        self.add_reservation(reservation)

    def add_admin_reservation(self):
        start = datetime.now() + timedelta(days=1)
        end = datetime.now() + timedelta(days=1, hours=1)
        reservation = Reservation("Admin Reservation", start, end, False, self.admin.id, "Description")
        self.login_as_admin()
        self.add_reservation(reservation)

    def add_base_reservation(self):
        base_reservation_start = datetime(2018, 01, 01, 12, 00, 00, 00)
        base_reservation_end = datetime(2018, 01, 01, 16, 00, 00, 00)
        base_reservation = Reservation("base reservation", base_reservation_start, base_reservation_end, False,
                                       USER_USER_ID)
        self.login_as_user()
        self.add_reservation(base_reservation)
        return base_reservation_end, base_reservation_start

    def test_flask_application_is_up_and_running(self):
        result = self.client.get("/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, "Hello, this is an API, Swagger documentation will follow here...")

    def test_actions_when_not_logged_in(self):
        reservation = Reservation("test", datetime.now(), datetime.now(), False, USER_USER_ID)
        db.session.add(reservation)
        db.session.commit()
        result = self.client.get(RESERVATION_URL)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(json.loads(result.data)), 1)
        #self.assertEqual(json.loads(result.data), [])
        self.assert_unauthorized(self.client.get(USER_URL))
        self.assert_unauthorized(self.client.get(USER_URL + "/1"))
        self.assert_unauthorized(self.client.put(USER_URL + "/1"))
        self.assert_unauthorized(self.client.delete(USER_URL + "/1"))
        self.assert_unauthorized(self.client.post(RESERVATION_URL))
        self.assert_unauthorized(self.client.get(RESERVATION_URL + "/1"))
        self.assert_unauthorized(self.client.put(RESERVATION_URL + "/1"))
        self.assert_unauthorized(self.client.delete(RESERVATION_URL + "/1"))

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
        result = self.client.post(RESERVATION_URL, data=request_data, headers=DEFAULT_HEADERS)
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
        update_request = {"endTime": new_end, "title": "updated title"}
        update_response = self.client.put(RESERVATION_URL + "/" + str(reservation_id), data=json.dumps(update_request, default=self.datetime_converter), headers=DEFAULT_HEADERS)
        self.assertEqual(update_response.status_code, 204)
        read_response_data = self.get_reservation(reservation_id)
        self.assertEqual(read_response_data['endTime'], new_end.strftime("%a, %d %b %Y %X GMT"))
        self.assertNotEqual(read_response_data['endTime'], reservation.endTime.strftime("%a, %d %b %Y %X GMT"))
        # Delete
        self.delete_reservation(reservation_id)
        self.delete_reservation(reservation_id, 404)

    def test_admin_can_rud_other_reservations(self):
        self.add_user_reservation()
        self.login_as_admin()
        reservation = self.get_reservation(1)
        end_time = parse(reservation['endTime'])
        new_end = end_time + timedelta(hours=1)
        update_request = {"endTime": new_end}
        update_response = self.client.put(RESERVATION_URL + "/" + str(reservation['id']), data=json.dumps(update_request, default=self.datetime_converter), headers=DEFAULT_HEADERS)
        self.assertEqual(update_response.status_code, 204)
        self.delete_reservation(reservation['id'])

    def test_user_cannot_rud_other_reservations(self):
        self.add_admin_reservation()
        self.login_as_user()
        reservation = self.get_reservation(1)
        end_time = parse(reservation['endTime'])
        new_end = end_time + timedelta(hours=1)
        update_request = {"endTime": new_end}
        self.assert_not_allowed(self.client.put(RESERVATION_URL + "/" + str(reservation['id']), data=json.dumps(update_request, default=self.datetime_converter), headers=DEFAULT_HEADERS))
        self.delete_reservation(reservation['id'], 403, 200)

    def test_user_cannot_get_users(self):
        self.login_as_user()
        self.assert_not_allowed(self.client.get(USER_URL))
        self.assert_not_allowed(self.client.get(USER_URL + "/" + str(ADMIN_USER_ID)))
        response = self.client.get(USER_URL + "/" + str(USER_USER_ID))
        self.assertEqual(response.status_code, 200)

    def test_admin_user_can_read_all_users(self):
        self.login_as_admin()
        read_response = self.client.get(USER_URL)
        self.assertEqual(read_response.status_code, 200)
        read_response = self.client.get(USER_URL + "/" + str(USER_USER_ID))
        self.assertEqual(read_response.status_code, 200)
        read_response = self.client.get(USER_URL + "/" + str(ADMIN_USER_ID))
        self.assertEqual(read_response.status_code, 200)

    def test_admin_can_update_and_delete_users(self):
        self.login_as_admin()
        user_response = self.client.get(USER_URL + "/" + str(USER_USER_ID))
        language_before_update = json.loads(user_response.data)['language']
        self.assertEqual(language_before_update, 'de')
        update_request = {'language':'en'}
        update_response = self.client.put(USER_URL + "/" + str(USER_USER_ID), data=json.dumps(update_request), headers=DEFAULT_HEADERS)
        self.assertEqual(update_response.status_code, 204)
        user_response = self.client.get(USER_URL + "/" + str(USER_USER_ID))
        language_after_update = json.loads(user_response.data)['language']
        self.assertEqual(language_after_update, 'en')
        self.assertNotEqual(language_before_update, language_after_update)
        delete_response = self.client.delete(USER_URL + "/" + str(USER_USER_ID))
        self.assertEqual(delete_response.status_code, 204)
        user_response = self.client.get(USER_URL + "/" + str(USER_USER_ID))
        self.assertEqual(user_response.status_code, 404)
        delete_response = self.client.delete(USER_URL + "/" + str(USER_USER_ID))
        self.assertEqual(delete_response.status_code, 404)

    @mock.patch('endpoints.user.smtplib')
    def test_create_user(self, mock_smtplib):
        request_data = {'username':'testuser', 'email':'testuser@247.ch', 'password':'password', 'language':'de'}
        create_response = self.client.post(USER_URL, data=json.dumps(request_data), headers=DEFAULT_HEADERS)
        self.assertEqual(create_response.status_code, 201, create_response.data)
        mock_smtplib.SMTP_SSL.assert_called_with(app.config['MAIL_HOST'],app.config['MAIL_PORT'])
        self.login_as_admin()
        update_data = {'active': 1}
        update_response = self.client.put(USER_URL + "/" + str(USER_USER_ID + 1), data=json.dumps(update_data), headers=DEFAULT_HEADERS)
        self.assertEqual(update_response.status_code, 204)
        mock_smtplib.SMTP_SSL.assert_called_with(app.config['MAIL_HOST'],app.config['MAIL_PORT'])

    def test_cannot_have_overlapping_events(self):
        base_reservation_end, base_reservation_start = self.add_base_reservation()
        overlapping_beginning_start = base_reservation_start - timedelta(hours=1)
        overlapping_beginning_end = base_reservation_start + timedelta(hours=1)
        overlapping_beginning = Reservation("Overlapping beginning", overlapping_beginning_start, overlapping_beginning_end, False, ADMIN_USER_ID)
        self.login_as_admin()
        self.add_reservation(overlapping_beginning, 409)
        overlapping_end_start = base_reservation_end - timedelta(seconds=1)
        overlapping_end_end = base_reservation_end + timedelta(hours=1)
        overlapping_end = Reservation("Overlapping end", overlapping_end_start, overlapping_end_end, False, ADMIN_USER_ID)
        self.add_reservation(overlapping_end, 409)
        contained_start = base_reservation_start + timedelta(minutes=1)
        contained_end = base_reservation_end - timedelta(minutes=1)
        contained = Reservation("Contained", contained_start, contained_end, False, ADMIN_USER_ID)
        self.add_reservation(contained, 409)
        wrapping_start = base_reservation_start - timedelta(minutes=1)
        wrapping_end = base_reservation_end + timedelta(minutes=1)
        wrapping = Reservation("Wrapping", wrapping_start, wrapping_end, False, ADMIN_USER_ID)
        self.add_reservation(wrapping, 409)
        perfect_match_start = base_reservation_end
        perfect_match_end = base_reservation_end + timedelta(hours=1)
        perfect_match = Reservation("Perfect match", perfect_match_start, perfect_match_end, False, ADMIN_USER_ID)
        self.add_reservation(perfect_match)
        same_start_start = base_reservation_start
        same_start_end = base_reservation_end + timedelta(hours=1)
        same_start = Reservation("Same start", same_start_start, same_start_end, False, ADMIN_USER_ID)
        self.add_reservation(same_start, 409)
        same_end_start = base_reservation_start + timedelta(hours=1)
        same_end_end = base_reservation_end
        same_end = Reservation("Same end", same_end_start, same_end_end, False, ADMIN_USER_ID)
        self.add_reservation(same_end, 409)

    def test_wrong_time_values(self):
        base_reservation_end, base_reservation_start = self.add_base_reservation()
        wrong_values_start = datetime(2018, 01, 01, 10, 00, 00, 00)
        wrong_values_end = datetime(2018, 01, 01, 11, 00, 00, 00)
        wrong_values = Reservation("Wrong values", wrong_values_start, wrong_values_end, False, ADMIN_USER_ID)
        wrong_values.endTime -= timedelta(hours=2)
        self.login_as_admin()
        self.add_reservation(wrong_values, 400)
        update_end_time_request = { "endTime": (base_reservation_end - timedelta(days=1)).__str__()}
        self.update_reservation(update_end_time_request)
        update_start_time_request = {"startTime": (base_reservation_start + timedelta(days=1)).__str__()}
        self.update_reservation(update_start_time_request)
        update_wrong_dates_request = dict(update_start_time_request.items() + update_end_time_request.items())
        self.update_reservation(update_wrong_dates_request)
        self.update_reservation({'startTime': "asdf"})
        self.update_reservation({'endTime': "asdf"})
        invalid_start_date_data = wrong_values.to_dict()
        invalid_start_date_data['startTime'] = "asdf"
        result = self.client.post(RESERVATION_URL, data=json.dumps(invalid_start_date_data, default=self.datetime_converter),
                                  headers=DEFAULT_HEADERS)
        self.assertEqual(result.status_code, 400, result.data)
        invalid_end_date_data = wrong_values.to_dict()
        invalid_end_date_data['endTime'] = "asdf"
        result = self.client.post(RESERVATION_URL, data=json.dumps(invalid_end_date_data, default=self.datetime_converter),
                                  headers=DEFAULT_HEADERS)
        self.assertEqual(result.status_code, 400, result.data)
        missing_start_time_data = wrong_values.to_dict()
        del missing_start_time_data['startTime']
        result = self.client.post(RESERVATION_URL, data=json.dumps(missing_start_time_data, default=self.datetime_converter),
                                  headers=DEFAULT_HEADERS)
        self.assertEqual(result.status_code, 400, result.data)

    def test_check_unique(self):
        unique_result = self.client.get(USER_URL + "/checkUnique?key=username&value=newUser")
        self.assertEqual(unique_result.status_code, 200)
        self.assertEqual(json.loads(unique_result.data)['unique'], True)
        unique_result = self.client.get(USER_URL + "/checkUnique?key=username&value=user")
        self.assertEqual(unique_result.status_code, 200)
        self.assertEqual(json.loads(unique_result.data)['unique'], False)
        unique_result = self.client.get(USER_URL + "/checkUnique?key=username")
        self.assertEqual(unique_result.status_code, 400)
        unique_result = self.client.get(USER_URL + "/checkUnique?value=test")
        self.assertEqual(unique_result.status_code, 400)
        unique_result = self.client.get(USER_URL + "/checkUnique?key=asdf&value=asdf")
        self.assertEqual(unique_result.status_code, 400)
        unique_result = self.client.get(USER_URL + "/checkUnique?key=email&value=pat@247.ch")
        self.assertEqual(unique_result.status_code, 200)
        self.assertEqual(json.loads(unique_result.data)['unique'], False)
        unique_result = self.client.get(USER_URL + "/checkUnique?key=email&value=asdf@247.ch")
        self.assertEqual(unique_result.status_code, 200)
        self.assertEqual(json.loads(unique_result.data)['unique'], True)

    def test_user_update_self_password(self):
        self.login_as_user()
        update_password_missing_old = {"password": "asdfasdf"}
        update_result = self.client.put(USER_URL + "/" + str(USER_USER_ID),
                                        data=json.dumps(update_password_missing_old),
                                        headers=DEFAULT_HEADERS)
        self.assertEqual(update_result.status_code, 400, update_result.data)
        self.assertEqual(json.loads(update_result.data)['error']['msg'], "Current password must be provided as \"oldPassword\" within the request body")
        update_password_mismatch_old = {"password": "asdf", "oldPassword": "asdfasdf"}
        update_result = self.client.put(USER_URL + "/" + str(USER_USER_ID),
                                        data=json.dumps(update_password_mismatch_old),
                                        headers=DEFAULT_HEADERS)
        self.assertEqual(update_result.status_code, 401, update_result.data)
        self.assertEqual(json.loads(update_result.data)['error']['msg'], "Password missmatch for user")
        update_password_request = {"password": "asdf", "oldPassword": "password" }
        update_result = self.client.put(USER_URL + "/" + str(USER_USER_ID),
                                        data=json.dumps(update_password_request),
                                        headers=DEFAULT_HEADERS)
        self.assertEqual(update_result.status_code, 400, update_result.data)
        self.assertEqual(json.loads(update_result.data)['error']['msg'], "Password needs to be at least 8 characters long")
        update_password_request = {"password": "newPassword", "oldPassword": "password" }
        update_result = self.client.put(USER_URL + "/" + str(USER_USER_ID),
                                        data=json.dumps(update_password_request),
                                        headers=DEFAULT_HEADERS)
        self.assertEqual(update_result.status_code, 204, update_result.data)
        auth = "Basic " + base64.b64encode("user:newPassword")
        result = self.client.get("/token", None, headers={'Authorization': auth})
        self.assertEqual(result.status_code, 200, result.data)


    # TODO: Update protected user valus (username, email)


if __name__ == '__main__':
    unittest.main()