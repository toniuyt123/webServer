import datetime
import os.path
import aiofiles

class Logger:
  def __init__(self, path):
    self.path = path
    self.filename = str(datetime.date.today())

    if (not os.path.isdir(os.path.join(path, 'logs'))):
      os.mkdir(os.path.join(path, 'logs'))

    if (not os.path.isdir(os.path.join(path, 'logs/access'))):
      os.mkdir(os.path.join(path, 'logs/access'))

    if (not os.path.isdir(os.path.join(path, 'logs/error'))):
      os.mkdir(os.path.join(path, 'logs/error'))

    self.access_log = open(os.path.join(path, 'logs/access', self.filename), 'a')
    self.error_log = open(os.path.join(path, 'logs/error', self.filename), 'a')

  def logAccess(self, req):
    if (self.filename != str(datetime.date.today())):
      self.filename = str(datetime.date.today())
      self.access_log = open(os.path.join(self.path, 'logs/acess', self.filename), 'a')
    
    logtext = f'{datetime.datetime.now()} - {req.rawHTTP}\n'
    self.access_log.write(logtext)

  async def logAccessAsync(self, req):
    async with aiofiles.open(os.path.join(self.path, 'logs/acess', self.filename), mode='a') as f:
      logtext = f'{datetime.datetime.now()} - {req.rawHTTP}\n'
      await f.write(logtext)

  def logError(self, code, err = ''):
    if (self.filename != str(datetime.date.today())):
      self.filename = str(datetime.date.today())
      self.error_log = open(os.path.join(self.path, 'logs/acess', self.filename), 'a')
    
    logtext = f'{datetime.datetime.now()} - ERROR {code} {err}\n'
    self.error_log.write(logtext)
