import time
import socket
import json
import os
import signal
from logs import Logger
from utils import Request, Response, parseMultipart, parseUrlEncoded
from handlers import getHandler

def parseHTTP(clientcoket):
  data = b''
  req_end = 0
  headers = {}
  body = {}
  lines = []

  while True:
    chunk = clientcoket.recv(1024)

    if not chunk:
      break

    data += chunk

    if not req_end:
      # print(str(data))
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
        elif ('multipart/form-data;' in value):
          boundary = value.split('=', 1)[1]
          headers['files'] = parseMultipart(boundary, content)
      break

  # print(lines)
  url = lines[0].split(' ')[1]
  query = {}

  if '?' in url:
    query = parseUrlEncoded(url.split('?')[1])

  return Request(*lines[0].split(' '), headers, data, body, query)

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
# sock.setblocking(True)

print('listening on', (host, port))

def test(req, res):
  time.sleep(5)
  res.set_body('yee')
  res.send()

def errTest(req, res):
  raise Exception('This is test error')

def saveFile(req, res):
  if (req.headers['files'] != None):
    for [filename, body] in req.headers['files'].items():
      f = open(f'./files/{filename}', 'w')
      f.write(body)
      f.close()

  res.send()

def sendFile(req, res):
  if 'filename' in req.body:
    filename = req.body['filename']
  elif 'filename' in req.query:
    filename = req.query['filename']

  path = f'./files/{filename}'

  if (filename != None):
    f = open(path, 'r')
    res.set_headers({
      'content-disposition': f'attachment; filename={filename}',
      'content-length': os.stat(path).st_size
    })
    res.send()
    
    while True:
      data = f.read(65536)
      if not data:
        break
      res.sendChunk(data)
    
    f.close()

  else:
    res.status_code = 404
    res.send()
  

def ramTest(req, res):
  res.status_code = 200
  res.send()

def add(req, res):
  sum_result = (int)(req.body['a'] or 0) + (int)(req.body['b'] or 0)

  print(sum_result)

  res.send(str(sum_result))

handler.addRoute('/test', test)
handler.addRoute('/error', errTest)
handler.addRoute('/saveFile', saveFile)
handler.addRoute('/sendFile', sendFile)
handler.addRoute('/ramTest', saveFile)
handler.addRoute('/sum', add)

def reapChildren(signum, frame):
  while 1:
    try:
      pid, stat = os.waitpid(-1, os.WNOHANG)
      if not pid: break
    except:
      break 

def waitChild(signum, frame):
  pid, stat = os.waitpid(-1, os.WNOHANG)

signal.signal(signal.SIGCHLD, waitChild)

while True:
  (clientsocket, address) = sock.accept()
  child_pid = os.fork()

  if child_pid == 0:
    req = parseHTTP(clientsocket)
    res = Response(clientsocket)

    handler.handleRequest(req, res)
    clientsocket.close()

    logger.logAccess(req)
    os._exit(0)
  else:
    clientsocket.close()
