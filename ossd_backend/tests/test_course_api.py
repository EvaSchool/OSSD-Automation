import requests
import os

BASE_URL = "http://127.0.0.1:8080"
LOGIN_ENDPOINT = "/api/v1/users/login"
COURSES_ENDPOINT = "/api/v1/courses"

def debug_response(label, response):
    print(f"🔹 {label} | Status: {response.status_code}")
    try:
        print(f"🔹 {label} | Response JSON:", response.json())
    except:
        print(f"🔹 {label} | Raw Text:", response.text)

# === Step 1: Login ===
login_data = {
    "username": "admin",
    "password": "123456"
}

login_response = requests.post(BASE_URL + LOGIN_ENDPOINT, json=login_data)
debug_response("Login", login_response)

if login_response.status_code != 200:
    print("❌ Login failed")
    exit(1)

access_token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {access_token}"}
print("✅ Login successful.")

# === Step 2: Create a course ===
test_course_code = "TEST101"

# 先尝试删除可能存在的测试课程
delete_test_data = {"course_codes": [test_course_code]}
requests.delete(BASE_URL + COURSES_ENDPOINT, json=delete_test_data, headers=headers)

new_course = {
    "course_code": test_course_code,
    "course_name": "Equivalent Credits",
    "description": "Equivalent Credits granted through PLAR or transcript evaluation",
    "credit": 0.0,
    "course_level": '11',
    "is_compulsory": None
}

create_response = requests.post(BASE_URL + COURSES_ENDPOINT, json=new_course, headers=headers)
debug_response("Create Course", create_response)

if create_response.status_code == 201:
    print("✅ Course created successfully.")
else:
    print("❌ Failed to create course.")
    exit(1)

# === Step 3a: Get by course_code ===
params = {"course_code": test_course_code}
get_response = requests.get(BASE_URL + COURSES_ENDPOINT, headers=headers, params=params)
debug_response("Get by Course Code", get_response)
courses = get_response.json().get("data", {}).get("list", [])
found = any(c['course_code'] == test_course_code for c in courses)
print("✅ Course found by course_code." if found else "❌ Course not found by course_code.")

# === Step 3b: Keyword fuzzy search ===
params = {"keyword": "ENG"}
fuzzy_response = requests.get(BASE_URL + COURSES_ENDPOINT, headers=headers, params=params)
debug_response("Fuzzy Search", fuzzy_response)
fuzzy_courses = fuzzy_response.json().get("data", {}).get("list", [])
fuzzy_found = any(test_course_code in c['course_code'] for c in fuzzy_courses)
print("✅ Course found by keyword fuzzy search." if fuzzy_found else "❌ Course not found by keyword fuzzy search.")



# === Step 4: Update course ===
update_data = {
    "course_name": "Updated Test Course",
    "description": "Updated description.",
    "credit": 0.5,
    "course_level": "12",
    "is_compulsory": False
}
update_response = requests.put(f"{BASE_URL + COURSES_ENDPOINT}/{test_course_code}", json=update_data, headers=headers)
debug_response("Update Course", update_response)
print("✅ Course updated successfully." if update_response.status_code == 200 else "❌ Failed to update course.")

# 验证更新后的课程信息
get_response = requests.get(BASE_URL + COURSES_ENDPOINT, headers=headers, params={"course_code": test_course_code})
debug_response("Get Updated Course", get_response)
courses = get_response.json().get("data", {}).get("list", [])
if courses:
    updated_course = courses[0]
    print(f"Updated course_level: {updated_course['course_level']}")


# === Step 5: Delete course ===
delete_data = {"course_codes": [test_course_code]}
delete_response = requests.delete(BASE_URL + COURSES_ENDPOINT, json=delete_data, headers=headers)
debug_response("Delete Course", delete_response)
print("✅ Course deleted successfully." if delete_response.status_code == 200 else "❌ Failed to delete course.")

# 获取当前文件所在目录的父目录（项目根目录）
project_root = os.path.dirname(os.path.dirname(__file__))
# 尝试不同的文件扩展名
for ext in ['.xlsx', '.csv']:
    import_file_path = os.path.join(project_root, f"coursedata{ext}")
    if os.path.exists(import_file_path):
        print(f"📁 找到导入文件: {import_file_path}")
        break
else:
    print("❌ 未找到导入文件")
    exit(1)

# 以 multipart/form-data 方式上传
with open(import_file_path, "rb") as f:
    files = {
        "file": (os.path.basename(import_file_path), f)
    }

    import_response = requests.post(BASE_URL + "/api/v1/courses/import", files=files, headers=headers)

def debug_import_response(label, response):
    print(f"🔹 {label} | Status: {response.status_code}")
    try:
        res_json = response.json()
        print(f"  Created: {res_json.get('data', {}).get('created', [])}")
        print(f"  Updated: {res_json.get('data', {}).get('updated', [])}")
        print(f"  Errors: {res_json.get('data', {}).get('errors', [])}")
    except:
        print(f"🔹 {label} | Raw Text:", response.text)

# 调用打印结果
debug_import_response("Import Courses", import_response)