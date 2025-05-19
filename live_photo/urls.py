from django.urls import path
from . import views

urlpatterns = [
    # ===== 用户访问路径 =====
    # 首页：显示所有相册列表
    path('', views.index, name='index'),
    
    # 相册访问
    path('gallery/<str:gallery_name>/', views.gallery_view, name='gallery_view'),
    path('gallery/<str:gallery_name>/photos/', views.get_gallery_photos, name='get_gallery_photos'),
    
    # 访问权限验证
    path('gallery/<str:gallery_name>/verify/', views.verify_access, name='verify_access'),
    
    # ===== 管理员路径 =====
    # 相册管理
    path('admin/gallery/', views.admin_gallery_list, name='admin_gallery_list'),
    path('admin/gallery/create/', views.create_gallery, name='create_gallery'),
    path('admin/gallery/<int:gallery_id>/update/', views.update_gallery, name='update_gallery'),
    path('admin/gallery/<int:gallery_id>/delete/', views.delete_gallery, name='delete_gallery'),
    
    # 照片管理
    path('admin/gallery/<str:gallery_name>/photos/', views.admin_photos, name='admin_photos'),
    path('admin/gallery/<str:gallery_name>/upload/', views.upload_photos, name='upload_photos'),
    path('admin/gallery/<str:gallery_name>/batch/', views.batch_operation, name='batch_operation'),
    path('admin/photo/<int:photo_id>/status/', views.update_photo_status, name='update_photo_status'),
    path('admin/gallery/<str:gallery_name>/set-cover/', views.set_cover_photo, name='set_cover_photo'),
    
    # 标签管理
    path('admin/tags/', views.manage_tags, name='manage_tags'),
    path('admin/photo/<int:photo_id>/tags/', views.photo_tags, name='photo_tags'),
    
    # 登录相关
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user-status/', views.get_user_status, name='user_status'),
] 