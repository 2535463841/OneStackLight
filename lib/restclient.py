import http.client as httplib
import json
import logging
import ssl

from simplelib.httpclient import httperror

LOG = logging.getLogger(name=__name__)


class Response(object):

    def __init__(self, status, headers, content):
        self.status = status
        self.headers = headers
        self._content = content

    @property
    def content(self):
        if self._content:
            if isinstance(self._content, dict):
                return self._content
            try:
                return json.loads(self._content)
            except ValueError:
                pass
        return self._content

    def __str__(self):
        return '[%s] headers=%s, content=%s' % (
            self.status, self.headers, self._content)


class RestClient(object):

    def __init__(self, scheme, host, port, timeout=60):
        self.scheme = scheme
        self.host = host
        self.port = port
        self.timeout = timeout
        if self.scheme not in ['http', 'https']:
            raise ValueError("scheme must be http or https")

        if self.scheme == 'https':
            ssl._create_default_https_context = \
                ssl._create_unverified_context                  # noqa
            self.connection = httplib.HTTPSConnection(self.host, self.port,
                                                      timeout=self.timeout)
        else:
            self.connection = httplib.HTTPConnection(self.host, self.port,
                                                     timeout=self.timeout)

    @property
    def endpoint(self):
        return '%s://%s:%s' % (self.scheme, self.host, self.port)

    def do_request(self, method, path, body=None, headers=None):
        if not headers:
            headers = self.headers
        LOG.debug("Request: %s %s body:%s, headers:%s",
                  method, path, body, headers)
        body = json.dumps(body) if (body and isinstance(body, dict)) else body
        self.connection.connect()
        self.connection.request(method, path, body, headers)
        resp = self.connection.getresponse()
        headers = {}
        for header, value in resp.getheaders():
            headers[header] = value
        content = resp.read()
        self.connection.close()
        resp = Response(resp.status, headers, content)
        LOG.debug("Response: %s", resp)
        if resp.status == 401:
            raise httperror.Unauthorized()
        elif resp.status == 404:
            raise httperror.Http404Error(
                url=self.endpoint + path, resp=resp)
        return resp

    def get(self, path, headers=None):
        """
        :param path: the path of request
        :param headers: the header of request, type is dict
        :return: json or str
        """
        return self.do_request('GET', path, None, headers or self.headers)

    def post(self, path, body, headers=None):
        """
        :param path: the path of request
        :param body: the body of request
        :param headers: the header of request, type is dict
        :return: json or str
        """
        return self.do_request('POST', path, body, headers or self.headers)

    def put(self, path, body, headers=None):
        """
        :param path: the path of request
        :param body: the body or request
        :param headers: the headers of request, type is dict
        :return:
        """
        return self.do_request('PUT', path, body, headers or self.headers)

    def delete(self, path, headers=None):
        """
        :param path: the path of request
        :param headers: the header of request, type is dict
        :return: json or str
        """
        return self.do_request('DELETE', path, None, headers or self.headers)

    @property
    def headers(self):
        return {"Content-Type": "application/json"}
