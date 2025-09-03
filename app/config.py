import os
import secrets
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, "..", ".env"))

class Config:
    # 基本配置
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(basedir, '..', 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LINE OAuth 配置
    LINE_CHANNEL_ID = os.environ.get("LINE_CHANNEL_ID")
    LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
    LINE_REDIRECT_URI = os.environ.get("LINE_REDIRECT_URI") or "http://localhost:5000/auth/callback"
    
    # LINE API URLs
    LINE_AUTH_URL = os.environ.get("LINE_AUTH_URL", "https://access.line.me/oauth2/v2.1/authorize")
    LINE_TOKEN_URL = os.environ.get("LINE_TOKEN_URL", "https://api.line.me/oauth2/v2.1/token")
    LINE_PROFILE_URL = os.environ.get("LINE_PROFILE_URL", "https://api.line.me/v2/profile")
    
    # OAuth 配置
    OAUTH_SCOPE = os.environ.get("OAUTH_SCOPE", "profile openid")  # 移除 email，除非你的 LINE 應用有申請
    OAUTH_STATE = os.environ.get("OAUTH_STATE") or secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_line_config():
        """驗證 LINE OAuth 設定是否完整"""
        required_configs = [
            'LINE_CHANNEL_ID',
            'LINE_CHANNEL_SECRET',
            'LINE_REDIRECT_URI'
        ]
        
        missing_configs = []
        for config in required_configs:
            if not getattr(Config, config):
                missing_configs.append(config)
        
        if missing_configs:
            raise ValueError(f"缺少必要的 LINE 設定: {', '.join(missing_configs)}")
        
        return True