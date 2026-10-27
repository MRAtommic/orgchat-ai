const fs = require('fs');
if (!fs.existsSync('public')) fs.mkdirSync('public');

const svg = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='#16a34a'/><text x='16' y='24' font-size='20' text-anchor='middle'>🌾</text></svg>";
fs.writeFileSync('public/favicon.svg', svg);

const header = Buffer.from([0, 0, 1, 0, 1, 0]);
const bmpHeaderSize = 40;
const pixelDataSize = 16 * 16 * 4;
const maskSize = 16 * 4;
const imgSize = bmpHeaderSize + pixelDataSize + maskSize;
const dir = Buffer.alloc(16);
dir[0] = 16;
dir[1] = 16;
dir[2] = 0;
dir[3] = 0;
dir.writeUInt16LE(1, 4);
dir.writeUInt16LE(32, 6);
dir.writeUInt32LE(imgSize, 8);
dir.writeUInt32LE(22, 12);

const bmpHeader = Buffer.alloc(40);
bmpHeader.writeUInt32LE(40, 0);
bmpHeader.writeInt32LE(16, 4);
bmpHeader.writeInt32LE(32, 8);
bmpHeader.writeUInt16LE(1, 12);
bmpHeader.writeUInt16LE(32, 14);
bmpHeader.writeUInt32LE(0, 16);
bmpHeader.writeUInt32LE(pixelDataSize + maskSize, 20);

const pixelData = Buffer.alloc(pixelDataSize, 0);
for (let y = 0; y < 16; y++) {
  for (let x = 0; x < 16; x++) {
    const idx = (y * 16 + x) * 4;
    if (x >= 2 && x <= 13 && y >= 2 && y <= 13) {
      pixelData[idx] = 0x4a;
      pixelData[idx + 1] = 0xa3;
      pixelData[idx + 2] = 0x16;
      pixelData[idx + 3] = 0xff;
    }
  }
}
const maskData = Buffer.alloc(maskSize, 0);

const icoBuffer = Buffer.concat([header, dir, bmpHeader, pixelData, maskData]);
fs.writeFileSync('public/favicon.ico', icoBuffer);
console.log('Successfully created public/favicon.ico and public/favicon.svg');
