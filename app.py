from flask import Flask
from config import Config
from extensions import db, login_manager, bcrypt
from routes.student import student_bp
from routes.lecturer import lecturer_bp
from routes.admin import admin_bp
from models import User
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'lecturer.login'  # default for @login_required
    login_manager.login_message_category = 'info'
    bcrypt.init_app(app)

    # register blueprints
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(lecturer_bp)
    app.register_blueprint(admin_bp)

    # create tables if not exist
    with app.app_context():
        db.create_all()
        # create a default admin if not exists
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User(
                name='admin',
                subject=None,
                is_admin=True
            )
            admin.set_password('admin123')  # change default!
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: username='admin', password='admin123'. Change it!")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)