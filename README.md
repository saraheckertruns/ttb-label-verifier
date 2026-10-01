# TTB Alcohol Label Verification Prototype

A lightweight AI-powered prototype that compares information from an alcohol beverage label against application data and identifies potential discrepancies for human review.

## Overview

The application allows a user to enter application information and upload an image of an alcohol beverage label. The system uses an OpenAI vision-capable model to extract key information from the label and compare it against the submitted application data.

The prototype verifies four fields:

- Brand Name
- Class / Type
- Alcohol Content
- Net Contents

Each field is displayed as PASS or FAIL based on the comparison.

## Approach

The prototype uses:

- Python
- Streamlit for the user interface
- OpenAI API for image analysis and structured data extraction
- Rule-based comparison logic for verification

The AI model extracts structured label information as JSON. The application then compares the extracted information with the application data entered by the user.

Basic normalization is used for alcohol content so equivalent formats such as `45% ABV` and `45% alc/vol` can be treated as matching values.

## Running Locally

1. Clone the repository.

2. Create and activate a Python virtual environment.

3. Install dependencies:

    pip install -r requirements.txt

4. Create `.streamlit/secrets.toml` and add your OpenAI API key:

    OPENAI_API_KEY = "your-api-key"

5. Start the application:

    streamlit run app.py

6. Open the local Streamlit URL displayed in the terminal.

## Assumptions and Limitations

This project is intended as a functional prototype rather than a production compliance system.

- Label extraction depends on image quality and readability.
- The prototype evaluates four primary fields.
- AI-extracted information should support, rather than replace, human compliance review.
- Additional normalization and regulatory validation rules would be appropriate for a production implementation.
- Production deployment would require additional security, testing, monitoring, auditability, and error handling.

## Future Improvements

Potential next steps include expanding regulatory validation rules, confidence scoring, human-review workflows, audit logging, additional label fields, and integration with existing application systems.