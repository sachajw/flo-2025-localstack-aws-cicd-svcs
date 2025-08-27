#!/usr/bin/env node

/**
 * LocalStack CI/CD Workshop Demo App
 * A simple utility library for demonstration purposes
 */

class DemoUtils {
    static greet(name = 'World') {
        return `Hello, ${name}! Welcome to LocalStack CI/CD Workshop`;
    }

    static add(a, b) {
        return a + b;
    }

    static multiply(a, b) {
        return a * b;
    }

    static isEven(number) {
        return number % 2 === 0;
    }

    static formatDate(date = new Date()) {
        return date.toISOString().split('T')[0];
    }

    static randomBetween(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
}

// Export for use as a module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DemoUtils;
}

// CLI usage
if (require.main === module) {
    console.log(DemoUtils.greet());
    console.log(`Today is: ${DemoUtils.formatDate()}`);
    console.log(`Random number: ${DemoUtils.randomBetween(1, 100)}`);
    console.log(`2 + 3 = ${DemoUtils.add(2, 3)}`);
    console.log(`4 * 5 = ${DemoUtils.multiply(4, 5)}`);
    console.log(`10 is even: ${DemoUtils.isEven(10)}`);
}