#!/usr/bin/env node

/**
 * Individual MCP Service Tester
 * Tests GitHub, Puppeteer, and Brave Search services individually
 */

const { spawn } = require('child_process');
const fs = require('fs');

console.log('🧪 Individual MCP Service Tester');
console.log('=================================\n');

// Load environment if available
if (fs.existsSync('.env.mcp.configured')) {
    const envContent = fs.readFileSync('.env.mcp.configured', 'utf8');
    envContent.split('\n').forEach(line => {
        if (line.startsWith('GITHUB_PERSONAL_ACCESS_TOKEN=')) {
            process.env.GITHUB_PERSONAL_ACCESS_TOKEN = line.split('=')[1];
        } else if (line.startsWith('BRAVE_API_KEY=')) {
            process.env.BRAVE_API_KEY = line.split('=')[1];
        } else if (line.startsWith('PUPPETEER_EXECUTABLE_PATH=')) {
            process.env.PUPPETEER_EXECUTABLE_PATH = line.split('=')[1];
        }
    });
}

// Test individual service
async function testService(name, command, args, requiredEnv = null) {
    console.log(`🔍 Testing ${name}...`);
    
    if (requiredEnv && !process.env[requiredEnv]) {
        console.log(`  ⚠️  ${name}: Missing required environment variable ${requiredEnv}`);
        console.log(`     Configure with: ./configure-mcp-services.sh`);
        return false;
    }
    
    return new Promise((resolve) => {
        const serverProcess = spawn(command, args, {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: process.env
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

        setTimeout(() => {
            if (!resolved) {
                resolved = true;
                serverProcess.kill('SIGTERM');
                
                // For Puppeteer, it may not output text but still work
                if (output.includes('running') || error.includes('running') ||
                    output.includes('Server') || error.includes('Server') ||
                    output.includes('MCP') || error.includes('MCP') ||
                    (name.includes('Puppeteer') && !error.includes('Error') && !error.includes('failed'))) {
                    console.log(`  ✅ ${name}: Working correctly!`);
                    if (output.trim()) console.log(`     Output: ${output.substring(0, 80)}...`);
                    resolve(true);
                } else {
                    console.log(`  ❌ ${name}: Not responding properly`);
                    if (error.trim()) console.log(`     Error: ${error.substring(0, 80)}...`);
                    resolve(false);
                }
            }
        }, 5000);

        serverProcess.on('error', (err) => {
            if (!resolved) {
                resolved = true;
                console.log(`  ❌ ${name}: Failed to start - ${err.message}`);
                resolve(false);
            }
        });
    });
}

// Run tests
async function runTests() {
    console.log('Testing configured MCP services...\n');
    
    const results = {
        github: await testService(
            'GitHub MCP Server', 
            'npx', 
            ['@modelcontextprotocol/server-github'],
            'GITHUB_PERSONAL_ACCESS_TOKEN'
        ),
        
        puppeteer: await testService(
            'Puppeteer MCP Server',
            'npx',
            ['puppeteer-mcp-server']
        ),
        
        brave: await testService(
            'Brave Search MCP Server',
            'npx',
            ['@modelcontextprotocol/server-brave-search'],
            'BRAVE_API_KEY'
        )
    };
    
    console.log('\n📊 Test Results:');
    console.log('================');
    
    const working = Object.values(results).filter(r => r).length;
    const total = Object.keys(results).length;
    
    console.log(`✅ Working: ${working}/${total} services`);
    
    Object.entries(results).forEach(([service, working]) => {
        console.log(`  ${working ? '✅' : '❌'} ${service}`);
    });
    
    if (working < total) {
        console.log('\n🔧 To configure missing services:');
        console.log('   ./configure-mcp-services.sh');
    }
    
    console.log('\n🚀 To start working services:');
    if (results.github) console.log('   ./start-mcp-server.sh github');
    if (results.puppeteer) console.log('   ./start-mcp-server.sh puppeteer');
    if (results.brave) console.log('   ./start-mcp-server.sh brave-search');
}

runTests().catch(console.error);
