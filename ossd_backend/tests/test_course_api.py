import requests

BASE_URL = "http://127.0.0.1:8080"
LOGIN_ENDPOINT = "/api/v1/users/login"
COURSES_ENDPOINT = "/api/v1/courses"

# === Step 1: Login ===
login_data = {
    "username": "admin",  # 确保你用的是管理员账户
    "password": "123456"
}

login_response = requests.post(BASE_URL + LOGIN_ENDPOINT, json=login_data)
if login_response.status_code != 200:
    print("❌ Login failed:", login_response.text)
    exit(1)

access_token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {access_token}"}
print("✅ Login successful.")

# === Step 2: Create a course ===
test_course_code = "TEST102"
new_course = {
    "course_code": test_course_code,
    "course_name": "Test Course",
    "description": "This is a test course.",
    "credit": 1.0,
    "course_level": "GRADE_11",
    "is_compulsory": True
}

create_response = requests.post(BASE_URL + COURSES_ENDPOINT, json=new_course, headers=headers)
if create_response.status_code == 201:
    print("✅ Course created successfully.")
else:
    print("❌ Failed to create course:", create_response.text)
    exit(1)

# === Step 3a: 精确 course_code 匹配查询 ===
params = {"course_code": test_course_code}
get_response = requests.get(BASE_URL + COURSES_ENDPOINT, headers=headers, params=params)
courses = get_response.json().get("data", {}).get("list", [])
found = any(c['course_code'] == test_course_code for c in courses)

if found:
    print("✅ Course found by course_code.")
else:
    print("❌ Course not found by course_code.")

# === Step 3b: 模糊 keyword 查询 ===
params = {"keyword": "TEST"}
fuzzy_response = requests.get(BASE_URL + COURSES_ENDPOINT, headers=headers, params=params)
fuzzy_courses = fuzzy_response.json().get("data", {}).get("list", [])
fuzzy_found = any(test_course_code in c['course_code'] for c in fuzzy_courses)

if fuzzy_found:
    print("✅ Course found by keyword fuzzy search.")
else:
    print("❌ Course not found by keyword fuzzy search.")

# === Step 4: Update course ===
update_data = {
    "course_name": "Updated Test Course",
    "description": "Updated description.",
    "credit": 0.5,
    "course_level": "GRADE_12",
    "is_compulsory": False
}

update_response = requests.put(f"{BASE_URL + COURSES_ENDPOINT}/{test_course_code}", json=update_data, headers=headers)
if update_response.status_code == 200:
    print("✅ Course updated successfully.")
else:
    print("❌ Failed to update course:", update_response.text)

# === Step 5: Delete course ===
# 删除现在是批量 delete，需要传 JSON 请求体
delete_data = {"course_codes": [test_course_code]}
delete_response = requests.delete(BASE_URL + COURSES_ENDPOINT, json=delete_data, headers=headers)

if delete_response.status_code == 200:
    print("✅ Course deleted successfully.")
else:
    print("❌ Failed to delete course:", delete_response.text)
