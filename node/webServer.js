const fs = require('fs');
const net = require('net');
const path = require('path');

const server = net.createServer();

const codes = {
  200: 'OK',
  404: 'Not Found',
  405: 'Method Not Allowed',
  500: 'Internal Server Error',
};

const routes = {};

server.on('connection', (socket) => {

  socket.on('data', (data) => {
    const { req, res } = parseRequest(data);

    if (req.url) {
      const filepath = path.join(__dirname, `.${req.url}`);
      const handler = routes[req.url]; 
  
      if (fs.existsSync(filepath)) {
        if (fs.lstatSync(filepath).isFile()) {
          const file = fs.readFileSync(filepath);

          return socket.end(file)
        }
      } else if (handler) {
        if (handler.methods.includes(req.method)) {
          handler.cb(req, res);
          
          return socket.end(JSON.stringify(res));
        }
  
        constructStatus(res, 405); 
      } else  {
        constructStatus(res, 404); 
      }
    }

    console.log(res);
    return socket.end(JSON.stringify(res));
  });
});

const listen = (port) => {
  server.listen(port);
}

const get = (route, cb) => {
  routeWrapper(route, cb, ['GET']);
};

const post = (route, cb) => {
  routeWrapper(route, cb, ['POST']);
};

const all = (route, cb) => {
  routeWrapper(route, cb, ['GET, POST']);
};

const routeWrapper = (route, cb, methods) => {
  routes[route] = {
    type: 'handler',
    methods,
    cb,
  };
};

const parseRequest = (rawHTTP) => {
  rawHTTP = rawHTTP.toString();

  const lines = rawHTTP.split('\n');
  const firstLineTokens = lines[0].split(' ');

  const req = {
    method: firstLineTokens[0],
    url: firstLineTokens[1],
    query: parseUrlEncoded(firstLineTokens[1].split('?')[1]),
    body: {},
  };

  const res = {};

  // first line already parsed
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    const key = line.split(':')[0].trim();

    if (key !== '') {
      const data = line.substring(key.length + 1).trim();

      req[key.toLowerCase()] = data;

      if (key.toLowerCase() === 'content-length') {
        const length = parseInt(data);
        let bytesRead = 0;
        let content = '';

        while (bytesRead < length) {
          for (let j = i + 1; j < lines.length; j++) {
            content += lines[j];
            bytesRead += lines[j].length;
            i++;
          }
        }

        content = content.trim();

        if (req['content-type'] === 'application/x-www-form-urlencoded') {
          req.query = { ...req.query, ...parseUrlEncoded(content) };
        } else if (req['content-type'] === 'application/json') {
          req.body = { ...JSON.parse(content) };
        } else if (req['content-type'] === 'text/plain') {
          req.body = { content };
        } else if (req['content-type'] === 'multipart/form-data') {

        }
      }
    }
  }

  return { req, res };
};

const parseUrlEncoded = (query) => {
  if (query) {
    const params = query.split('&');
    const result = {};

    for (const param of params) {
      const [key, value] = param.split('=');

      result[key] = value;
    }

    return result;
  }

  return {};
}

const constructStatus = (res, code) => {
  res.statusCode = code;
  res.statusMessage = codes[code];
}

module.exports = {
  get,
  post,
  all,
  listen,
};
