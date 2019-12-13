class Request:
  def __init__(self, method, url, HTTP_version, headers, body={}):
    self.method = method
    self.url = url
    self.headers = headers
    self.HTTP_version = HTTP_version
    self.body = body

class Response:
  codes = {
    200: 'OK',
    404: 'Not Found',
    405: 'Method Not Allowed',
    500: 'Internal Server Error'
  } 

  def __init__(self, socket, HTTP_version = 1.1, status_code = 200, headers = None, body = ''):
    self.socket = socket
    self.status_code = status_code
    self.headers = headers or {}
    self.HTTP_version = HTTP_version
    self.body = body

  def set_body(self, body, content_type = 'text/plain'):
    self.headers['content-type'] = content_type
    self.headers['content-length'] = len(body)
    self.body = body

  def toBytes(self):
    http_begin = (f'HTTP/{self.HTTP_version} {self.status_code} {self.codes[self.status_code]}\r\n' +
      '\r\n'.join(f'{key}:{value}' for [key, value] in self.headers.items()) +
      '\r\n\r\n')

    return (http_begin + self.body).encode()

  def send(self, data = None):
    if data:
      self.set_body(data)

    self.socket.sendall(self.toBytes())
    self.socket.close()
