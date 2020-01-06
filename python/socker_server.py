import time
import socket
import json
import os
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
      print(lines)

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

  if (filename != None):
    f = open(f'./files/{filename}', 'r')
    res.set_headers({
      'content-disposition': f'attachment; filename={filename}'
    })

    res.send(f.read())
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

activeChildren = []

def reapChildren():
  while activeChildren:
    pid, stat = os.waitpid(0, os.WNOHANG)
    if not pid: break
    activeChildren.remove(pid)
    # print(activeChildren)

while True:
  (clientsocket, address) = sock.accept()
  # reapChildren()
  child_pid = os.fork()

  if child_pid == 0:
    req = parseHTTP(clientsocket)
    res = Response(clientsocket)
    logger.logAccess(req)

    handler.handleRequest(req, res)
    clientsocket.close()
    os._exit(0)
  else:
    pass
    #activeChildren.append(child_pid)
