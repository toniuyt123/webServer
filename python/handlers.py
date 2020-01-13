import os.path
import struct
from logs import Logger
import importlib.util
from utils import AsyncResponse

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

class FastCGI(Handler):
  FCGI_HEADER_LEN = 8

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

  reqId = 1

  class Record():
    def __init__(self, type, req_id, role, flags, version = 1):
      self.version = 1
      self.type = type
      self.req_id = req_id
      self.role = role
      self.flags = flags
      self.params = {}
        
    def __repr__(self):
      return '{%d, %d, %d, %d}' % (self.type, self.req_id, self.role, self.flags)

    def decodeRecord(self, frmt, data):
      self.version, self.type, self.requestId, self.contentLength, \
        self.paddingLength = struct.unpack(frmt, data)

    def write(self, frmt, socket):
      self.paddingLength = -self.contentLength & 7
  
      header = struct.pack(frmt, self.version, self.type, self.requestId, \
        self.contentLength, self.paddingLength)
  
      socket.sendall(header)


  def handleRequest(self, req, res):
    pass

class WSGI(Handler):
  response = None

  def __init__(self, app):
    spec = importlib.util.spec_from_file_location("application", app)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    self.app = module.application

  def handleRequest(self, req, res):
    def start_response(status, response_headers, exc_info=None):
      self.response = AsyncResponse(req.writer, '1.1', status, dict(response_headers))

      return self.response.write

    environ = {}
    environ['REQUEST_METHOD'] = req.method
    environ['PATH_INFO'] = req.url
    environ['QUERY_STRING'] = req.query
    environ['CONTENT_TYPE'] = req.headers['content-type']
    environ['CONTENT_LENGTH'] = req.headers['content-length']
    (environ['SERVER_NAME'], environ['SERVER_PORT']) = (req.headers['host'].split(':')
      if ':' in req.headers['host']
      else (req.headers['host'], '') )
    environ['SERVER_PROTOCOL'] = 'HTTP/1.0'

    for (key, value) in req.headers.items():
      environ['HTTP_' + key.replace('-', '_').upper()] = value

    result = self.app(environ, start_response)

    for data in result:
      self.response.write(data)

    self.response.send()

    

def getHandler(handler, params = { 'app': 'wsgi.py' }):
  if handler == 'static':
    return StaticHandler() 
  elif handler == 'route':
    return RouteHandler()
  elif handler == 'wsgi':
    return WSGI(params['app'])
  elif handler == 'fcgi':
    return FastCGI()

    