"""
Application factory.

Instead of creating the Flask `app` object as a global variable, we build
it inside a function (`create_app`). This is the standard Flask pattern
because it lets us:
  - create multiple app instances (useful for testing)
  - control exactly when the database and other extensions are attached
  - avoid circular imports between models and routes
"""

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import Config

# These are created here (unbound to any app) and "attached" to the real
# app later inside create_app(). This is the standard Flask-SQLAlchemy /
# Flask-Login pattern.
db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- attach extensions to this app ---
    db.init_app(app)
    login_manager.init_app(app)

    # Where Flask-Login sends a user who tries to visit a protected page
    # without being logged in.
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # --- import models so SQLAlchemy knows about them ---
    # This import has to happen after db.init_app(), and it must happen
    # somewhere before db.create_all() is called.
    from app.models.user import User
    from app.models import student, teacher, department, course, semester
    from app.models import section, subject, enrollment, attendance
    from app.models import examination, marks, fee, payment, notice

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- register blueprints (route groups) ---
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.students import students_bp
    from app.routes.teachers import teachers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(teachers_bp)

    # --- error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()  # undo any half-finished database change
        return render_template("errors/500.html"), 500

    # --- make sure the database file/tables exist ---
    with app.app_context():
        db.create_all()

    return app
