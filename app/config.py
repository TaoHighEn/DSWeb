import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, "..", ".env"))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev_key"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LINE OAuth 配置
    LINE_CHANNEL_ID = os.environ.get("LINE_CHANNEL_ID")
    LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
    LINE_REDIRECT_URI = os.environ.get("LINE_REDIRECT_URI")
    
    # LINE API URLs
    LINE_AUTH_URL = os.environ.get("LINE_AUTH_URL", "https://access.line.me/oauth2/v2.1/authorize")
    LINE_TOKEN_URL = os.environ.get("LINE_TOKEN_URL", "https://api.line.me/oauth2/v2.1/token")
    LINE_PROFILE_URL = os.environ.get("LINE_PROFILE_URL", "https://api.line.me/v2/profile")
    
    # OAuth 配置
    OAUTH_SCOPE = os.environ.get("OAUTH_SCOPE", "profile openid email")
    OAUTH_STATE = os.environ.get("OAUTH_STATE", "random_state_string")
