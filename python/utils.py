class Request:
  def __init__(self, method, url, HTTP_version, headers, rawHTTP, body = None, query = None):
    self.method = method
    self.url = url
    self.headers = headers
    self.HTTP_version = HTTP_version
    self.rawHTTP = rawHTTP
    self.body = body or {}
    self.query = query or {}

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

  def set_headers(self, headers):
    for [key, value] in headers.items():
      self.headers[key] = value

  def set_body(self, body, content_type = 'text/plain'):
    if ('content-type' in self.headers):
      self.headers['content-type'] = content_type

    self.headers['content-length'] = len(body)
    self.body = body

  def toBytes(self):
    http_begin = (f'HTTP/{self.HTTP_version} {self.status_code} {self.codes[self.status_code]}\r\n' +
      '\r\n'.join(f'{key}: {value}' for [key, value] in self.headers.items()) +
      '\r\n\r\n')

    return (http_begin + self.body).encode()

  def send(self, data = None):
    if data != None:
      self.set_body(data)

    if 'content-length' not in self.headers:
      self.headers['content-length'] = 0

    self.socket.sendall(self.toBytes())
    self.socket.close()

def parseMultipart(boundary, content):
  files = {}

  parts = str(content).split(f'--{boundary}')[1:-1]

  for part in parts:
    current_file = part.split('\\r\\n')[1:-1]
    filename = ''

    for hpart in current_file[0].split(';'):
      if hpart.find('="') > 0:
        [key, value] = hpart.split('="')

        filename = value[:-1]
    files[filename] = current_file[-1]

  return files