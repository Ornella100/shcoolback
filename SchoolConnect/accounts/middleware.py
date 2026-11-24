from django.http import JsonResponse


class ParentPortalAccessMiddleware:
    """Empêche un compte parent d'appeler les APIs destinées au personnel scolaire."""

    allowed_paths = {
        '/api/csrf/',
        '/api/login/',
        '/api/logout/',
        '/api/me/',
        '/api/password-reset/',
        '/api/password-reset/confirm/',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (
            user
            and user.is_authenticated
            and getattr(user, 'account_type', None) == 'PARENT'
            and request.path.startswith('/api/')
            and request.path not in self.allowed_paths
            and not request.path.startswith('/api/parent-portal/')
        ):
            return JsonResponse(
                {'detail': "Cette API n'est pas accessible depuis un compte parent."},
                status=403,
            )
        return self.get_response(request)
