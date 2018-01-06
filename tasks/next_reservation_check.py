import locale
import smtplib
from locale import setlocale

from main import app, db
import pytz
from datetime import datetime, timedelta
from constants import MAIL_MESSAGES
from DB.User import User
from email.mime.text import MIMEText


def datetime_converter(object):
    if isinstance(object, datetime):
        return object.__str__()


def send_friendly_reminder(next_reservation, user, mailer):
    mail_to = user.email
    mail_from = app.config['MAIL_FROM']
    user_locale = "en_US" if user.language == "en" else "de_CH"
    lc = locale.setlocale(locale.LC_TIME)
    try:
        locale.setlocale(locale.LC_TIME, user_locale)
        next_reservation_string = next_reservation.startTime.strftime("%c")
    finally:
        locale.setlocale(locale.LC_TIME, lc)
    mail_message = MAIL_MESSAGES[user.language]['reminder']['message'].format(user.username, next_reservation_string)
    message = MIMEText(mail_message)
    message["Subject"] = MAIL_MESSAGES[user.language]['reminder']['subject']
    message["From"] = mail_from
    message["To"] = mail_to
    mailer.sendmail(mail_from, mail_to, message.as_string())


def check_all_users():
    mail_host = app.config['MAIL_HOST']
    mail_port = app.config['MAIL_PORT']
    mail_user = app.config['MAIL_LOGIN_USER']
    mail_pass = app.config['MAIL_LOGIN_PASS']
    mailer = smtplib.SMTP_SSL(mail_host, mail_port)
    mailer.login(mail_user, mail_pass)
    print "Start checking reservations"
    now = pytz.utc.localize(datetime.now())
    all_users = User.query.all()
    for user in all_users:
        next_reservation = user.get_next_reservation()
        if next_reservation is not None and not next_reservation.reminderMailSent:
            start_time = next_reservation.startTime
            if start_time - timedelta(days=2) < now:
                send_friendly_reminder(next_reservation, user, mailer)
                next_reservation.reminderMailSent = True
                db.session.commit()
    mailer.quit()
