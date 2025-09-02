const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/**
 * Generate latest.yml dynamically during build process
 * This script reads package.json for version and generates update metadata
 */

function generateLatestYml() {
    console.log('[BUILD] Generating latest.yml...');
    
    // Read package.json for current version
    const packagePath = path.join(__dirname, 'package.json');
    const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    const currentVersion = packageData.version;
    
    console.log(`[BUILD] Current version: ${currentVersion}`);
    console.log(`[BUILD] Generating latest.yml for CURRENT version (bundled with app): ${currentVersion}`);
    
    // Generate the current version metadata (this gets bundled with the app)
    const updateMetadata = {
        version: currentVersion,
        files: [
            {
                url: `https://your-b2-bucket.s3.amazonaws.com/Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-${currentVersion}.exe`,
                // Note: In production, you'd calculate actual SHA512 and size from the built file
                sha512: "current-version-sha512-hash-placeholder",
                size: 140000000 // Approximate size
            }
        ],
        path: `Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-${currentVersion}.exe`,
        sha512: "current-version-sha512-hash-placeholder",
        releaseDate: new Date().toISOString()
    };
    
    // Convert to YAML format manually (to avoid adding yaml dependency)
    const yamlContent = `version: ${updateMetadata.version}
files:
  - url: ${updateMetadata.files[0].url}
    sha512: ${updateMetadata.files[0].sha512}
    size: ${updateMetadata.files[0].size}
path: ${updateMetadata.path}
sha512: ${updateMetadata.sha512}
releaseDate: '${updateMetadata.releaseDate}'
`;

    // Write the generated latest.yml
    const outputPath = path.join(__dirname, 'latest.yml');
    fs.writeFileSync(outputPath, yamlContent, 'utf8');
    
    console.log(`[BUILD] Generated latest.yml for current version at: ${outputPath}`);
    console.log(`[BUILD] Content:\n${yamlContent}`);
    
    return outputPath;
}

// Enhanced version that can calculate actual file hashes and sizes
function generateLatestYmlFromBuild(distDir) {
    console.log('[BUILD] Generating latest.yml from built files...');
    
    const packagePath = path.join(__dirname, 'package.json');
    const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    const currentVersion = packageData.version;
    
    // Look for the built Windows installer
    const expectedFilename = `Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-${currentVersion}.exe`;
    const builtFilePath = path.join(distDir, expectedFilename);
    
    let fileMetadata = {
        size: 140000000,
        sha512: "placeholder-sha512-hash"
    };
    
    // If the built file exists, calculate actual metadata
    if (fs.existsSync(builtFilePath)) {
        console.log(`[BUILD] Found built file: ${builtFilePath}`);
        
        const fileBuffer = fs.readFileSync(builtFilePath);
        const hash = crypto.createHash('sha512');
        hash.update(fileBuffer);
        
        fileMetadata = {
            size: fileBuffer.length,
            sha512: hash.digest('base64')
        };
        
        console.log(`[BUILD] Calculated SHA512: ${fileMetadata.sha512}`);
        console.log(`[BUILD] File size: ${fileMetadata.size} bytes`);
    } else {
        console.log(`[BUILD] Built file not found, using placeholder metadata`);
    }
    
    // For testing: advertise next version
    const versionParts = currentVersion.split('.');
    const nextPatchVersion = parseInt(versionParts[2]) + 1;
    const nextVersion = `${versionParts[0]}.${versionParts[1]}.${nextPatchVersion}`;
    
    const yamlContent = `version: ${nextVersion}
files:
  - url: https://your-b2-bucket.s3.amazonaws.com/Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-${nextVersion}.exe
    sha512: ${fileMetadata.sha512}
    size: ${fileMetadata.size}
path: Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-${nextVersion}.exe
sha512: ${fileMetadata.sha512}
releaseDate: '${new Date().toISOString()}'
`;

    const outputPath = path.join(__dirname, 'latest.yml');
    fs.writeFileSync(outputPath, yamlContent, 'utf8');
    
    console.log(`[BUILD] Generated latest.yml advertising version ${nextVersion}`);
    return outputPath;
}

// Enhanced function to copy package.json for bundling
function copyPackageJsonForBundling() {
    console.log('[BUILD] Copying package.json for bundling...');
    
    const packagePath = path.join(__dirname, 'package.json');
    const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    
    // Create a minimal package.json for bundling with the app
    const bundlePackageData = {
        name: packageData.name,
        version: packageData.version,
        description: packageData.description,
        author: packageData.author
    };
    
    // Write the minimal package.json that will be bundled
    const bundlePackagePath = path.join(__dirname, 'app-package.json');
    fs.writeFileSync(bundlePackagePath, JSON.stringify(bundlePackageData, null, 2), 'utf8');
    
    console.log(`[BUILD] Created app-package.json for bundling with version: ${packageData.version}`);
    console.log(`[BUILD] Location: ${bundlePackagePath}`);
    
    return bundlePackagePath;
}

// Generate latest.yml with current version for bundling
function generateBundledLatestYml() {
    console.log('[BUILD] Generating bundled latest.yml (current version)...');
    
    const packagePath = path.join(__dirname, 'package.json');
    const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    const currentVersion = packageData.version;
    
    console.log(`[BUILD] Bundling latest.yml with current version: ${currentVersion}`);
    
    // Generate YAML for current version (what the app is)
    const yamlContent = `version: ${currentVersion}
files:
  - url: https://your-update-server.com/Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-${currentVersion}.exe
    sha512: current-version-sha512-placeholder
    size: 140000000
path: Accurate-Machine-Repair-Maintenance-Tracker-Win10-Setup-${currentVersion}.exe
sha512: current-version-sha512-placeholder
releaseDate: '${new Date().toISOString()}'
`;

    const outputPath = path.join(__dirname, 'latest.yml');
    fs.writeFileSync(outputPath, yamlContent, 'utf8');
    
    console.log(`[BUILD] Generated latest.yml for bundling at: ${outputPath}`);
    console.log(`[BUILD] Content:\n${yamlContent}`);
    
    return outputPath;
}

// Create versions.json to control what the server advertises as latest
function createVersionsConfig(targetVersion) {
    console.log(`[BUILD] Creating versions.json with latest version: ${targetVersion}`);
    
    const versionsData = {
        latest: targetVersion,
        available: [targetVersion],
        notes: "This file controls what version the update server advertises as the latest available. Update this when you deploy new versions.",
        lastUpdated: new Date().toISOString()
    };
    
    const versionsPath = path.join(__dirname, 'versions.json');
    fs.writeFileSync(versionsPath, JSON.stringify(versionsData, null, 2), 'utf8');
    
    console.log(`[BUILD] Created versions.json at: ${versionsPath}`);
    console.log(`[BUILD] Content: ${JSON.stringify(versionsData, null, 2)}`);
    
    return versionsPath;
}

// Update versions.json to advertise a new version
function updateAvailableVersion() {
    console.log('[BUILD] Updating available version for deployment...');
    
    const packagePath = path.join(__dirname, 'package.json');
    const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    const currentVersion = packageData.version;
    
    // For deployment, we want to advertise the version we just built
    console.log(`[BUILD] Setting ${currentVersion} as the latest available version`);
    
    createVersionsConfig(currentVersion);
    
    // Also generate latest.yml for the current version
    generateBundledLatestYml();
    
    return currentVersion;
}

// Run the appropriate function based on command line arguments
const args = process.argv.slice(2);

if (args.includes('--copy-package')) {
    copyPackageJsonForBundling();
} else if (args.includes('--bundled')) {
    generateBundledLatestYml();
} else if (args.includes('--update-available')) {
    updateAvailableVersion();
} else if (args.includes('--set-latest') && args.includes('--version')) {
    const versionIndex = args.indexOf('--version');
    const targetVersion = args[versionIndex + 1];
    createVersionsConfig(targetVersion);
} else if (args.includes('--from-build') && args.includes('--dist')) {
    const distIndex = args.indexOf('--dist');
    const distDir = args[distIndex + 1];
    generateLatestYmlFromBuild(distDir);
} else {
    generateLatestYml();
}
