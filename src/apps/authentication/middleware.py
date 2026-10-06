from django.utils import translation


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                language = request.user.preferences.language
            except request.user._meta.model.preferences.RelatedObjectDoesNotExist:
                language = None

            if language:
                translation.activate(language)
                request.LANGUAGE_CODE = language

        return self.get_response(request)
