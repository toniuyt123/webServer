import socket, asyncio
import time
import json
import os
from logs import Logger
from utils import Request, AsyncResponse, parseMultipart, parseUrlEncoded
from handlers import getHandler


try:
  with open('config.json') as config_file:
    config = json.load(config_file)
except FileNotFoundError:
  config = {}

host = config.get('host', 'localhost')
port = config.get('port', 5000)
handler = getHandler(config.get('handler', 'route'))

async def test(req, res):
  res.set_body('yee')
  await res.send()

handler.addRoute('/test', test)

async def handleClient(reader, writer):
  data = b''
  req_end = 0
  headers = {}
  body = {}
  lines = []

  while True:
    chunk = await reader.read(1024)

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

  req = Request(*lines[0].split(' '), headers, data, body, query)
  res = AsyncResponse(writer)

  await handler.handleAsync(req, res)

loop = asyncio.get_event_loop()
coro = asyncio.start_server(handleClient, host, port, loop=loop)
server = loop.run_until_complete(coro)

print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
