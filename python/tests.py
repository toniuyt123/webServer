import socket
import json
import unittest
import requests
import os

try:
  with open('config.json') as config_file:
    config = json.load(config_file)
except FileNotFoundError:
  config = {}

host = config.get('host', 'localhost')
port = config.get('port', 5001)

class TestStringMethods(unittest.TestCase):

    def test_simple(self):
      res= requests.get(f'http://localhost:{port}/test')
      self.assertEqual(res.status_code, 200)
      self.assertEqual(res.text, 'yee')

    def test_404(self):
      res= requests.get(f'http://localhost:{port}/notfound')
      self.assertEqual(res.status_code, 404)

    def test_500(self):
      res= requests.get(f'http://localhost:{port}/error')
      self.assertEqual(res.status_code, 500)

    def test_ram(self):
      url = f'http://localhost:{port}/ramTest'

      chunk = str(os.urandom(10000)) + '\n'
      with open("BigFile.txt", "w") as f:
        for i in range(300):
          print(i)
          f.write(chunk)
        f.close()

      res = requests.post(url, files={'upload_file': open('BigFile.txt','rb')})
      self.assertEqual(res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
