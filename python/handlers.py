import os.path
from logs import Logger

logger = Logger('./')

class Handler:
  def handleRequest(self, req, res):
    pass

class StaticHandler(Handler):
  def handleRequest(self, req, res):
    if os.path.isfile(f'.{req.url}'):
      f = open(f'.{req.url}', 'r')
      res.set_body(f.read())
      res.send()
    else:
      logger.logError(404)
      res.status_code = 404
      res.send()

class RouteHandler(Handler):
  route_handlers = {}

  def handleRequest(self, req, res):
    if req.url in RouteHandler.route_handlers:
      try:
        RouteHandler.route_handlers[req.url](req, res)
      except Exception as e:
        logger.logError(500, e)
        res.status_code = 500
        res.send()
    else:
      logger.logError(404)
      res.status_code = 404
      res.send()

  def addRoute(self, route, handler):
    if callable(handler):
      RouteHandler.route_handlers[route] = handler

def getHandler(handler):
  if handler == 'static':
    return StaticHandler() 
  elif handler == 'route':
    return RouteHandler()
    