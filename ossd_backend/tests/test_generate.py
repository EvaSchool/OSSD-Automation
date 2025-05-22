import requests
import sys
import random

print(">>> test_generate.py running")
print(">>> python executable:", sys.executable)

BASE_URL = "http://localhost:8080"
LOGIN_ENDPOINT = "/api/v1/users/login"
STUDENTS_ENDPOINT = "/api/v1/students"
GENERATE_ENDPOINT = "/api/v1/templates/{template_type}/generate/student/{student_id}"
COURSES_ENDPOINT = "/api/v1/courses"

# 登录获取token
login_data = {
    "username": "alice",
    "password": "123456"
}
print(f"[调试] 尝试登录: {BASE_URL + LOGIN_ENDPOINT}")
login_response = requests.post(BASE_URL + LOGIN_ENDPOINT, json=login_data)
access_token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {access_token}"}

# 1. 查找学生
last_name = "Chen"
first_name = "Yanhong"
resp = requests.get(
    BASE_URL + STUDENTS_ENDPOINT + f"?keyword={last_name}",
    headers=headers
)
students = resp.json().get("data", {}).get("list", [])
target_students = [stu for stu in students if stu["first_name"].lower() == first_name.lower()]
if not target_students:
    print(f"未找到学生 {last_name} {first_name}")
    exit(1)
student_id = target_students[0]["student_id"]
print(f"找到学生 {last_name} {first_name}，student_id={student_id}")

# 2. 获取所有课程
courses_resp = requests.get(BASE_URL + COURSES_ENDPOINT, headers=headers)
all_courses = courses_resp.json().get("data", {}).get("list", [])
if not all_courses:
    print("未找到任何课程")
    exit(1)

# 3. 随机选择三门课程
selected_courses = random.sample(all_courses, min(3, len(all_courses)))
print(f"随机选择的三门课程: {[c['course_code'] for c in selected_courses]}")

# 4. 需要生成的模板类型（去掉 PredictedGrades）
template_types = [
    #"ReportCard",
    #"Transcript",
    #"LetterOfEnrolment",
    #"LetterOfAcceptance",
    # "WelcomeLetter", # 可用
    #"FinalTranscript"
]

# 5. 依次生成每个文件
for tpl in template_types:
    url = BASE_URL + GENERATE_ENDPOINT.format(template_type=tpl, student_id=student_id)
    # 对于 WelcomeLetter，需要传入课程代码列表
    if tpl == "WelcomeLetter":
        print("[调试] selected_courses:", selected_courses)
        resp = requests.post(url, headers=headers, json={"course_codes": [c["course_code"] for c in selected_courses]})
    else:
        resp = requests.post(url, headers=headers, json={})
    if resp.status_code == 200:
        print(f"✅ {tpl} 生成成功，文件已保存在服务器 generated_docs 目录下")
    else:
        print(f"❌ {tpl} 生成失败：{resp.text}")