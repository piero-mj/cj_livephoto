# 照片直播系统需求文档

## 一、功能需求

### 1. 相册管理功能（管理员）
#### 1.1 相册属性 ✅
- 相册名称
- 时间（支持手动选择日期）
- 描述信息
- 访问链接（域名/IP + live_photo + gallery + 相册名称）

#### 1.2 相册管理功能（管理员）✅
- 支持创建多个相册
- 支持在PC/移动端进行增删改查操作
- 支持通过Django admin后台管理
- 相册列表展示与搜索
- 相册封面显示已上传的照片缩略图（1-3张）
- 支持配置相册封面图（可选择相册内的照片，或者为空）

### 2. 照片管理功能（管理员）
#### 2.1 照片上传 ✅
- 支持单张/批量照片上传
- 支持常见图片格式（jpg, png, gif等）
- 显示上传结果（成功/失败）
- 上传失败时显示失败的文件名
- 上传成功后自动刷新显示
- 支持文件大小限制和格式验证
- 自动生成缩略图（不展示在管理界面）

#### 2.2 照片操作（管理员）✅
- 照片状态管理（隐藏/显示/待补充）
- 批量操作功能：
  - 全选/勾选
  - 批量下载
  - 批量删除
  - 批量隐藏/显示
- 标签管理：
  - 支持创建分类标签（如"人物"、"场景"）
  - 支持批量打标签
- 单张照片操作：
  - 隐藏/显示切换（通过眼睛图标）
  - 删除（同时删除原图和缩略图）
  - 设置为封面图
  - 操作按钮（隐藏/显示、删除、设为封面）全在图片下方，横向排列

#### 2.3 照片筛选功能 ✅
- 按状态筛选（全部/显示/隐藏/待补充，下拉选择）
- 按标签筛选（下拉选择，所有标签）
- 前端筛选实现

### 3. 照片展示功能（用户）
#### 3.1 访问控制 ⏳
- [待实现] 权限验证：需要输入全名（first name + last name）才能访问
- [待实现] 访问记录审计

#### 3.2 照片展示功能（用户）⏳
- 非管理员只能查看相册照片（没有上传、隐藏、删除功能或权限）
- 主要用于手机浏览器和PC浏览器场景
- 响应式设计，适配不同屏幕尺寸
- 照片自动更新（定期检查新照片）
- 支持照片缩略图显示
- 排版风格简洁、现代

相册照片展示UI（待实现）：
1. 相册部分：
   - 相册封面页
   - 相册名称
   - 相册描述

2. 照片展示部分：
   - 瀑布流布局展示照片
   - 支持点击查看大图
   - 大图下支持长按下载照片

### 4. 用户认证功能 ✅
- 管理员登录/登出
- 访问管理员页面需要登录
- 右上角显示用户状态
- 登录状态持久化

## 二、界面要求
### 2.1 已实现 ✅
- 管理员前端页面：相册和照片的增删改查、批量操作、标签管理等全部管理功能
- 色调：保持主色调（#3D365C、#7C4585、#C95792、#F8B55F）
- 排版：图片、按钮、标签等间距紧凑，视觉现代
- 清晰的标题和描述展示
- 简洁的上传界面
- 美观的照片网格布局
- 良好的用户交互体验
- 直观的管理界面
- 友好的批量操作界面

### 2.2 待实现 ⏳
- 用户前端页面：瀑布流/网格布局
- 移动端适配优化
- 照片大图查看功能
- 照片下载功能

## 三、技术实现
### 3.1 技术栈 ✅
- 后端：Django
- 前端：Bootstrap 5
- 数据库：SQLite（开发）/ PostgreSQL（生产）
- 文件存储：本地存储（开发）/ 云存储（生产）

### 3.2 技术特性
#### 3.2.1 已实现 ✅
- 异步加载和更新机制
- 支持并发上传
- 图片自动压缩和优化
- 快速加载和响应
- 批量操作性能优化
- 图片加载性能优化

#### 3.2.2 待实现 ⏳
- 实时更新功能
- 使用模态框展示大图
- 稳定的实时更新机制

## 四、性能要求
### 4.1 已实现 ✅
- 支持并发上传
- 图片自动压缩和优化
- 快速加载和响应
- 批量操作性能优化
- 图片加载性能优化

### 4.2 待优化 ⏳
- 实时更新机制的性能优化
- 大图加载的性能优化
- 移动端性能优化

## 五、后续计划
1. 实现用户端照片展示功能
2. 优化移动端适配
3. 实现照片大图查看和下载功能
4. 添加访问控制和审计功能
5. 优化实时更新机制
6. 完善错误处理和日志记录
7. 添加更多的用户反馈机制
8. 优化图片加载和缓存策略
