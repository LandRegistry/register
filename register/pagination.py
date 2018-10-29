from register.exceptions import ApplicationError
from flask import request
from functools import wraps


class PaginatedResource(object):
    def __init__(self):
        self.start = int(request.args.get('start', 0))
        self.limit = int(request.args.get('limit', 50))
        self.count = None

    def add_headers(self, headers=None):
        if self.count is None:
            raise ApplicationError("Count not set on PaginatedResource", "WGAF")

        if headers is None:
            headers = {}
        headers['Link'] = self._get_link_header()
        return headers

    def set_count(self, count):
        self.count = count

    def _get_link_header(self):
        headers = []

        if self.start > 0:
            prev_start = self.start - self.limit
            if prev_start < 0:
                prev_start = 0
            value = '?start={}&limit={}'.format(prev_start, self.limit)
            headers.append('<{}>; rel="{}"'.format(value, 'previous'))

        if self.start + self.limit < self.count:
            next_start = self.start + self.limit
            next_limit = self.limit
            if next_start + self.limit > self.count:
                next_limit -= (next_start + self.limit) - self.count
            value = '?start={}&limit={}'.format(next_start, next_limit)
            headers.append('<{}>; rel="{}"'.format(value, 'next'))

        return ','.join(headers)


def paginated_resource(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        page = PaginatedResource()
        resp = f(page, *args, **kwargs)
        resp.headers = page.add_headers(resp.headers)
        return resp
    return decorated
