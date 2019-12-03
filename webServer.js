const fs = require('fs');
const net = require('net');
const path = require('path');

const server = net.createServer();

server.on('connection', (socket) => {

  socket.on('data', (data) => {
    console.log('Data sent to server : ' + data);
    const req = parseRequest(data);
    console.log(req);

    if (req.url) {
      const filepath = path.join(__dirname, `.${req.url}`);

      if (fs.existsSync(filepath)) {
        const file = fs.readFileSync(filepath);

        return socket.end(file);
      }
    }

    socket.end();
  });
});

server.listen(2222);

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
        } if (req['content-type'] === 'application/json') {
          req.body = { ...JSON.parse(content) };
        }
      }
    }
  }

  return req;
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
