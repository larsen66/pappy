class TestingModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.testing = True
        response = self.get_response(request)
        return response 