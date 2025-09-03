from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # 根路径路由
    @app.route("/")
    def index():
        return render_template("index.html")

    # 載入藍圖
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app
