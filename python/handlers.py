import os.path

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
      res.status_code = 404
      res.send()

class RouteHandler(Handler):
  route_handlers = {}

  def handleRequest(self, req, res):
    if req.url in RouteHandler.route_handlers:
      RouteHandler.route_handlers[req.url](req, res)

  def addRoute(self, route, handler):
    if callable(handler):
      RouteHandler.route_handlers[route] = handler

def getHandler(handler):
  if handler == 'static':
    return StaticHandler() 
  elif handler == 'route':
    return RouteHandler()
    