const app = require('./webServer');

app.get('/test', (req, res) => {
  console.log(req, res);
  res.ye = 'Hello';
});

app.listen(2222);