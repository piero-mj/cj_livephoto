from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
from django.db.models import Q
from .models import Gallery, Photo, Tag, AccessLog
from PIL import Image
import os
import json
from datetime import datetime
import zipfile
from io import BytesIO
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def create_thumbnail(image_path, size=(200, 200)):
    """创建缩略图"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size)
            # 生成缩略图路径
            thumb_path = image_path.replace('original', 'thumbnails')
            # 确保缩略图目录存在
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
            # 保存缩略图
            img.save(thumb_path, "JPEG")
            return thumb_path
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None

@csrf_exempt
@login_required
def create_gallery(request):
    """创建相册 API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            date = data.get('date')
            
            # 验证相册名称
            if not name:
                return JsonResponse({
                    'status': 'error',
                    'message': '相册名称不能为空'
                }, status=400)
            
            # 验证相册名称长度
            if len(name) > 100:
                return JsonResponse({
                    'status': 'error',
                    'message': '相册名称不能超过100个字符'
                }, status=400)
            
            # 检查相册名是否已存在（使用精确匹配）
            existing_gallery = Gallery.objects.filter(name=name).first()
            if existing_gallery:
                return JsonResponse({
                    'status': 'error',
                    'message': f'相册名称"{name}"已存在，请使用其他名称',
                    'existing_gallery': {
                        'id': existing_gallery.id,
                        'name': existing_gallery.name,
                        'created_at': existing_gallery.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                }, status=400)
            
            # 处理日期
            if not date:
                date = timezone.now().date()
            else:
                if isinstance(date, str):
                    try:
                        date = datetime.strptime(date, "%Y-%m-%d").date()
                    except ValueError:
                        return JsonResponse({
                            'status': 'error',
                            'message': '日期格式无效，请使用YYYY-MM-DD格式'
                        }, status=400)
            
            # 创建相册
            try:
                gallery = Gallery.objects.create(
                    name=name,
                    description=description,
                    date=date
                )
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
            
            # 创建相册目录
            try:
                create_gallery_directories(name)
            except Exception as e:
                # 如果目录创建失败，删除已创建的相册记录
                gallery.delete()
                return JsonResponse({
                    'status': 'error',
                    'message': f'创建相册目录失败：{str(e)}'
                }, status=500)
            
            return JsonResponse({
                'status': 'success',
                'message': '相册创建成功',
                'data': {
                    'id': gallery.id,
                    'name': gallery.name,
                    'description': gallery.description,
                    'date': gallery.date.strftime('%Y-%m-%d'),
                    'created_at': gallery.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': '无效的请求数据格式'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'创建相册失败：{str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': '方法不允许'
    }, status=405)

@csrf_exempt
@login_required
def upload_photos(request, gallery_name):
    """上传照片"""
    if request.method == 'POST':
        try:
            # 解码 URL 编码的相册名称
            decoded_name = unquote(gallery_name)
            logger.info(f"Original gallery_name: {gallery_name}")
            logger.info(f"Decoded gallery_name: {decoded_name}")
            
            # 尝试查找相册
            try:
                gallery = Gallery.objects.get(name=decoded_name)
                logger.info(f"Found gallery: {gallery.name}")
            except Gallery.DoesNotExist:
                logger.error(f"Gallery not found: {decoded_name}")
                # 列出所有相册名称，用于调试
                all_galleries = Gallery.objects.values_list('name', flat=True)
                logger.error(f"Available galleries: {list(all_galleries)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'相册"{decoded_name}"不存在',
                    'debug_info': {
                        'requested_name': decoded_name,
                        'available_galleries': list(all_galleries)
                    }
                }, status=404)
            
            files = request.FILES.getlist('photos')
            
            if not files:
                logger.warning("No files uploaded")
                return JsonResponse({
                    'status': 'error',
                    'message': '没有上传文件'
                }, status=400)
            
            uploaded_photos = []
            failed_photos = []
            
            for file in files:
                try:
                    # 验证文件类型
                    if not file.content_type.startswith('image/'):
                        failed_photos.append({
                            'name': file.name,
                            'error': '不支持的文件类型'
                        })
                        continue
                    
                    # 验证文件大小（例如限制为100MB）
                    if file.size > 100 * 1024 * 1024:
                        failed_photos.append({
                            'name': file.name,
                            'error': '文件大小超过限制'
                        })
                        continue
                    
                    # 保存原始图片
                    photo = Photo.objects.create(
                        gallery=gallery,
                        original=file,
                        metadata={
                            'original_name': file.name,
                            'size': file.size,
                            'content_type': file.content_type
                        }
                    )
                    
                    # 创建缩略图
                    image_path = os.path.join(settings.MEDIA_ROOT, photo.original.name)
                    thumb_path = create_thumbnail(image_path)
                    if thumb_path:
                        photo.thumbnail = thumb_path.replace(settings.MEDIA_ROOT, '')
                        photo.save()
                    
                    uploaded_photos.append({
                        'id': photo.id,
                        'image_url': photo.original.url,
                        'thumbnail_url': photo.thumbnail.url if photo.thumbnail else '',
                        'uploaded_at': photo.created_at
                    })
                except Exception as e:
                    failed_photos.append({
                        'name': file.name,
                        'error': str(e)
                    })
            
            if uploaded_photos:
                return JsonResponse({
                    'status': 'success',
                    'message': f'成功上传 {len(uploaded_photos)} 张照片',
                    'data': {
                        'uploaded_photos': uploaded_photos,
                        'failed_photos': failed_photos
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': '没有照片上传成功',
                    'data': {
                        'failed_photos': failed_photos
                    }
                }, status=400)
                
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': f'上传失败：{str(e)}'
            }, status=500)
            
    return JsonResponse({
        'status': 'error',
        'message': '方法不允许'
    }, status=405)

@csrf_exempt
def batch_operation(request, gallery_name):
    """批量操作照片"""
    if request.method == 'POST':
        try:
            gallery = get_object_or_404(Gallery, name=gallery_name)
            data = json.loads(request.body)
            operation = data.get('operation')
            photo_ids = data.get('photo_ids', [])
            
            if not photo_ids:
                return JsonResponse({'error': '未选择照片'}, status=400)
            
            photos = Photo.objects.filter(id__in=photo_ids, gallery=gallery)
            
            if operation == 'delete':
                # 批量删除
                deleted_photos = []
                for photo in photos:
                    try:
                        # 删除原图和缩略图
                        if photo.original:
                            default_storage.delete(photo.original.name)
                        if photo.thumbnail:
                            default_storage.delete(photo.thumbnail.name)
                        photo.delete()
                        deleted_photos.append(photo.id)
                    except Exception as e:
                        return JsonResponse({
                            'error': f'删除照片 {photo.id} 失败: {str(e)}'
                        }, status=500)
                
                return JsonResponse({
                    'message': f'成功删除 {len(deleted_photos)} 张照片',
                    'deleted_photos': deleted_photos
                })
                
            elif operation == 'hide':
                # 批量隐藏/显示
                status = data.get('status', 'hidden')
                photos.update(status=status)
                return JsonResponse({
                    'message': f'成功更新 {len(photo_ids)} 张照片状态',
                    'updated_photos': photo_ids
                })
                
            elif operation == 'download':
                # 批量下载
                memory_file = BytesIO()
                with zipfile.ZipFile(memory_file, 'w') as zf:
                    for photo in photos:
                        if photo.original:
                            file_path = os.path.join(settings.MEDIA_ROOT, photo.original.name)
                            if os.path.exists(file_path):
                                zf.write(file_path, os.path.basename(photo.original.name))
                
                memory_file.seek(0)
                return FileResponse(
                    memory_file,
                    as_attachment=True,
                    filename=f'{gallery_name}_photos.zip'
                )
            
            elif operation == 'tag':
                # 批量打标签
                tag_ids = data.get('tag_ids', [])
                for photo in photos:
                    photo.tags.set(tag_ids)
                return JsonResponse({
                    'message': f'成功为 {len(photo_ids)} 张照片打标签',
                    'updated_photos': photo_ids
                })
            
            return JsonResponse({'error': '不支持的操作'}, status=400)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': '方法不允许'}, status=405)

@csrf_exempt
def manage_tags(request):
    """标签管理"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tag_name = data.get('name')
            
            if not tag_name:
                return JsonResponse({'error': '标签名称不能为空'}, status=400)
            
            tag, created = Tag.objects.get_or_create(name=tag_name)
            return JsonResponse({
                'id': tag.id,
                'name': tag.name,
                'created': created
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    elif request.method == 'GET':
        try:
            tags = Tag.objects.all()
            return JsonResponse({
                'tags': [{'id': tag.id, 'name': tag.name} for tag in tags]
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': '方法不允许'}, status=405)

@csrf_exempt
def photo_tags(request, photo_id):
    """照片标签操作"""
    try:
        photo = get_object_or_404(Photo, id=photo_id)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            tag_ids = data.get('tag_ids', [])
            photo.tags.set(tag_ids)
            return JsonResponse({
                'message': '标签更新成功',
                'tags': [{'id': tag.id, 'name': tag.name} for tag in photo.tags.all()]
            })
            
        elif request.method == 'GET':
            return JsonResponse({
                'tags': [{'id': tag.id, 'name': tag.name} for tag in photo.tags.all()]
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
        
    return JsonResponse({'error': '方法不允许'}, status=405)

@csrf_exempt
def verify_access(request, gallery_name):
    """验证访问权限"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            
            if not first_name or not last_name:
                return JsonResponse({'error': '请输入全名'}, status=400)
            
            # 记录访问日志
            AccessLog.objects.create(
                gallery_name=gallery_name,
                visitor_name=f"{first_name} {last_name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({'message': '验证成功'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': '方法不允许'}, status=405)

@csrf_exempt
def get_gallery_photos(request, gallery_name):
    """获取相册照片"""
    try:
        # 解码 URL 编码的相册名称
        decoded_name = unquote(gallery_name)
        # 处理 HTML 实体
        decoded_name = decoded_name.replace('&amp;', '&')
        logger.info(f"Original gallery_name: {gallery_name}")
        logger.info(f"Decoded gallery_name: {decoded_name}")
        
        # 尝试查找相册
        try:
            gallery = Gallery.objects.get(name=decoded_name)
            logger.info(f"Found gallery: {gallery.name}")
        except Gallery.DoesNotExist:
            logger.error(f"Gallery not found: {decoded_name}")
            # 列出所有相册名称，用于调试
            all_galleries = Gallery.objects.values_list('name', flat=True)
            logger.error(f"Available galleries: {list(all_galleries)}")
            return JsonResponse({
                'status': 'error',
                'message': f'相册"{decoded_name}"不存在',
                'debug_info': {
                    'requested_name': decoded_name,
                    'available_galleries': list(all_galleries)
                }
            }, status=404)
        
        # 获取分页参数
        page = int(request.GET.get('page', 1))
        per_page = 20  # 每页显示20张照片
        
        # 获取排序参数
        sort_order = request.GET.get('sort', 'desc')  # 默认从晚到早
        
        # 获取可见照片并根据排序参数排序
        photos = gallery.photos.filter(status='visible')
        if sort_order == 'asc':
            photos = photos.order_by('created_at')  # 从早到晚
        else:
            photos = photos.order_by('-created_at')  # 从晚到早
        
        # 分页
        paginator = Paginator(photos, per_page)
        try:
            photos_page = paginator.page(page)
        except EmptyPage:
            return JsonResponse({
                'status': 'success',
                'photos': [],
                'has_more': False
            })
        
        return JsonResponse({
            'status': 'success',
            'photos': [{
                'id': photo.id,
                'image_url': photo.original.url if photo.original else '',
                'thumbnail_url': photo.thumbnail.url if photo.thumbnail else '',
                'uploaded_at': photo.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'metadata': photo.metadata,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in photo.tags.all()]
            } for photo in photos_page],
            'has_more': photos_page.has_next()
        })
    except Exception as e:
        logger.error(f"Error in get_gallery_photos: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
def gallery_view(request, gallery_name):
    """相册页面视图"""
    try:
        # 解码 URL 编码的相册名称
        decoded_name = unquote(gallery_name)
        # 处理 HTML 实体
        decoded_name = decoded_name.replace('&amp;', '&')
        logger.info(f"Original gallery_name: {gallery_name}")
        logger.info(f"Decoded gallery_name: {decoded_name}")
        
        # 尝试查找相册
        try:
            gallery = Gallery.objects.get(name=decoded_name)
            logger.info(f"Found gallery: {gallery.name}")
        except Gallery.DoesNotExist:
            logger.error(f"Gallery not found: {decoded_name}")
            # 列出所有相册名称，用于调试
            all_galleries = Gallery.objects.values_list('name', flat=True)
            logger.error(f"Available galleries: {list(all_galleries)}")
            return JsonResponse({
                'status': 'error',
                'message': f'相册"{decoded_name}"不存在',
                'debug_info': {
                    'requested_name': decoded_name,
                    'available_galleries': list(all_galleries)
                }
            }, status=404)
        
        return render(request, 'live_photo/gallery.html', {
            'gallery': gallery
        })
    except Exception as e:
        logger.error(f"Error in gallery_view: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
def admin_gallery(request):
    """相册管理页面"""
    galleries = Gallery.objects.all().order_by('-created_at')
    return render(request, 'live_photo/admin_gallery.html', {
        'galleries': galleries
    })

@csrf_exempt
def admin_photos(request, gallery_name):
    """照片管理页面"""
    gallery = get_object_or_404(Gallery, name=gallery_name)
    photos = Photo.objects.filter(gallery=gallery).order_by('-created_at')
    tags = Tag.objects.all()
    return render(request, 'live_photo/admin_photos.html', {
        'gallery': gallery,
        'photos': photos,
        'tags': tags
    })

@csrf_exempt
def index(request):
    """首页视图，显示所有相册"""
    galleries = Gallery.objects.all().order_by('-created_at')
    today = timezone.now().date()
    return render(request, 'live_photo/index.html', {
        'galleries': galleries,
        'today': today,
    })

def admin_gallery_list(request):
    """相册管理页面"""
    galleries = Gallery.objects.all()
    today = timezone.now().date()
    return render(request, 'live_photo/admin_gallery.html', {
        'galleries': galleries,
        'today': today,
    })

@csrf_exempt
@require_POST
def create_gallery(request):
    """创建相册（管理）"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            date = data.get('date')
            if not date:
                date = timezone.now().date()
            description = data.get('description', '').strip()
            if not name:
                return JsonResponse({'error': '相册名称不能为空'}, status=400)
            if Gallery.objects.filter(name=name).exists():
                return JsonResponse({'error': '相册名称已存在'}, status=400)
            gallery = Gallery.objects.create(name=name, date=date, description=description)
            return JsonResponse({'success': True, 'id': gallery.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@require_POST
def update_gallery(request, gallery_id):
    """更新相册"""
    gallery = get_object_or_404(Gallery, id=gallery_id)
    try:
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, '相册名称不能为空')
            return redirect('admin_gallery_list')
        
        # 检查相册名是否已存在（排除当前相册）
        existing_gallery = Gallery.objects.filter(name=name).exclude(id=gallery_id).first()
        if existing_gallery:
            messages.error(request, f'相册名称"{name}"已存在，请使用其他名称')
            return redirect('admin_gallery_list')
        
        # 更新相册信息
        gallery.name = name
        gallery.description = description
        gallery.save()
        
        messages.success(request, '相册更新成功')
    except Exception as e:
        logger.error(f"Error updating gallery: {str(e)}", exc_info=True)
        messages.error(request, f'更新失败: {str(e)}')
    
    return redirect('admin_gallery_list')

@require_POST
def delete_gallery(request, gallery_id):
    """删除相册"""
    gallery = get_object_or_404(Gallery, id=gallery_id)
    try:
        # 删除相册目录
        gallery_path = os.path.join(settings.MEDIA_ROOT, 'live_photo_gallary', gallery.name)
        if os.path.exists(gallery_path):
            import shutil
            shutil.rmtree(gallery_path)
        
        gallery.delete()
        messages.success(request, '相册删除成功')
    except Exception as e:
        messages.error(request, f'删除失败: {str(e)}')
    
    return redirect('admin_gallery_list')

def admin_photos(request, gallery_name):
    """照片管理页面"""
    gallery = get_object_or_404(Gallery, name=gallery_name)
    photos = Photo.objects.filter(gallery=gallery).order_by('-created_at')
    paginator = Paginator(photos, 20)
    page = request.GET.get('page')
    photos = paginator.get_page(page)
    tags = Tag.objects.all()
    context = {
        'gallery': gallery,
        'photos': photos,
        'tags': tags,
    }
    return render(request, 'live_photo/admin_photos.html', context)

@csrf_exempt
@require_POST
def update_photo_status(request, photo_id):
    """更新单张照片状态"""
    try:
        photo = get_object_or_404(Photo, id=photo_id)
        data = json.loads(request.body)
        status = data.get('status')
        if status not in ['visible', 'hidden', 'pending']:
            return JsonResponse({'status': 'error', 'message': '无效的状态值'})
        photo.status = status
        photo.save()
        return JsonResponse({'status': 'success', 'message': '状态更新成功'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
@login_required
def set_cover_photo(request, gallery_name):
    """设置相册封面图"""
    if request.method == 'POST':
        try:
            # 解码 URL 编码的相册名称
            decoded_name = unquote(gallery_name)
            logger.info(f"Original gallery_name: {gallery_name}")
            logger.info(f"Decoded gallery_name: {decoded_name}")
            
            # 获取相册
            try:
                gallery = Gallery.objects.get(name=decoded_name)
                logger.info(f"Found gallery: {gallery.name}")
            except Gallery.DoesNotExist:
                logger.error(f"Gallery not found: {decoded_name}")
                return JsonResponse({
                    'success': False,
                    'error': f'相册"{decoded_name}"不存在'
                }, status=404)
            
            # 获取请求数据
            data = json.loads(request.body)
            photo_id = data.get('photo_id')
            
            if not photo_id:
                return JsonResponse({
                    'success': False,
                    'error': '缺少参数 photo_id'
                }, status=400)
            
            # 获取照片
            try:
                photo = Photo.objects.get(id=photo_id, gallery=gallery)
                logger.info(f"Found photo: {photo.id}")
            except Photo.DoesNotExist:
                logger.error(f"Photo not found: {photo_id}")
                return JsonResponse({
                    'success': False,
                    'error': f'照片不存在或不属于该相册'
                }, status=404)
            
            # 设置封面图
            gallery.cover_photo = photo
            gallery.save()
            
            logger.info(f"Set cover photo for gallery {gallery.name}: {photo.id}")
            return JsonResponse({
                'success': True,
                'message': '封面图设置成功',
                'data': {
                    'photo_id': photo.id,
                    'thumbnail_url': photo.thumbnail.url if photo.thumbnail else photo.original.url
                }
            })
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON data")
            return JsonResponse({
                'success': False,
                'error': '无效的请求数据'
            }, status=400)
        except Exception as e:
            logger.error(f"Error setting cover photo: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
            
    return JsonResponse({
        'success': False,
        'error': '方法不允许'
    }, status=405)

def login_view(request):
    """登录视图"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/live_photo/admin/gallery/')
            return JsonResponse({'success': True, 'redirect': next_url})
        else:
            return JsonResponse({'success': False, 'error': '用户名或密码错误'})
    
    return render(request, 'live_photo/login.html')

def logout_view(request):
    """登出视图"""
    logout(request)
    return redirect('login')

def get_user_status(request):
    """获取用户状态"""
    if request.user.is_authenticated:
        return JsonResponse({
            'is_authenticated': True,
            'username': request.user.username
        })
    return JsonResponse({
        'is_authenticated': False
    })

def create_gallery_directories(gallery_name):
    """创建相册目录结构"""
    try:
        # 使用原始相册名称，不做字符过滤
        gallery_path = os.path.join(settings.MEDIA_ROOT, 'live_photo_gallary', gallery_name)
        original_path = os.path.join(gallery_path, 'original')
        thumbnails_path = os.path.join(gallery_path, 'thumbnails')
        
        # 创建目录
        os.makedirs(original_path, exist_ok=True)
        os.makedirs(thumbnails_path, exist_ok=True)
        
        # 设置权限
        os.chmod(gallery_path, 0o755)
        os.chmod(original_path, 0o755)
        os.chmod(thumbnails_path, 0o755)
        
        return True
    except Exception as e:
        logger.error(f"Error creating gallery directories: {str(e)}", exc_info=True)
        raise 