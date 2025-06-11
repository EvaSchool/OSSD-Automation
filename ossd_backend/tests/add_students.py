import requests
import os

BASE_URL = "http://127.0.0.1:8080"
IMPORT_ENDPOINT = "/api/v1/students/import"
LOGIN_ENDPOINT = "/api/v1/users/login"

# 登录获取token
login_data = {
    "username": "alice",  # 请替换为你的管理员用户名
    "password": "123456"  # 请替换为你的管理员密码
}

login_response = requests.post(BASE_URL + LOGIN_ENDPOINT, json=login_data)
if login_response.status_code != 200:
    print("❌ 登录失败:", login_response.text)
    exit(1)

access_token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {access_token}"}
print("✅ 登录成功.")

# 定位studentdata.csv文件（假设在ossd_backend目录下）
file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "studentdata.csv")

with open(file_path, "rb") as f:
    files = {"file": ("studentdata.csv", f, "text/csv")}
    response = requests.post(BASE_URL + IMPORT_ENDPOINT, files=files, headers=headers)

print("状态码:", response.status_code)
try:
    print("返回内容:", response.json())
except Exception:
    print("返回内容(非json):", response.text)