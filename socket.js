var net = require('net');
var server = net.createServer(function(connection) { 
   console.log ('client has connected successfully!');
   
   connection.on('end', function() {
      console.log ('client has disconnected successfully!');
   });
   connection.write('Hello Node.js!\r\n');
   connection.pipe(connection);
});
server.listen(8067, function() { 
   console.log('server is listening');
   console.log('server bound address is: ' + server.address ());
});