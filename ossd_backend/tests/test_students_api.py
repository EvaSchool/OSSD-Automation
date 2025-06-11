import requests
import os

BASE_URL = "http://127.0.0.1:8080"
LOGIN_ENDPOINT = "/api/v1/users/login"
IMPORT_ENDPOINT = "/api/v1/students/import"

# === Step 1: Login and get access token ===
login_data = {
    "username": "alice",
    "password": "123456"
}

login_response = requests.post(BASE_URL + LOGIN_ENDPOINT, json=login_data)
if login_response.status_code != 200:
    print("❌ Login failed:", login_response.text)
    exit(1)

access_token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {access_token}"}
print("✅ Login successful.")

# === Step 2: 批量导入studentdata.csv ===
file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "studentdata.csv")

with open(file_path, "rb") as f:
    files = {"file": ("studentdata.csv", f, "text/csv")}
    response = requests.post(BASE_URL + IMPORT_ENDPOINT, files=files, headers=headers)

print("状态码:", response.status_code)
try:
    print("返回内容:", response.json())
except Exception:
    print("返回内容(非json):", response.text)

'''
# === Step 2: Create a test student ===
test_OEN = "123456789"
new_student = {
    "last_name": "Test",
    "first_name": "Student",
    "OEN": test_OEN,
    "birth_year": 2005,
    "birth_month": "JAN",  # ✅ MUST BE UPPERCASE
    "birth_day": 15,
    "enrollment_year": 2022,
    "enrollment_month": "SEP",  # ✅ MUST BE UPPERCASE
    "enrollment_day": 1,
    "expected_graduation_year": 2026,
    "expected_graduation_month": "JUN",  # ✅ MUST BE UPPERCASE
    "expected_graduation_day": 30,
    "address": "123 Test Street",
    "graduation_status": "IN_PROGRESS",  # ✅ MUST BE UPPERCASE
    "volunteer_hours": 10
}

create_response = requests.post(BASE_URL + STUDENTS_ENDPOINT, json=new_student, headers=headers)
if create_response.status_code != 201:
    print("❌ Failed to create student:", create_response.text)
    exit(1)

created_student = create_response.json()
student_id = created_student["student_id"]
print(f"✅ Student created with ID {student_id}")

# === Step 3: Confirm student exists in the list ===
list_response = requests.get(BASE_URL + STUDENTS_ENDPOINT, headers=headers)
if list_response.status_code == 200:
    students = list_response.json()
    found = any(s['OEN'] == test_OEN for s in students)
    if found:
        print("✅ Student found in list.")
    else:
        print("❌ Student not found in list.")
else:
    print("❌ Failed to fetch students:", list_response.text)

# === Step 4: Delete the test student ===
#delete_response = requests.delete(f"{BASE_URL}{STUDENTS_ENDPOINT}/{student_id}", headers=headers)
#if delete_response.status_code == 204:
#    print("✅ Student deleted.")
#else:
#    print("❌ Failed to delete student:", delete_response.text)

# === Step 5: Confirm student no longer exists ===
list_after_delete = requests.get(BASE_URL + STUDENTS_ENDPOINT, headers=headers)
if list_after_delete.status_code == 200:
    students_after = list_after_delete.json()
    still_exists = any(s['OEN'] == test_OEN for s in students_after)
    if not still_exists:
        print("✅ Student successfully removed from list.")
    else:
        print("❌ Student still exists after deletion.")
else:
    print("❌ Failed to fetch students after deletion:", list_after_delete.text)

print("\n=== Extra Enum Validation Tests ===")

# 1. Lowercase and spaced enum values should work (normalize_enum_input will fix them)
test_enum_case_student = {
    **new_student,
    "OEN": "987654321",
    "birth_month": "jan",  # lowercase
    "enrollment_month": "sep",  # lowercase
    "expected_graduation_month": "jun",  # lowercase
    "graduation_status": "in progress",  # with space
}
response = requests.post(BASE_URL + STUDENTS_ENDPOINT, json=test_enum_case_student, headers=headers)
if response.status_code == 201:
    print("✅ Enum normalization (lowercase/spaced) works.")
    sid = response.json()["student_id"]
    # cleanup
    requests.delete(f"{BASE_URL}{STUDENTS_ENDPOINT}/{sid}", headers=headers)
else:
    print("❌ Enum normalization failed:", response.text)


# 2. Invalid month should fail
invalid_month_student = {
    **new_student,
    "OEN": "111222333",
    "birth_month": "JXX",  # invalid month
}
response = requests.post(BASE_URL + STUDENTS_ENDPOINT, json=invalid_month_student, headers=headers)
if response.status_code == 400 and "JXX" in response.text:
    print("✅ Invalid month correctly rejected.")
else:
    print("❌ Invalid month test failed:", response.text)


# 3. Invalid graduation status should fail
invalid_status_student = {
    **new_student,
    "OEN": "444555666",
    "graduation_status": "FINISHED"  # not a valid Enum
}
response = requests.post(BASE_URL + STUDENTS_ENDPOINT, json=invalid_status_student, headers=headers)
if response.status_code == 400 and "FINISHED" in response.text:
    print("✅ Invalid graduation status correctly rejected.")
else:
    print("❌ Invalid graduation status test failed:", response.text)
'''