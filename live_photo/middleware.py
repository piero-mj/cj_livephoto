from django.shortcuts import redirect
from django.urls import reverse

class AdminAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 检查是否是管理员页面
        if request.path.startswith('/live_photo/admin/'):
            # 排除登录页面和静态文件
            if not request.path.startswith('/live_photo/admin/login/') and not request.path.startswith('/live_photo/admin/static/'):
                # 检查用户是否已登录
                if not request.user.is_authenticated:
                    # 保存当前URL到session
                    request.session['next'] = request.path
                    # 重定向到登录页面
                    return redirect('login')

        response = self.get_response(request)
        return response 