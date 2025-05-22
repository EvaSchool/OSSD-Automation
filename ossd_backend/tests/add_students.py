import requests

BASE_URL = "http://127.0.0.1:8080"
LOGIN_ENDPOINT = "/api/v1/users/login"
STUDENTS_ENDPOINT = "/api/v1/students"

# 登录获取token
login_data = {
    "username": "alice",
    "password": "123456"
}

login_response = requests.post(BASE_URL + LOGIN_ENDPOINT, json=login_data)
if login_response.status_code != 200:
    print("❌ 登录失败:", login_response.text)
    exit(1)

access_token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {access_token}"}
print("✅ 登录成功.")

# 学生数据
students_data = [
    {
        "last_name": "Wang",
        "first_name": "Kechen",
        "OEN": "816145163",
        "birth_year": 2006,
        "birth_month": "DEC",
        "birth_day": 21,
        "enrollment_year": 2025,
        "enrollment_month": "FEB",
        "enrollment_day": 24,
        "expected_graduation_year": 2025,
        "expected_graduation_month": "JUN",
        "expected_graduation_day": 30,
        "address": "China Railway Yidu International Unit E, GuiYang, GuiZhou, China",
        "graduation_status": "IN_PROGRESS",
        "volunteer_hours": 0
    },
    {
        "last_name": "Qi",
        "first_name": "Ziwen",
        "OEN": "757679436",
        "birth_year": 2007,
        "birth_month": "JUN",
        "birth_day": 8,
        "enrollment_year": 2024,
        "enrollment_month": "SEP",
        "enrollment_day": 3,
        "expected_graduation_year": 2025,
        "expected_graduation_month": "JUN",
        "expected_graduation_day": 30,
        "address": "170 Sheppard Ave E, North York, Canada",
        "graduation_status": "IN_PROGRESS",
        "volunteer_hours": 0
    },
    {
        "last_name": "Wang",
        "first_name": "Luowen",
        "OEN": "414991547",
        "birth_year": 2007,
        "birth_month": "JAN",
        "birth_day": 11,
        "enrollment_year": 2024,
        "enrollment_month": "SEP",
        "enrollment_day": 3,
        "expected_graduation_year": 2025,
        "expected_graduation_month": "JUN",
        "expected_graduation_day": 30,
        "address": "170 Sheppard Ave E, North York, Canada",
        "graduation_status": "IN_PROGRESS",
        "volunteer_hours": 0
    },
    {
        "last_name": "Lin",
        "first_name": "Keqin",
        "OEN": "199561135",
        "birth_year": 2007,
        "birth_month": "JUN",
        "birth_day": 7,
        "enrollment_year": 2024,
        "enrollment_month": "SEP",
        "enrollment_day": 3,
        "expected_graduation_year": 2025,
        "expected_graduation_month": "JUN",
        "expected_graduation_day": 30,
        "address": "170 Sheppard Ave E, North York, Canada",
        "graduation_status": "IN_PROGRESS",
        "volunteer_hours": 0
    },
    {
        "last_name": "Tang",
        "first_name": "Yonglin",
        "OEN": "875598575",
        "birth_year": 2005,
        "birth_month": "AUG",
        "birth_day": 19,
        "enrollment_year": 2024,
        "enrollment_month": "SEP",
        "enrollment_day": 3,
        "expected_graduation_year": 2025,
        "expected_graduation_month": "JUN",
        "expected_graduation_day": 30,
        "address": "170 Sheppard Ave E, North York, Canada",
        "graduation_status": "IN_PROGRESS",
        "volunteer_hours": 0
    },
    {
        "last_name": "Duan Shufan",
        "first_name": "Shufan",
        "OEN": "491840401",
        "birth_year": 2007,
        "birth_month": "JUN",
        "birth_day": 2,
        "enrollment_year": 2024,
        "enrollment_month": "SEP",
        "enrollment_day": 3,
        "expected_graduation_year": 2025,
        "expected_graduation_month": "JUN",
        "expected_graduation_day": 30,
        "address": "170 Sheppard Ave E, North York, Canada",
        "graduation_status": "IN_PROGRESS",
        "volunteer_hours": 0
    },
    {
        "last_name": "Lee",
        "first_name": "Teresa",
        "OEN": "267987964",
        "birth_year": 2005,
        "birth_month": "DEC",
        "birth_day": 5,
        "enrollment_year": 2024,
        "enrollment_month": "SEP",
        "enrollment_day": 3,
        "expected_graduation_year": 2025,
        "expected_graduation_month": "JUN",
        "expected_graduation_day": 30,
        "address": "170 Sheppard Ave E, North York, Canada",
        "graduation_status": "IN_PROGRESS",
        "volunteer_hours": 0
    },
    {
        "last_name": "Kong",
        "first_name": "Zemu",
        "OEN": "497852137",
        "birth_year": 2006,
        "birth_month": "FEB",
        "birth_day": 5,
        "enrollment_year": 2025,
        "enrollment_month": "MAR",
        "enrollment_day": 26,
        "expected_graduation_year": 2027,
        "expected_graduation_month": "JUN",
        "expected_graduation_day": 30,
        "address": "170 Sheppard Ave E, North York, Canada",
        "graduation_status": "IN_PROGRESS",
        "volunteer_hours": 0
    }
]

# 添加学生
for student in students_data:
    # 先检查OEN是否已存在
    check_response = requests.get(f"{BASE_URL}{STUDENTS_ENDPOINT}?keyword={student['OEN']}", headers=headers)
    if check_response.status_code == 200:
        existing_students = check_response.json().get('data', {}).get('list', [])
        if any(s['OEN'] == student['OEN'] for s in existing_students):
            print(f"⚠️ 学生 {student['first_name']} {student['last_name']} (OEN: {student['OEN']}) 已存在，跳过.")
            continue

    # 如果不存在，则添加
    response = requests.post(BASE_URL + STUDENTS_ENDPOINT, json=student, headers=headers)
    if response.status_code == 201:
        print(f"✅ 学生 {student['first_name']} {student['last_name']} 添加成功.")
    else:
        print(f"❌ 学生 {student['first_name']} {student['last_name']} 添加失败: {response.text}")