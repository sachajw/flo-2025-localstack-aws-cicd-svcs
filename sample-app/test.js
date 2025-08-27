#!/usr/bin/env node

/**
 * Simple tests for the demo app
 */

const DemoUtils = require('./index.js');

function assert(condition, message) {
    if (!condition) {
        throw new Error(message);
    }
    console.log(`✅ ${message}`);
}

function runTests() {
    console.log('🧪 Running LocalStack Demo App Tests...\n');

    try {
        // Test greet function
        assert(
            DemoUtils.greet() === 'Hello, World! Welcome to LocalStack CI/CD Workshop',
            'Default greeting works'
        );
        
        assert(
            DemoUtils.greet('LocalStack') === 'Hello, LocalStack! Welcome to LocalStack CI/CD Workshop',
            'Custom greeting works'
        );

        // Test math functions
        assert(DemoUtils.add(2, 3) === 5, 'Addition works');
        assert(DemoUtils.add(-1, 1) === 0, 'Addition with negatives works');
        
        assert(DemoUtils.multiply(4, 5) === 20, 'Multiplication works');
        assert(DemoUtils.multiply(0, 100) === 0, 'Multiplication by zero works');

        // Test isEven function
        assert(DemoUtils.isEven(2) === true, 'Even number detection works');
        assert(DemoUtils.isEven(3) === false, 'Odd number detection works');
        assert(DemoUtils.isEven(0) === true, 'Zero is even');

        // Test formatDate function
        const today = new Date('2025-01-15');
        assert(DemoUtils.formatDate(today) === '2025-01-15', 'Date formatting works');

        // Test randomBetween function
        const random = DemoUtils.randomBetween(1, 5);
        assert(random >= 1 && random <= 5, 'Random number is in range');

        console.log('\n🎉 All tests passed! The app is ready for deployment.');
        process.exit(0);
        
    } catch (error) {
        console.error(`❌ Test failed: ${error.message}`);
        process.exit(1);
    }
}

if (require.main === module) {
    runTests();
}