// check-tailwind.cjs
const fs = require('fs');
const path = require('path');

console.log('🔍 Checking for Tailwind classes in your React files...\n');

// Tailwind classes to search for
const tailwindClasses = [
  'bg-blue-500',
  'text-white',
  'p-4',
  'rounded',
  'flex',
  'items-center',
  'justify-center',
  'min-h-screen',
  'bg-gradient-to-br',
];

// Function to search for classes in a file
const searchFile = (filePath) => {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const foundClasses = tailwindClasses.filter((cls) => content.includes(cls));

    if (foundClasses.length > 0) {
      console.log(`✅ ${path.relative('.', filePath)}`);
      console.log(`   Found: ${foundClasses.join(', ')}`);
      return true;
    }
    return false;
  } catch (error) {
    console.log(`❌ Error reading ${filePath}: ${error.message}`);
    return false;
  }
};

// Function to recursively search directories
const searchDirectory = (dir, pattern = /\.(jsx?|tsx?)$/) => {
  let foundCount = 0;

  try {
    const files = fs.readdirSync(dir, { withFileTypes: true });

    for (const file of files) {
      const fullPath = path.join(dir, file.name);

      if (
        file.isDirectory() &&
        !file.name.startsWith('.') &&
        file.name !== 'node_modules'
      ) {
        foundCount += searchDirectory(fullPath, pattern);
      } else if (file.isFile() && pattern.test(file.name)) {
        if (searchFile(fullPath)) {
          foundCount++;
        }
      }
    }
  } catch (error) {
    console.log(`❌ Error reading directory ${dir}: ${error.message}`);
  }

  return foundCount;
};

console.log('Starting search from current directory...\n');

// Search common directories
const directories = ['./src', './pages', './components', '.'];

let totalFound = 0;

for (const dir of directories) {
  if (fs.existsSync(dir)) {
    console.log(`\n📁 Searching in ${dir}/`);
    const count = searchDirectory(dir);
    totalFound += count;
  } else {
    console.log(`\n⚠️  Directory ${dir}/ does not exist`);
  }
}

console.log(`\n📊 Summary:`);
console.log(`- Total files with Tailwind classes: ${totalFound}`);
console.log(`- If this is 0, Tailwind won't generate any CSS`);

// Check the actual file structure
console.log(`\n📁 Actual file structure:`);
try {
  const srcFiles = fs.readdirSync('./src', { withFileTypes: true });
  console.log('./src/');
  srcFiles.forEach((file) => {
    console.log(`  ${file.isDirectory() ? '📁' : '📄'} ${file.name}`);
  });
} catch (error) {
  console.log('❌ Cannot read src directory');
}
