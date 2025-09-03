import requests
import urllib.parse
from flask import Blueprint, render_template, redirect, request, url_for, session, current_app, flash
from app import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    # 建立 LINE OAuth URL
    params = {
        "response_type": "code",
        "client_id": current_app.config["LINE_CHANNEL_ID"],
        "redirect_uri": current_app.config["LINE_REDIRECT_URI"],
        "state": current_app.config["OAUTH_STATE"],
        "scope": current_app.config["OAUTH_SCOPE"]
    }
    
    # 正確編碼URL參數
    query = urllib.parse.urlencode(params)
    line_login_url = f"{current_app.config['LINE_AUTH_URL']}?{query}"
    
    return render_template("login.html", line_login_url=line_login_url)

@auth_bp.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    # 檢查是否有錯誤
    if error:
        flash(f"LINE 登入失敗: {error}", "error")
        return redirect(url_for("auth.login"))
    
    # 檢查 code 是否存在
    if not code:
        flash("未收到授權碼", "error")
        return redirect(url_for("auth.login"))
    
    # 驗證 state (防止 CSRF 攻擊)
    if state != current_app.config["OAUTH_STATE"]:
        flash("狀態驗證失敗", "error")
        return redirect(url_for("auth.login"))
    
    try:
        # 交換 Access Token
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": current_app.config["LINE_REDIRECT_URI"],
            "client_id": current_app.config["LINE_CHANNEL_ID"],
            "client_secret": current_app.config["LINE_CHANNEL_SECRET"],
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_res = requests.post(
            current_app.config["LINE_TOKEN_URL"], 
            data=data, 
            headers=headers,
            timeout=10
        )
        
        if token_res.status_code != 200:
            flash(f"取得 Access Token 失敗: {token_res.status_code}", "error")
            return redirect(url_for("auth.login"))
        
        token_json = token_res.json()
        
        if "error" in token_json:
            flash(f"LINE API 錯誤: {token_json.get('error_description', token_json['error'])}", "error")
            return redirect(url_for("auth.login"))
        
        access_token = token_json.get("access_token")
        if not access_token:
            flash("未收到 Access Token", "error")
            return redirect(url_for("auth.login"))
        
        # 取得用戶資料
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_res = requests.get(
            current_app.config["LINE_PROFILE_URL"], 
            headers=headers,
            timeout=10
        )
        
        if profile_res.status_code != 200:
            flash(f"取得用戶資料失敗: {profile_res.status_code}", "error")
            return redirect(url_for("auth.login"))
        
        profile = profile_res.json()
        
        line_user_id = profile.get("userId")
        display_name = profile.get("displayName")
        email = profile.get("email")  # 如果有申請 email scope
        
        if not line_user_id:
            flash("未取得用戶ID", "error")
            return redirect(url_for("auth.login"))
        
        # 儲存或更新用戶
        user = User.query.filter_by(line_user_id=line_user_id).first()
        if not user:
            user = User(
                username=display_name, 
                email=email,
                line_user_id=line_user_id
            )
            db.session.add(user)
        else:
            # 更新現有用戶資料
            user.username = display_name
            if email:
                user.email = email
        
        db.session.commit()
        session["user_id"] = user.id
        flash(f"歡迎 {display_name or '使用者'}！", "success")
        
        return redirect(url_for("auth.profile"))
        
    except requests.RequestException as e:
        flash(f"網路連線錯誤: {str(e)}", "error")
        return redirect(url_for("auth.login"))
    except Exception as e:
        flash(f"系統錯誤: {str(e)}", "error")
        return redirect(url_for("auth.login"))

@auth_bp.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        flash("請先登入", "warning")
        return redirect(url_for("auth.login"))
    
    user = User.query.get(user_id)
    if not user:
        flash("找不到用戶資料", "error")
        session.pop("user_id", None)
        return redirect(url_for("auth.login"))
    
    return render_template("profile.html", user=user)

@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("已成功登出", "info")
    return redirect(url_for("main.index"))