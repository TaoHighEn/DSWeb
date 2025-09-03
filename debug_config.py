# debug_config.py - 用來檢查設定的腳本
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv('.env')

print("=== LINE Login 設定檢查 ===")
print(f"LINE_CHANNEL_ID: {os.environ.get('LINE_CHANNEL_ID', '❌ 未設定')}")
print(f"LINE_CHANNEL_SECRET: {'✅ 已設定' if os.environ.get('LINE_CHANNEL_SECRET') else '❌ 未設定'}")
print(f"LINE_REDIRECT_URI: {os.environ.get('LINE_REDIRECT_URI', '❌ 未設定')}")
print(f"OAUTH_SCOPE: {os.environ.get('OAUTH_SCOPE', 'profile openid')}")

# 檢查重導向URI格式
redirect_uri = os.environ.get('LINE_REDIRECT_URI')
if redirect_uri:
    if redirect_uri.startswith('http://localhost:5000'):
        print("✅ 重導向URI格式正確")
    else:
        print(f"⚠️ 重導向URI可能有問題: {redirect_uri}")
        print("   建議使用: http://localhost:5000/auth/callback")

print("\n=== 建議檢查項目 ===")
print("1. LINE Developers Console 中的 Callback URL 是否與 LINE_REDIRECT_URI 一致")
print("2. 確認正在正確的 LINE Channel 中設定")
print("3. 確認 Flask 應用程式運行在正確的端口上")
print("4. 檢查是否有多個 .env 檔案")