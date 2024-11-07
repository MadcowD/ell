const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function compileTSC() {
  console.log('Compiling TypeScript...');
  try {
    execSync('tsc -p tsconfig.build.json --noCheck', { stdio: 'inherit' });
    console.log('TypeScript compilation completed successfully.');
  } catch (error) {
    console.error('TypeScript compilation failed:', error);
    process.exit(1);
  }
}

function moveFilesUpOneLevel() {
  console.log('Moving files up one level...');
  const distPath = path.join(__dirname, '..', 'dist');
  const srcPath = path.join(distPath, 'src');

  if (!fs.existsSync(srcPath)) {
    console.error('The src directory does not exist in dist.');
    return;
  }

  fs.readdirSync(srcPath).forEach(file => {
    const srcFile = path.join(srcPath, file);
    const destFile = path.join(distPath, file);

    fs.renameSync(srcFile, destFile);
    console.log(`Moved ${file} up one level.`);
  });

  // Remove the now-empty src directory
  fs.rmdirSync(srcPath);
  console.log('Removed empty src directory.');
}

function build() {
  compileTSC();
  moveFilesUpOneLevel();
  console.log('Build process completed.');
}

build();