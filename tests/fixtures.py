class MockResponse:
    """Fake response object."""

    def __init__(self, status=200, body=None, json=None):
        self.status = status
        self._body = body
        self._json = json

    def json(self):
        return self._json

    def raise_for_status(self):
        pass
