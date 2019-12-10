import socket
import selectors
import types
import json
import os.path
from utils import Request, Response

def parseUrlEncoded(query):
  if (query):
    params = query.split('&')
    result = {}

    for param in params:
      [key, value] = param.split('=')

      result[key] = value

    return result

  return {}

def handleHTTP(clientcoket):
  data = b''
  
  while True:
    chunk = clientcoket.recv(1024); 

    if not chunk:
      break

    data += chunk

  lines = data.decode('utf-8').split('\r\n')
  headers = {}
  body = {}

  for i in range(1, len(lines)):
    line = lines[i]

    try:
      if (len(line) > 0):
        [key, value] = line.split(': ', 1)
        headers[key.lower()] = value

        if (key.lower() == 'content-type'):
          content = ''
          length = int(headers['content-length'])

          while (len(content) < length):
            i += 1
            content += lines[i]

          if (value == 'text/plain'):
            body = content
          elif (value == 'application/json'):
            body = json.loads(content)
          elif (value == 'application/x-www-form-urlencoded'):
            body = parseUrlEncoded(content)

    except ValueError:
      print('To do')

  return Request(*lines[0].split(' '), headers, body)

try:
  with open('config.json') as config_file:
    config = json.load(config_file)
except FileNotFoundError:
  config = {}

host = config.get('host', 'localhost')
port = config.get('port', 5001)
route_handlers = {}

sel = selectors.DefaultSelector()
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
sock.listen()
sock.setblocking(True)

print('listening on', (host, port))

while True:
  (clientsocket, address) = sock.accept()

  req = handleHTTP(clientsocket)
  res = Response(clientsocket)

  if (req.url in route_handlers):
    route_handlers[req.url](req, res)
  elif (os.path.isfile(f'.{req.url}')):
    f = open(f'.{req.url}', 'r')
    res.set_body(f.read())
  
  res.send()


