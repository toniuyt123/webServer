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

  def __init__(self, socket, HTTP_version = 1.1, status_code = 200, headers = {}, body = {}):
    self.socket = socket
    self.status_code = status_code
    self.headers = headers
    self.HTTP_version = HTTP_version
    self.body = body

  def set_body(self, body):
    self.body = body

  def toString(self):
    return (f'HTTP/{self.HTTP_version} {self.status_code} {self.codes[self.status_code]}\r\n' +
      '\r\n'.join(f'{key}:{value}' for [key, value] in self.headers.items()) +
      '\r\n\r\n' + 
      self.body)

  def send(self):
    self.socket.send(self.toString().encode())
