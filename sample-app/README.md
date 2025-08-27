# LocalStack Demo App

A simple Node.js utility library for demonstrating LocalStack CI/CD capabilities.

## Features

- **Greeting functions** - Welcome messages
- **Math utilities** - Basic arithmetic operations
- **Number utilities** - Even/odd detection
- **Date formatting** - ISO date strings
- **Random generators** - Numbers within ranges

## Usage

```bash
# Run the app
node index.js

# Run tests
npm test
```

## API

```javascript
const DemoUtils = require('./index.js');

DemoUtils.greet('LocalStack');           // "Hello, LocalStack! ..."
DemoUtils.add(2, 3);                     // 5
DemoUtils.multiply(4, 5);                // 20
DemoUtils.isEven(10);                    // true
DemoUtils.formatDate();                  // "2025-08-27"
DemoUtils.randomBetween(1, 100);         // Random number 1-100
```

## CI/CD Pipeline

This app demonstrates a complete LocalStack CI/CD workflow:

1. **Source** - Uploaded to S3 bucket
2. **Test** - Runs `npm test` via CodeBuild  
3. **Package** - Creates publishable npm package
4. **Deploy** - Publishes to CodeArtifact repository

All services run locally in LocalStack - no AWS costs!