#!/usr/bin/env node

/**
 * TDD Test Runner for AICleaner Card
 * Runs tests in headless browser environment
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function runUITests() {
    console.log('🧪 Starting AICleaner Card TDD Tests...\n');
    
    let browser;
    try {
        // Launch browser
        browser = await puppeteer.launch({
            headless: false, // Set to true for CI/CD
            devtools: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        
        const page = await browser.newPage();
        
        // Set viewport for responsive testing
        await page.setViewport({ width: 1200, height: 800 });
        
        // Navigate to test page
        const testFilePath = path.join(__dirname, 'test_aicleaner_card.html');
        const testFileUrl = `file://${testFilePath}`;
        
        console.log(`📄 Loading test page: ${testFileUrl}`);
        await page.goto(testFileUrl, { waitUntil: 'networkidle0' });
        
        // Wait for tests to complete
        await page.waitForTimeout(3000);
        
        // Get test results
        const testResults = await page.evaluate(() => {
            return {
                results: window.testFramework ? window.testFramework.results : [],
                logs: window.console ? window.console.logs : []
            };
        });
        
        // Display results
        console.log('📊 Test Results:');
        console.log('================');
        
        if (testResults.results.length === 0) {
            console.log('❌ No tests were executed. Check test setup.');
            return false;
        }
        
        let passed = 0;
        let failed = 0;
        
        testResults.results.forEach(result => {
            const icon = result.status === 'pass' ? '✅' : '❌';
            console.log(`${icon} ${result.name}`);
            if (result.error) {
                console.log(`   Error: ${result.error}`);
            }
            
            if (result.status === 'pass') passed++;
            else failed++;
        });
        
        console.log('\n📈 Summary:');
        console.log(`   Passed: ${passed}`);
        console.log(`   Failed: ${failed}`);
        console.log(`   Total:  ${passed + failed}`);
        
        const success = failed === 0;
        console.log(`\n${success ? '🎉' : '💥'} Tests ${success ? 'PASSED' : 'FAILED'}`);
        
        // Take screenshot for documentation
        await page.screenshot({ 
            path: path.join(__dirname, 'test_results.png'),
            fullPage: true 
        });
        console.log('📸 Screenshot saved: test_results.png');
        
        return success;
        
    } catch (error) {
        console.error('💥 Test execution failed:', error);
        return false;
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Check if running directly
if (require.main === module) {
    runUITests().then(success => {
        process.exit(success ? 0 : 1);
    });
}

module.exports = { runUITests };
