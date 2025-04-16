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

- 如果同时在开发，建议互相说一声“我 push 一下”，防止冲突。
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


