import socket
import json
from logs import Logger
from utils import Request, Response
from handlers import getHandler

def parseUrlEncoded(query):
  try:
    params = query.split('&')
    result = {}

    for param in params:
      [key, value] = param.split('=')

      result[key] = value

    return result
  except ValueError:
    pass

  return {}

def parseHTTP(clientcoket):
  data = b''
  req_end = 0
  headers = {}
  body = {}
  
  while True:
    chunk = clientcoket.recv(1024)

    if not chunk:
      break

    data += chunk

    if not req_end:
      body_begin = data.decode('utf-8').find('\r\n\r\n')

    if body_begin and not req_end:
      lines = data[:body_begin].decode('utf-8').split('\r\n')

      for i in range(1, len(lines)):
        line = lines[i]

        if (len(line) > 0):
          [key, value] = line.split(': ', 1)
          headers[key.lower()] = value

      if 'content-length' in headers:
        req_end = int(headers['content-length']) + body_begin + 4
      else:
        req_end = body_begin + 4

    if len(data) == req_end and body_begin:
      if 'content-type' in headers:
        content = data[body_begin + 4:]
        value = headers['content-type']

        if (value == 'text/plain'):
          body = content
        elif (value == 'application/json'):
          body = json.loads(content)
        elif (value == 'application/x-www-form-urlencoded'):
          body = parseUrlEncoded(content.decode())

      break

  return Request(*lines[0].split(' '), headers, data, body)

try:
  with open('config.json') as config_file:
    config = json.load(config_file)
except FileNotFoundError:
  config = {}

host = config.get('host', 'localhost')
port = config.get('port', 5000)
handler = getHandler(config.get('handler', 'route'))
logger = Logger('./')

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
sock.listen()
sock.setblocking(True)

print('listening on', (host, port))

def test(req, res):
  res.set_body('yee')
  res.send()

handler.addRoute('/test', test)

while True:
  (clientsocket, address) = sock.accept()

  req = parseHTTP(clientsocket)
  res = Response(clientsocket)
  logger.log(req)
  handler.handleRequest(req, res)
