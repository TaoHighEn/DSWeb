import requests
from flask import Blueprint, render_template, redirect, request, url_for, session, current_app
from app import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    # 建立 Line OAuth URL
    params = {
        "response_type": "code",
        "client_id": current_app.config["LINE_CHANNEL_ID"],
        "redirect_uri": current_app.config["LINE_REDIRECT_URI"],
        "state": current_app.config["OAUTH_STATE"],
        "scope": current_app.config["OAUTH_SCOPE"]
    }
    query = "&".join([f"{k}={v}" for k,v in params.items()])
    line_login_url = f"{current_app.config['LINE_AUTH_URL']}?{query}"
    return render_template("login.html", line_login_url=line_login_url)

@auth_bp.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    # 交換 Access Token
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": current_app.config["LINE_REDIRECT_URI"],
        "client_id": current_app.config["LINE_CHANNEL_ID"],
        "client_secret": current_app.config["LINE_CHANNEL_SECRET"],
    }
    token_res = requests.post(current_app.config["LINE_TOKEN_URL"], data=data)
    token_json = token_res.json()
    access_token = token_json.get("access_token")

    # 取得用戶資料
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_res = requests.get(current_app.config["LINE_PROFILE_URL"], headers=headers)
    profile = profile_res.json()

    line_user_id = profile["userId"]
    display_name = profile.get("displayName")

    # 儲存或更新用戶
    user = User.query.filter_by(line_user_id=line_user_id).first()
    if not user:
        user = User(username=display_name, line_user_id=line_user_id)
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    return redirect(url_for("auth.profile"))

@auth_bp.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    user = User.query.get(user_id)
    return f"歡迎 {user.username or '使用者'} (Line ID: {user.line_user_id})"
