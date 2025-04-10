const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');
const IconGenerator = require('icon-gen');

// Create directory for icons if it doesn't exist
const iconsDir = path.join(__dirname, 'electron_app', 'icons');
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

// Create a canvas for our icon
const size = 256;
const canvas = createCanvas(size, size);
const ctx = canvas.getContext('2d');

// Draw a blue square with rounded corners
ctx.fillStyle = '#4169E1'; // Royal Blue
ctx.beginPath();
const radius = 30;
ctx.moveTo(radius, 0);
ctx.lineTo(size - radius, 0);
ctx.quadraticCurveTo(size, 0, size, radius);
ctx.lineTo(size, size - radius);
ctx.quadraticCurveTo(size, size, size - radius, size);
ctx.lineTo(radius, size);
ctx.quadraticCurveTo(0, size, 0, size - radius);
ctx.lineTo(0, radius);
ctx.quadraticCurveTo(0, 0, radius, 0);
ctx.closePath();
ctx.fill();

// Add text "AM"
ctx.font = 'bold 120px Arial';
ctx.fillStyle = 'white';
ctx.textAlign = 'center';
ctx.textBaseline = 'middle';
ctx.fillText('AM', size/2, size/2);

// Save as PNG
const pngPath = path.join(iconsDir, 'app.png');
const pngStream = fs.createWriteStream(pngPath);
const pngStream2 = canvas.createPNGStream();
pngStream2.pipe(pngStream);

pngStream.on('finish', () => {
  console.log('PNG icon created');
  
  // Generate ICO from PNG
  IconGenerator({
    source: pngPath,
    targets: [
      { dest: iconsDir, 
        icons: { ico: { sizes: [256] } } 
      }
    ]
  }).then(() => {
    console.log('ICO file created successfully');
  }).catch((err) => {
    console.error('Error generating ICO:', err);
  });
});
