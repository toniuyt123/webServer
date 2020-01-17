def application(environ, start_response):
  start_response(200, [('content-length', 12)])

  return [b'Hello World!']
