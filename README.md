# VocalTranscribe API Service

Welcome to the VocalTranscribe API Service. This server, built using Python, Flask, SQLite, and the SpeechRecognition library, provides endpoints for user registration, API key generation, and audio file transcription. It supports transcription in various languages and ensures secure access through HTTPS.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
    - [Register New Account](#register-new-account)
    - [Generate API Key](#generate-api-key)
    - [Transcribe Audio](#transcribe-audio)

4. [Subscription Plans](#subscription-plans)
5. [Endpoints](#endpoints)
6. [SSL Configuration](#ssl-configuration)
7. [Database Setup](#database-setup)
8. [License](#license)
9. [Contributing](#contributing)

## Features

- **User Registration**: Create a user account with a subscription plan.
- **API Key Generation**: Generate an API key using a JWT token.
- **Speech-to-Text**: Transcribe audio files into text in various languages.

- **Secure Communication**: Ensure secure API communication through HTTPS.
- **Subscription Plans**: Choose from Free, Silver and Gold plans based on transcription limits.

## Installation

1. Clone the Repository:
```bash
git clone https://github.com/swissmarley/vocaltranscribe-api.git
cd vocaltranscribe-api
```

2. Install Dependencies:
```bash
pip install -r requirements.txt
```

3. Setup SSL Certificates: Ensure you have `cert.pem` and `key.pem` in your project root.

4. Database Setup: Create the database by running:
```bash
python create_db.py
```

## Usage

### Register New Account
To create a new user account with a subscription plan, use the `create_account.py` script:
```bash
python create_account.py user@example.com --plan silver
```

### Generate API Key
Generate an API key by making a POST request with your JWT token:
```bash
curl -X POST https://localhost:5003/generate-api-key \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Transcribe Audio
To transcribe an audio file, make a POST request with your API key, the audio file, and the language:
```bash
curl -X POST -H "X-API-Key: YOUR_API_KEY" \
     -F "audio=@speech.mp3" \
     -F "language=spanish" \
     https://localhost:5003/speech-to-text
```

## Subscription Plans
- **Free**: 50 transcriptions per month.
- **Silver**: 500 transcriptions per month.

- **Gold**: 2000 transcriptions per month.

## Endpoints
- **POST** `/register`: Register a new user account.
- **POST** `/generate-api-key`: Generate an API key.

- **POST** `/speech-to-text`: Transcribe an audio file.

## SSL Configuration
Ensure you have SSL certificates (`cert.pem` and `key.pem`) configured for HTTPS.

## Database Setup
To set up the database, run:
```bash
python create_db.py
```

To add a user with a subscription plan, run:
```bash
python create_account.py user@example.com --plan silver
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please read our Contributing Guidelines for more details.
