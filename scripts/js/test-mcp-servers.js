#!/usr/bin/env node

/**
 * Comprehensive MCP Server Test Suite
 * Tests all installed MCP servers to ensure they're working correctly
 */

const { spawn } = require('child_process');
const fs = require('fs');

console.log('🧪 MCP Server Test Suite\n');
console.log('Testing all installed MCP servers...\n');

// Load configuration
const config = JSON.parse(fs.readFileSync('mcp-config.json', 'utf8'));

// Test results
const results = {
    passed: [],
    failed: [],
    total: 0
};

// Test a single MCP server
function testServer(name, serverConfig) {
    return new Promise((resolve) => {
        console.log(`Testing ${name}...`);
        
        const serverProcess = spawn(serverConfig.command, serverConfig.args, {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env, ...serverConfig.env }
        });

        let output = '';
        let error = '';
        let resolved = false;

        serverProcess.stdout.on('data', (data) => {
            output += data.toString();
        });

        serverProcess.stderr.on('data', (data) => {
            error += data.toString();
        });

        // Give server 3 seconds to start
        setTimeout(() => {
            if (!resolved) {
                resolved = true;
                serverProcess.kill('SIGTERM');
                
                // Check if server started successfully
                if (output.includes('running') || error.includes('running') || 
                    output.includes('Server') || error.includes('Server') ||
                    output.includes('MCP') || error.includes('MCP')) {
                    console.log(`  ✅ ${name}: Started successfully`);
                    results.passed.push(name);
                } else {
                    console.log(`  ❌ ${name}: Failed to start`);
                    console.log(`     Output: ${output.substring(0, 100)}...`);
                    console.log(`     Error: ${error.substring(0, 100)}...`);
                    results.failed.push(name);
                }
                resolve();
            }
        }, 3000);

        serverProcess.on('error', (err) => {
            if (!resolved) {
                resolved = true;
                console.log(`  ❌ ${name}: Error - ${err.message}`);
                results.failed.push(name);
                resolve();
            }
        });
    });
}

// Test all servers
async function runTests() {
    const servers = Object.entries(config.mcpServers);
    results.total = servers.length;

    for (const [name, serverConfig] of servers) {
        await testServer(name, serverConfig);
    }

    // Print summary
    console.log('\n📊 Test Results Summary:');
    console.log(`Total servers tested: ${results.total}`);
    console.log(`✅ Passed: ${results.passed.length}`);
    console.log(`❌ Failed: ${results.failed.length}`);
    
    if (results.passed.length > 0) {
        console.log('\n✅ Working servers:');
        results.passed.forEach(name => console.log(`  - ${name}`));
    }
    
    if (results.failed.length > 0) {
        console.log('\n❌ Failed servers:');
        results.failed.forEach(name => console.log(`  - ${name}`));
        console.log('\nNote: Some servers may require API keys or additional configuration.');
    }

    console.log('\n🎉 MCP server testing completed!');
}

runTests().catch(console.error);
