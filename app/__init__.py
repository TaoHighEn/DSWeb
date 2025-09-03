from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 驗證 LINE 設定
    try:
        Config.validate_line_config()
    except ValueError as e:
        app.logger.error(f"LINE 設定錯誤: {e}")
        print(f"錯誤: {e}")
        print("請檢查 .env 檔案中的 LINE OAuth 設定")

    db.init_app(app)
    migrate.init_app(app, db)

    # 註冊藍圖
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)

    # 模板全局變量
    @app.context_processor
    def inject_globals():
        return {
            'current_year': 2025
        }

    # 錯誤處理
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    return app