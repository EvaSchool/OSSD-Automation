# 🤝 OSSD-Automation 协作开发指南

欢迎加入项目开发！本指南适用于 EvaSchool/OSSD-Automation 项目的协作流程。

---

## ✅ 基本要求

- 每位开发者都已 clone 项目仓库：`git@github.com:EvaSchool/OSSD-Automation.git`
- 在自己的电脑上开发与测试

---

## 🪜 每次开始开发之前：

1. 打开终端进入项目目录：`cd ~/你的项目目录`
2. 拉取主分支最新代码：
   ```bash
   git pull origin main
   ```
3. 确认没有未提交的更改：
   ```bash
   git status
   ```

---

## 💻 编码和提交

### 1. 添加文件变更：
```bash
git add .
```

### 2. 提交说明：
```bash
git commit -m "你的名字: 添加了课程导入功能"
```

---

## 🔁 提交前同步主分支

在 `push` 之前一定要同步一次主分支，防止冲突：
```bash
git pull origin main
```
如果有冲突，按照 Git 提示编辑冲突文件，然后：
```bash
git add .
git commit -m "解决冲突"
```

---

## 🚀 推送代码到 GitHub

```bash
git push origin main
```

---

## 💡 小提示

- 如果同时在开发，建议互相说一声"我 push 一下"，防止冲突。
- 每次只改你负责的功能模块，避免改动对方代码。

---

## 📁 推荐文件夹结构保持清晰

```
project/
├── .git/                       # Git 版本控制文件夹（自动生成）
├── .vscode/                    # VS Code 编辑器配置（可选）
├── bin/                        # Python 虚拟环境相关目录（自动生成）
├── include/                    # Python 虚拟环境头文件（自动生成）
├── lib/                        # Python 虚拟环境库（自动生成）
├── lib64 -> lib                # lib 的软链接
├── pyvenv.cfg                  # Python 虚拟环境配置文件
│
├── run.py                      # 项目入口脚本，用于运行 Flask 应用
├── CONTRIBUTING.md             # 项目贡献指南（协作规范）
│
├── ossd_backend/               # 项目主应用目录
│   ├── app/                    # 后端 Flask 应用代码
│   │   ├── models/             # 所有数据库模型类
│   │   ├── routes/             # 所有 API 路由模块
│   │   ├── utils/              # 工具函数，如权限装饰器等
│   │   ├── __init__.py         # create_app 方法初始化 Flask 应用
│   │   └── config.py           # Flask 配置类（开发环境、生产环境等）
│   │
│   ├── frontend/               # 前端页面开发目录（React/Vue/HTML/CSS）
│   ├── generated_docs/         # 系统生成的 PDF、报告等文档
│   ├── uploads/                # 文件上传保存路径
│   ├── scripts/                # 一次性脚本，如课程批量导入
│   ├── tests/                  # 自动化测试脚本（可选）
│   ├── requirements.txt        # pip 安装依赖列表
│   ├── .env                    # 环境变量配置（例如数据库连接、密钥）
│   └── dev.db                  # 本地开发用 SQLite 数据库（如使用 MySQL 可忽略）
---

# OSSD 后台管理系统

## 项目概述
这是一个基于 Flask 的后台管理系统，主要用于管理学生、课程、文档模板等信息，并提供文档生成功能。

## 技术栈
- 后端：Flask + SQLAlchemy
- 数据库：MySQL
- 认证：JWT
- 文件存储：本地文件系统

## 已完成功能

### 1. 用户管理
- 用户注册
- 用户登录（JWT认证）
- 用户权限控制（管理员/普通用户）

### 2. 学生管理
- 学生信息的CRUD操作
- 学生列表查询（支持分页和筛选）

### 3. 课程管理
- 课程信息的CRUD操作
- 课程列表查询（支持分页和筛选）

### 4. 学生课程管理
- 学生选课/退课
- 课程状态管理
- 批量操作支持

### 5. 文档模板管理
- 模板的CRUD操作
- 模板类型管理
- 模板文件上传/下载

### 6. 操作日志系统
- 记录关键操作（创建/更新/删除）
- 支持按用户、时间、操作类型等筛选
- 仅管理员可访问

### 7. 文档生成功能
- 单个学生文档生成
- 批量学生文档生成
- 单个学生多份文档生成
- 支持多种文档类型（成绩单、入学信、录取信等）

## 待完成任务

### 1. 系统优化
- [ ] 添加缓存机制
- [ ] 优化数据库查询性能
- [ ] 添加数据库索引
- [ ] 实现定时任务（如日志清理）

### 2. 安全性增强
- [ ] 添加请求频率限制
- [ ] 完善错误处理机制
- [ ] 添加操作审计日志
- [ ] 实现敏感数据加密

### 3. 功能扩展
- [ ] 添加数据导入/导出功能
- [ ] 实现数据统计和报表
- [ ] 添加系统配置管理
- [ ] 实现用户操作指南

## 项目结构
```
ossd_backend/
├── app/
│   ├── models/          # 数据模型
│   ├── routes/          # 路由处理
│   ├── services/        # 业务逻辑
│   ├── utils/           # 工具函数
│   └── __init__.py      # 应用初始化
├── config/              # 配置文件
├── migrations/          # 数据库迁移
└── requirements.txt     # 项目依赖
```

## 开发环境设置
1. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置数据库：
- 创建MySQL数据库
- 修改配置文件中的数据库连接信息
- 运行数据库迁移：
```bash
flask db upgrade
```

4. 运行应用：
```bash
flask run
```

## API文档
主要API端点：

### 用户相关
- POST /api/v1/users/register - 用户注册
- POST /api/v1/users/login - 用户登录

### 学生相关
- GET /api/v1/students - 获取学生列表
- POST /api/v1/students - 创建学生
- GET /api/v1/students/<id> - 获取学生详情
- PUT /api/v1/students/<id> - 更新学生信息
- DELETE /api/v1/students/<id> - 删除学生

### 课程相关
- GET /api/v1/courses - 获取课程列表
- POST /api/v1/courses - 创建课程
- GET /api/v1/courses/<id> - 获取课程详情
- PUT /api/v1/courses/<id> - 更新课程信息
- DELETE /api/v1/courses/<id> - 删除课程

### 学生课程相关
- GET /api/v1/student_courses - 获取选课列表
- POST /api/v1/student_courses - 创建选课记录
- PUT /api/v1/student_courses/<id> - 更新选课状态
- DELETE /api/v1/student_courses/<id> - 删除选课记录

### 模板相关
- GET /api/v1/templates - 获取模板列表
- POST /api/v1/templates - 创建模板
- GET /api/v1/templates/<id> - 获取模板详情
- PUT /api/v1/templates/<id> - 更新模板
- DELETE /api/v1/templates/<id> - 删除模板

### 文档生成相关
- POST /api/v1/templates/<template_type>/generate/student/<student_id> - 为单个学生生成文档
- POST /api/v1/templates/<template_type>/generate/batch - 批量生成文档
- POST /api/v1/templates/generate/student/<student_id>/packages - 为单个学生生成多个文档

### 操作日志相关（仅管理员）
- GET /api/v1/operation-logs - 获取操作日志列表
- GET /api/v1/operation-logs/<id> - 获取单个日志详情
- GET /api/v1/operation-logs/user/<user_id> - 获取用户操作日志
- GET /api/v1/operation-logs/time-range - 按时间范围查询日志

## 注意事项
1. 所有需要认证的API都需要在请求头中包含JWT令牌：
```
Authorization: Bearer <your_jwt_token>
```

2. 操作日志API仅对管理员开放，需要确保用户具有管理员权限。

3. 文件上传API需要确保上传目录具有正确的写入权限。

4. 数据库迁移时需要注意备份数据。

## 联系方式
如有问题，请联系项目负责人。

## 更新日志
- 2024-03-xx: 完成基础功能开发
- 2024-03-xx: 添加操作日志系统
- 2024-03-xx: 实现用户权限控制
- 2024-03-xx: 完成文档生成功能


