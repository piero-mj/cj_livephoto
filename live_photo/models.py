from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinLengthValidator, MaxLengthValidator
import os
import uuid
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def gallery_photo_path(instance, filename):
    """生成照片存储路径"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('live_photo_gallary', instance.gallery.name, 'original', filename)

def gallery_thumbnail_path(instance, filename):
    """生成缩略图存储路径"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}_thumb.{ext}"
    return os.path.join('live_photo_gallary', instance.gallery.name, 'thumbnails', filename)

class Gallery(models.Model):
    """相册模型"""
    name = models.CharField(
        '相册名称',
        max_length=100,
        unique=True,
        validators=[
            MinLengthValidator(1, message='相册名称不能为空'),
            MaxLengthValidator(100, message='相册名称不能超过100个字符')
        ],
        help_text='相册名称（支持emoji表情）'
    )
    date = models.DateField('日期', null=True, blank=True)
    description = models.TextField('描述', blank=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    cover_photo = models.ForeignKey('Photo', null=True, blank=True, on_delete=models.SET_NULL, related_name='cover_of_galleries', verbose_name='封面照片')

    class Meta:
        verbose_name = '相册'
        verbose_name_plural = '相册'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def clean(self):
        """验证相册名称"""
        super().clean()
        if not self.name:
            raise ValidationError({'name': '相册名称不能为空'})
        if len(self.name) > 100:
            raise ValidationError({'name': '相册名称不能超过100个字符'})

class Tag(models.Model):
    """标签模型"""
    name = models.CharField('标签名称', max_length=50, unique=True)
    created_at = models.DateTimeField('创建时间', default=timezone.now)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['name']

    def __str__(self):
        return self.name

class Photo(models.Model):
    """照片模型"""
    STATUS_CHOICES = (
        ('visible', '显示'),  # 默认状态
        ('hidden', '隐藏'),
        ('pending', '待补充'),
    )

    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name='photos', verbose_name='所属相册')
    original = models.ImageField('原图', upload_to=gallery_photo_path)
    thumbnail = models.ImageField('缩略图', upload_to=gallery_thumbnail_path)
    metadata = models.JSONField('元数据', default=dict)  # 存储原始文件名、大小等信息
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='visible')
    tags = models.ManyToManyField(Tag, blank=True, related_name='photos', verbose_name='标签')
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '照片'
        verbose_name_plural = '照片'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.metadata.get('original_name', '未命名')} - {self.gallery.name}"

    def save(self, *args, **kwargs):
        """保存时自动生成缩略图"""
        if not self.pk:  # 只在创建时处理
            # 这里可以添加生成缩略图的逻辑
            pass
        super().save(*args, **kwargs)

class AccessLog(models.Model):
    """访问日志模型"""
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name='access_logs', verbose_name='相册')
    visitor_name = models.CharField('访问者姓名', max_length=100)
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user_agent = models.TextField('用户代理', blank=True)
    accessed_at = models.DateTimeField('访问时间', default=timezone.now)

    class Meta:
        verbose_name = '访问日志'
        verbose_name_plural = '访问日志'
        ordering = ['-accessed_at']

    def __str__(self):
        return f"{self.visitor_name} - {self.gallery.name} - {self.accessed_at}"