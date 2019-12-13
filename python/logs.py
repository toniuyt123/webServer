import datetime
import os.path

class Logger:
  def __init__(self, path):
    self.path = path
    self.filename = str(datetime.date.today())

    if (not os.path.isdir(os.path.join(path, 'logs'))):
      os.mkdir(os.path.join(path, 'logs'))

    self.logfile = open(os.path.join(path, 'logs', self.filename), 'a')

  def log(self, req):
    if (self.filename != str(datetime.date.today())):
      self.filename = str(datetime.date.today())
      self.logfile = open(os.path.join(self.path, 'logs', self.filename), 'a')
    
    logtext = f'{datetime.datetime.now()} - {req.rawHTTP}\n'
    self.logfile.write(logtext)