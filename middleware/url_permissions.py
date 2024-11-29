from django.shortcuts import redirect
from django.urls import reverse

class URLPermissionMiddleware:
    """
    Middleware to enforce URL-based permissions for logged-in users.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Define public URLs that don't require permission checks
        public_urls = [
            reverse("login"),
            "/captcha/",
        ]

        # Allow requests to public URLs
        if any(request.path.startswith(url) for url in public_urls):
            return self.get_response(request)

        # Allow superusers unrestricted access
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        # Skip permission checks if user is not authenticated
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Skip permission checks if restrictions are disabled
        if not request.user.enforce_url_restrictions:
            return self.get_response(request)

        # Enforce URL restrictions for authenticated users
        allowed_urls = request.user.allowed_urls or []
        if not any(request.path.startswith(url) for url in allowed_urls):
            # Redirect to an "Access Denied" page if access is restricted
            return redirect(reverse("access_denied"))

        # Pass the request to the next middleware or view
        return self.get_response(request)
