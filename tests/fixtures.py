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


class AsyncMockResponse:
    """Fake async response object."""

    def __init__(self, status=200, body=None, json=None):
        self.status = status
        self._body = body
        self._json = json

    async def json(self):
        return self._json

    def raise_for_status(self):
        pass


class MockAsyncSession:
    """Fake aiohttp.AsyncSession object."""

    def __init__(self, get):
        self.get = get

    async def get(self):
        return self.get
