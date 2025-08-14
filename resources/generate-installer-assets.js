const fs = require('fs');
const path = require('path');

// Create a simple BMP sidebar image (164x314 pixels for NSIS)
// This creates a placeholder - you can replace with your own image
function createSidebarBMP() {
    const width = 164;
    const height = 314;
    const bitsPerPixel = 24;
    const bytesPerPixel = bitsPerPixel / 8;
    const rowSize = Math.ceil((width * bitsPerPixel) / 32) * 4;
    const pixelDataSize = rowSize * height;
    
    // BMP Header
    const fileSize = 54 + pixelDataSize;
    const header = Buffer.alloc(54);
    
    // File header
    header.write('BM', 0);                    // Signature
    header.writeUInt32LE(fileSize, 2);        // File size
    header.writeUInt32LE(0, 6);               // Reserved
    header.writeUInt32LE(54, 10);             // Pixel data offset
    
    // DIB header
    header.writeUInt32LE(40, 14);             // Header size
    header.writeInt32LE(width, 18);           // Width
    header.writeInt32LE(height, 22);          // Height
    header.writeUInt16LE(1, 26);              // Planes
    header.writeUInt16LE(bitsPerPixel, 28);   // Bits per pixel
    header.writeUInt32LE(0, 30);              // Compression (none)
    header.writeUInt32LE(pixelDataSize, 34);  // Image size
    header.writeInt32LE(2835, 38);            // X pixels per meter
    header.writeInt32LE(2835, 42);            // Y pixels per meter
    header.writeUInt32LE(0, 46);              // Colors used
    header.writeUInt32LE(0, 50);              // Important colors
    
    // Create pixel data (gradient background)
    const pixels = Buffer.alloc(pixelDataSize);
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const offset = y * rowSize + x * bytesPerPixel;
            // Create a blue gradient
            const blue = Math.floor((y / height) * 100) + 155;
            const green = Math.floor((y / height) * 50) + 50;
            const red = Math.floor((y / height) * 30) + 30;
            
            pixels[offset] = blue;      // Blue
            pixels[offset + 1] = green;  // Green
            pixels[offset + 2] = red;    // Red
        }
    }
    
    return Buffer.concat([header, pixels]);
}

// Generate installer sidebar if it doesn't exist
const sidebarPath = path.join(__dirname, 'installerSidebar.bmp');
if (!fs.existsSync(sidebarPath)) {
    console.log('Generating installer sidebar image...');
    const bmpData = createSidebarBMP();
    fs.writeFileSync(sidebarPath, bmpData);
    console.log('Installer sidebar created at:', sidebarPath);
} else {
    console.log('Installer sidebar already exists');
}