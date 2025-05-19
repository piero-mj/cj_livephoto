from django.contrib import admin
from .models import Gallery, Photo, Tag, AccessLog

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'description', 'created_at', 'updated_at')
    list_filter = ('date', 'created_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('gallery', 'original', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'gallery')
    search_fields = ('metadata__original_name', 'gallery__name')
    date_hierarchy = 'created_at'
    filter_horizontal = ('tags',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('gallery', 'visitor_name', 'ip_address', 'accessed_at')
    list_filter = ('gallery', 'accessed_at')
    search_fields = ('visitor_name', 'gallery__name')
    date_hierarchy = 'accessed_at'
