from flask import Flask
from controller.database import db
from controller.models import*
from datetime import datetime
from controller.routes import *

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'thisissecretkey'
db.init_app(app)

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(email='admin@gmail.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@gmail.com',
            password='1234567890',
            dob=datetime(1999, 1, 1),  # Convert to date object
            fullname='Admin User',
            qualification='Admin'
        )
        db.session.add(admin)
    db.session.commit()

from controller.routes import *

if __name__ == '__main__':
    app.run(debug=True)
