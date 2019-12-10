import socket, asyncio
import json
  
class Request:
  def __init__(self, method, url, HTTP_version, headers):
    self.method = method
    self.url = url
    self.headers = headers
    self.HTTP_version = HTTP_version

async def handler(reader, writer):
  data = b''

  while True:
    chunk = await reader.read()  # Max number of bytes to read

    if not chunk:
      break
    
    data += chunk

  print(data)

  lines = data.decode('utf-8').split('\r\n')
  headers = {}

  for line in lines[1:]:
    try:
      [key, value] = line.split(':', 1)
      headers[key] = value
    except ValueError:

  req = Request(*lines[0].split(' '), headers)
  
  writer.close()
  await writer.wait_closed()

async def main():
  try:
    with open('config.json') as config_file:
      config = json.load(config_file)
  except FileNotFoundError:
    config = {}

  host = config.get('host', 'localhost')
  port = config.get('port', 5000)

  server = await asyncio.start_server(handler, host, port)
  await server.serve_forever()

asyncio.run(main())
