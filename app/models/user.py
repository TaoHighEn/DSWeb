from app import db
from datetime import datetime

class User(db.Model):
    """
    使用者模型
    ----------
    id : 主鍵
    username : 使用者名稱
    email : 電子郵件
    line_user_id : LINE User ID (唯一)
    created_at : 建立時間
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=False, nullable=True)
    email = db.Column(db.String(120), unique=False, nullable=True)
    line_user_id = db.Column(db.String(128), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
