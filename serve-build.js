const http = require('http');
const fs = require('fs');
const path = require('path');

const port = 3001;
const buildDir = path.join(__dirname, 'build');

const server = http.createServer((req, res) => {
    let filePath;
    
    // Serve React build for the root path, demo.html for /demo
    if (req.url === '/demo') {
        filePath = path.join(__dirname, 'demo.html');
    } else if (req.url === '/') {
        filePath = path.join(buildDir, 'index.html');
    } else {
        filePath = path.join(buildDir, req.url);
    }
    
    // Handle static files
    if (fs.existsSync(filePath)) {
        const ext = path.extname(filePath);
        const contentType = {
            '.html': 'text/html',
            '.js': 'text/javascript',
            '.css': 'text/css',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.ico': 'image/x-icon'
        }[ext] || 'text/plain';
        
        res.writeHead(200, { 'Content-Type': contentType });
        fs.createReadStream(filePath).pipe(res);
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
    }
});

server.listen(port, () => {
    console.log(`Server running at http://localhost:${port}/`);
});

// Keep server running
process.on('SIGTERM', () => {
    server.close(() => {
        console.log('Server stopped');
    });
});