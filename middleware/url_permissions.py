from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse

class URLPermissionMiddleware:
    """
    Middleware to enforce URL-based permissions for logged-in users.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        public_urls = [
            reverse("login"),
            "/captcha/",
        ]

        if any(request.path.startswith(url) for url in public_urls):
            return self.get_response(request)

        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        if request.user.is_authenticated:
            allowed_urls = request.user.allowed_urls
            if not any(request.path.startswith(url) for url in allowed_urls):
                return redirect(reverse("access_denied")) 

        return self.get_response(request)
