import os.path
import struct
from logs import Logger
import importlib.util
from utils import AsyncResponse
import asyncio
import fcgiVariables

logger = Logger('./')

class Handler:
  def handleRequest(self, req, res):
    pass

class StaticHandler(Handler):
  def handleRequest(self, req, res):
    if os.path.isfile(f'.{req.url}'):
      f = open(f'.{req.url}', 'r')


      res.set_body(f.read())

      if (req.url.split('.')[1] == 'html'):
        res.set_headers({ 'content-type': 'text/html' })
  
      f.close()
      res.send()
    else:
      logger.logError(404)
      res.status_code = 404
      res.send()

class RouteHandler(Handler):
  route_handlers = {}

  def handleRequest(self, req, res):
    url = req.url.split('?')[0]

    if url in RouteHandler.route_handlers:
      try:
        RouteHandler.route_handlers[url](req, res)
      except Exception as e:
        logger.logError(500, e)
        res.status_code = 500
        res.send()
    else:
      logger.logError(404)
      res.status_code = 404
      res.send()

  async def handleAsync(self, req, res):
    url = req.url.split('?')[0]

    if url in RouteHandler.route_handlers:
      try:
        await RouteHandler.route_handlers[url](req, res)
      except Exception as e:
        logger.logError(500, e)
        res.status_code = 500
        await res.send()
    else:
      logger.logError(404)
      res.status_code = 404
      await res.send()

  def addRoute(self, route, handler):
    if callable(handler):
      RouteHandler.route_handlers[route] = handler


class WSGI(Handler):
  response = None

  def __init__(self, app):
    spec = importlib.util.spec_from_file_location("application", app)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    self.app = module.application

  async def handleAsync(self, req, res):
    def start_response(status, response_headers, exc_info=None):
      self.response = AsyncResponse(res.writer, '1.1', status, dict(response_headers))

      return self.response.write

    environ = {}
    environ['REQUEST_METHOD'] = req.method
    environ['PATH_INFO'] = req.url
    environ['QUERY_STRING'] = req.query
    environ['CONTENT_TYPE'] = req.headers['content-type']
    environ['CONTENT_LENGTH'] = req.headers['content-length']
    (environ['SERVER_NAME'], environ['SERVER_PORT']) = (req.headers['host'].split(':')
      if ':' in req.headers['host']
      else (req.headers['host'], ''))
    environ['SERVER_PROTOCOL'] = 'HTTP/1.0'

    for (key, value) in req.headers.items():
      environ['HTTP_' + key.replace('-', '_').upper()] = value

    result = self.app(environ, start_response)
    for data in result:
      print(data)
      self.response.write(data.decode())

    await self.response.send()

FCGI_HEADER_LEN = 8
FCGI_KEEP_CONN = 1
FCGI_VERSION_1 = 1

FCGI_BEGIN_REQUEST     = 1
FCGI_ABORT_REQUEST     = 2
FCGI_END_REQUEST       = 3
FCGI_PARAMS            = 4
FCGI_STDIN             = 5
FCGI_STDOUT            = 6
FCGI_STDERR            = 7
FCGI_DATA              = 8
FCGI_GET_VALUES        = 9
FCGI_GET_VALUES_RESULT = 10
FCGI_UNKNOWN_TYPE      = 11

FCGI_RESPONDER  = 1
FCGI_AUTHORIZER = 2
FCGI_FILTER     = 3

FCGI_REQUEST_COMPLETE = 0
FCGI_CANT_MPX_CONN    = 1
FCGI_OVERLOADED       = 2
FCGI_UNKNOWN_ROLE     = 3

FCGI_Header = '!BBHHBx'
FCGI_BeginRequestBody = '!HB5x'
FCGI_EndRequestBody = '!LB3x'
FCGI_UnknownTypeBody = '!B7x'
FGCI_ParamLengths = '!II'

class FastCGI(Handler):
  req_id = 1

  def __init__(self, path):
    self.reader, self.writer = asyncio.open_unix_connection(path)

  class Record():
    def __init__(self, type, requestId, body = b'', version = 1):
      self.version = 1
      self.type = type
      self.requestId = requestId
      self.body = body
      self.contentLength = len(body)
      self.params = {}

    def decodeRecord(self, frmt, data):
      self.version, self.type, self.requestId, self.contentLength, \
        self.paddingLength = struct.unpack(frmt, data)

    def write(self, frmt, writer):
      self.paddingLength = -self.contentLength & 7

      header = struct.pack(frmt, self.version, self.type, self.requestId, \
        self.contentLength, self.paddingLength)

      writer.write(header)

  def get_req_id(self):
    self.req_id += 1
    return self.req_id

  async def handleAsync(self, req, res):
    reqId = self.get_req_id()
    begin = self.Record(FCGI_BEGIN_REQUEST, reqId, struct.pack(FCGI_RESPONDER, FCGI_KEEP_CONN))
    begin.write(FCGI_BeginRequestBody, res.writer)
    
    params = {}
    params['REQUEST_METHOD'] = req.method
    params['PATH_INFO'] = req.url
    params['QUERY_STRING'] = req.query
    params['CONTENT_TYPE'] = req.headers['content-type']
    params['CONTENT_LENGTH'] = req.headers['content-length']
    (params['SERVER_NAME'], params['SERVER_PORT']) = (req.headers['host'].split(':')
      if ':' in req.headers['host']
      else (req.headers['host'], '') )
    params['SERVER_PROTOCOL'] = 'HTTP/1.0'

    for (key, value) in req.headers.items():
      params['HTTP_' + key.replace('-', '_').upper()] = value
    
    param_body = b''
    for key, value in params.items():
      param_body += struct.pack(FGCI_ParamLengths, len(key), len(value))
      param_body += bytes(key, 'ascii')
      param_body += bytes(value, 'ascii')

    params_record = self.Record(FCGI_PARAMS, reqId, param_body)
    params_record.write(FCGI_Header, req.writer)
    self.Record(FCGI_PARAMS, reqId).write(FCGI_Header, req.writer)

    stdin_record = self.Record(FCGI_STDIN, reqId, req.body)
    stdin_record.write(FCGI_Header, req.writer)
    self.Record(FCGI_STDIN, reqId).write(FCGI_Header, req.writer)

    await req.writer.drain()

def getHandler(handler, params = { 'app': 'wsgiTest.py' }):
  if handler == 'static':
    return StaticHandler() 
  elif handler == 'route':
    return RouteHandler()
  elif handler == 'wsgi':
    return WSGI(params['app'])
  elif handler == 'fcgi':
    return FastCGI()

    