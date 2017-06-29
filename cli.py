import click

from main import app, db
from DB.User import User
from DB.Reservation import Reservation
from datetime import datetime


@app.cli.command()
def initdb():
    """Initialize the database."""
    db.create_all()
    click.echo('Init the db')


@app.cli.command()
def addadminuser():
    admin = User('admin', 'admin', 'kly7@247.ch', "en", True, True)
    db.session.add(admin)
    db.session.commit()
    click.echo("Done")


@app.cli.command()
def addreservation():
    start = datetime.now()
    end = datetime.now()
    hour = end.hour + 1
    end = end.replace(hour=hour)
    res = Reservation("Title", start, end, False, 1, "Description")
    db.session.add(res)
    db.session.commit()
    click.echo("Done")


@app.cli.command()
def cleandb():
    db.drop_all()
    click.echo("Tables dropped")
