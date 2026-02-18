# Xmem

一个AI赋能的前后端分离的个人记账、笔记与待办管理应用。

## ✨ 功能特性

- 📝 **笔记与知识管理**：Markdown 笔记、图片/附件管理、标签与置顶、分享与权限控制
- 🧠 **AI 助手**：笔记智能摘要、从笔记提取待办事项、对话式助手
- 💰 **智能记账**：文本/图片输入，OCR 识别与 LLM 分类，支持多币种换算与统计汇总
- ✅ **待办管理**：任务组与子任务、进度与状态流转、AI 生成待办
- 📦 **导出能力**：笔记 CSV/Markdown 打包导出，带校验报告
- 🔐 **用户认证**：注册/登录、JWT 鉴权、登录审计
- 🖥️ **多端使用**：Web 与 Electron 桌面应用
- 🐳 **一键部署**：Docker Compose + Nginx 反向代理 + 证书续期

## 🛠️ 技术选型

### 前端
- **Vue 3** / **TypeScript** / **Vite**
- **Pinia** 状态管理、**Vue Router** 路由
- **Tailwind CSS** 与自定义主题
- **vue-echarts** 数据统计图表
- **md-editor-v3** Markdown 编辑与渲染
- **Axios** 请求封装、**driver.js** 引导流程

### 后端
- **FastAPI** + **Uvicorn**
- **PostgreSQL** + **SQLAlchemy**
- **Alembic** 数据库迁移
- **Celery** 异步任务 + **Redis** 消息队列
- **Tesseract OCR** 图片识别
- **Pydantic** 配置与数据校验

### 部署与运维
- **Docker Compose** 多容器编排
- **Nginx** 反向代理
- **Certbot** SSL 证书续期
- **GitHub Actions** CI/CD

## 📁 项目结构

```
Xmem/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── routers/         # API 路由（auth/notes/ledger/todos/ai/exports）
│   │   ├── services/        # 业务逻辑（AI、OCR、导出）
│   │   ├── tasks/           # Celery 任务
│   │   ├── utils/           # 通用工具
│   │   └── main.py          # 应用入口
│   ├── alembic/             # 迁移脚本
│   ├── test/                # pytest 测试
│   └── Dockerfile
├── frontend/                # Vue3 前端
│   ├── src/
│   │   ├── components/      # 业务组件
│   │   ├── views/           # 页面
│   │   ├── stores/          # Pinia
│   │   ├── api/             # API 客户端
│   │   └── utils/           # 前端工具
│   ├── tests/               # vitest 测试
│   └── Dockerfile
├── electron/                # Electron 桌面端
├── database/                # PostgreSQL Dockerfile
├── redis/                   # Redis Dockerfile
├── ssl/                     # 证书目录（由 certbot 挂载）
├── .github/workflows/       # CI/CD
├── docker-compose.yml       # 服务编排
├── DOCKER_DEPLOY.md         # 部署详细说明
└── HTTPS_MANUAL_SETUP.md    # HTTPS 手动初始化步骤
```

## 🚀 生产环境使用 Docker 部署

详细流程参见 [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md) 与 [HTTPS_MANUAL_SETUP.md](HTTPS_MANUAL_SETUP.md)。

### 1. 配置环境变量

在项目根目录创建 `.env`：

```env
# 数据库
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=xmem
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/xmem

# 鉴权
JWT_SECRET=please-change-in-production

# Redis
REDIS_URL=redis://redis:6379/0

# OCR / LLM（按需）
OCR_PROVIDER=local
TESSERACT_CMD=/usr/bin/tesseract
LLM_PROVIDER=
LLM_API_URL=
LLM_API_KEY=

# 前端
VITE_API_URL=/api
```

### 2. 启动服务

```bash
docker-compose up -d --build
```

### 3. 访问入口

- 前端：http://localhost
- API：通过 `/api/` 反向代理访问
- API 文档：如需直连，放开后端端口映射后访问 `http://localhost:8000/docs`

## 🧑‍💻 本地开发

### 后端

```bash
cd backend
uv sync
```

创建 `backend/.env`（示例）：

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/xmem
JWT_SECRET=your-secret-key
REDIS_URL=redis://localhost:6379/0
```

启动依赖服务：

```bash
docker-compose up -d db redis
```

运行后端：

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

运行 Celery Worker（需要时）：

```bash
uv run celery -A app.celery_app:celery_app worker --loglevel=info --pool=gevent --concurrency=20
```

### 前端

```bash
cd frontend
npm install
```

创建 `frontend/.env`：

```env
VITE_API_URL=http://localhost:8000
```

运行前端：

```bash
npm run dev
```

### Electron

```bash
cd electron
npm install
npm run dev
```

## 🧪 测试

### 后端（pytest）

```bash
cd backend
uv run pytest
```

### 前端（vitest）

```bash
cd frontend
npm run test:run
```

## ✅ 代码规范

- 前端：使用 TypeScript 严格模式，遵循 Vue 3 最佳实践。
  - 代码规范检查：`npm run lint`
  - typescript类型检查：`node .\node_modules\typescript\bin\tsc -p tsconfig.json --noEmit`
- 后端：遵循 PEP 8 及项目现有格式与风格约定。
  - 静态代码检查 `uv run ruff check .`

## 🤝 贡献

欢迎提交 Issue 与 Pull Request。请保证测试通过并遵循现有代码风格。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 👤 作者

Copyright (c) 2025 Xchkoo
