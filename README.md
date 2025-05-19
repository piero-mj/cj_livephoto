# CJ Live Photo Gallery

一个基于 Django 的照片直播系统，支持相册管理、照片上传和展示功能。

## 功能特性

### 已实现功能 ✅

#### 1. 相册管理
- 相册基本属性：名称、时间、描述、访问链接
- 相册 CRUD 操作（支持 PC/移动端）
- Django admin 后台管理
- 相册列表展示与搜索
- 相册封面管理（支持选择相册内照片作为封面）

#### 2. 照片管理
- 照片上传
  - 支持单张/批量上传
  - 支持常见图片格式（jpg, png, gif）
  - 上传结果反馈
  - 自动生成缩略图
  - 文件大小和格式验证
- 照片操作
  - 状态管理（隐藏/显示/待补充）
  - 批量操作（下载/删除/隐藏/显示）
  - 标签管理（创建分类标签、批量打标签）
  - 单张照片操作（隐藏/显示、删除、设为封面）
- 照片筛选
  - 按状态筛选
  - 按标签筛选

#### 3. 照片展示
- 用户端照片展示界面
  - 瀑布流/网格布局（支持切换）
  - 照片大图查看（模态框展示）
  - 照片下载功能
  - 移动端适配（响应式设计）
  - 照片排序功能
  - 自动加载新照片

#### 4. 用户认证
- 管理员登录/登出
- 访问控制
- 用户状态显示
- 登录状态持久化

### 待实现功能 ⏳

#### 1. 访问控制
- 权限验证（需要输入全名）
- 访问记录审计

## 技术栈

- 后端：Django 4.2.20
- 前端：Bootstrap 5
- 数据库：SQLite（开发）/ PostgreSQL（生产）
- 文件存储：本地存储（开发）/ 云存储（生产）

## 项目结构

```
CJ-livephoto/
├── manage.py              # Django 项目管理脚本
├── cj_livephoto/         # 项目配置目录
│   ├── settings.py       # 项目设置
│   ├── urls.py          # 项目 URL 配置
│   ├── asgi.py          # ASGI 配置
│   └── wsgi.py          # WSGI 配置
├── live_photo/          # 主应用目录
│   ├── models.py        # 数据模型
│   ├── views.py         # 视图函数
│   ├── urls.py          # 应用 URL 配置
│   ├── admin.py         # 管理界面配置
│   └── migrations/      # 数据库迁移文件
├── templates/           # 模板目录
│   ├── base.html       # 基础模板
│   └── live_photo/     # 应用模板
│       ├── index.html  # 首页
│       ├── gallery.html # 相册展示
│       ├── login.html  # 登录页面
│       └── admin_*.html # 管理页面
├── static/             # 静态文件目录
├── media/              # 媒体文件目录
└── requirements.txt    # 项目依赖
```

## 安装和运行

1. 克隆项目
```bash
git clone [项目地址]
cd CJ-livephoto
```

2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

5. 创建超级用户
```bash
python manage.py createsuperuser
```

6. 启动开发服务器
```bash
python manage.py runserver
```

## 访问地址

- 管理后台：http://127.0.0.1:8000/admin/
- 应用首页：http://127.0.0.1:8000/live_photo/
- 相册管理：http://127.0.0.1:8000/live_photo/admin/gallery/
- 登录页面：http://127.0.0.1:8000/live_photo/login/

## 开发计划

1. 添加访问控制和审计功能
2. 优化实时更新机制
3. 完善错误处理和日志记录
4. 添加更多的用户反馈机制
5. 优化图片加载和缓存策略

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

[待定]
