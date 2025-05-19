from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Gallery, Photo
import os
import json
from datetime import datetime

class PhotoLiveGalleryTests(TestCase):
    def setUp(self):
        # 创建测试用的图库
        self.gallery = Gallery.objects.create(
            name="测试图库",
            description="这是一个测试图库"
        )
        
        # 创建测试客户端
        self.client = Client()
        
        # 创建测试图片文件
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )

    def test_gallery_creation(self):
        """测试图库创建功能"""
        self.assertEqual(self.gallery.name, "测试图库")
        self.assertEqual(self.gallery.description, "这是一个测试图库")
        self.assertTrue(isinstance(self.gallery, Gallery))

    def test_photo_upload(self):
        """测试照片上传功能"""
        # 测试单张照片上传
        response = self.client.post(
            reverse('upload_photos', kwargs={'gallery_name': self.gallery.name}),
            {'photos': self.test_image}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Photo.objects.filter(gallery=self.gallery).exists())

    def test_photo_list_view(self):
        """测试照片列表视图"""
        # 先上传一张照片
        photo = Photo.objects.create(
            gallery=self.gallery,
            image=self.test_image,
            uploaded_at=datetime.now()
        )

        # 测试获取照片列表
        response = self.client.get(
            reverse('gallery_photos', kwargs={'gallery_name': self.gallery.name})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['photos']), 1)

    def test_gallery_view(self):
        """测试图库页面访问"""
        response = self.client.get(
            reverse('gallery_view', kwargs={'gallery_name': self.gallery.name})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'live_photo/gallery.html')

    def test_invalid_gallery(self):
        """测试访问不存在的图库"""
        response = self.client.get(
            reverse('gallery_view', kwargs={'gallery_name': '不存在的图库'})
        )
        self.assertEqual(response.status_code, 404)

    def test_photo_ordering(self):
        """测试照片排序功能"""
        # 创建多张照片
        for i in range(3):
            Photo.objects.create(
                gallery=self.gallery,
                image=self.test_image,
                uploaded_at=datetime.now()
            )

        # 获取照片列表
        response = self.client.get(
            reverse('gallery_photos', kwargs={'gallery_name': self.gallery.name})
        )
        data = json.loads(response.content)
        
        # 验证照片按上传时间倒序排列
        photos = data['photos']
        self.assertEqual(len(photos), 3)
        for i in range(len(photos)-1):
            self.assertGreater(
                datetime.fromisoformat(photos[i]['uploaded_at'].replace('Z', '+00:00')),
                datetime.fromisoformat(photos[i+1]['uploaded_at'].replace('Z', '+00:00'))
            )

    def tearDown(self):
        # 清理测试文件
        for photo in Photo.objects.all():
            if photo.image:
                if os.path.isfile(photo.image.path):
                    os.remove(photo.image.path)
