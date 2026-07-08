# AI-Powered Alcohol Label Verification Prototype

## Deployed Application

Live prototype:
https://ttb-ai-label-verification-app-prototype.streamlit.app/

## Summary

This prototype assists TTB compliance agents by extracting information from alcohol beverage label artwork and comparing it against application-provided values.

The application is designed as a **human-in-the-loop review aid**, not an automated label approval system. It helps agents quickly identify likely matches, mismatches, missing information, image quality concerns, and items that require human review.

The prototype supports single-label review and basic batch upload. It checks common label elements such as brand name, class/type, alcohol content, net contents, name/address, country of origin, and the government health warning statement.

The solution uses AI for label extraction and structured interpretation. Compliance comparison is performed with deterministic Python rules so the results are more transparent, repeatable, and explainable.

---

## Purpose

TTB compliance agents review a high volume of alcohol label applications. This prototype demonstrates how AI-assisted extraction and rules-based comparison can help reduce manual review effort while keeping the final decision with the human reviewer.

The app allows an agent to:

1. Upload alcohol label artwork.
2. Enter expected application values.
3. Extract label information using an AI vision model.
4. Compare extracted label text against the expected values.
5. Flag matches, likely matches, mismatches, missing fields, and warning issues.
6. Export review results to CSV.

The prototype does **not** approve or reject labels automatically.

---
# Approach

- AI is used for text extraction and structured interpretation.
- Python rules perform deterministic comparison.
- The tool flags matches, likely matches, mismatches, missing values, warning failures, and image quality concerns.

---

# Assumptions

- This prototype is for evaluation and demonstration only.
- No sensitive, classified, taxpayer, financial, or personally identifiable Treasury data is used.
- AI-generated recommendations are advisory and require human review.
- The application demonstrates a possible workflow, not a production authorization system.
- A future production version would require authentication, audit logging, security scanning, privacy review, and agency-approved hosting.

---

## Tech Stack

- Python
- Streamlit
- OpenAI vision-capable model for image extraction
- Pandas for tables and CSV export
- Deterministic Python comparison rules

---

## Features

- Single label artwork upload
- Expected application data entry
- AI-assisted extraction from uploaded label artwork
- Deterministic comparison rules
- Overall status of Pass, Needs Review, or Fail
- Government health warning strict check
- ABV/proof equivalency check, such as 45% ABV = 90 proof
- Country of origin parsing, such as USA matching PRODUCT OF USA
- Image quality notes for glare, blur, angle, crop, low contrast, or unreadable areas
- Human-in-the-loop agent notes
- Basic batch upload support
- CSV export
- Processing time display
- Fallback and error handling when extraction fails or the API key is missing
- Documentation of assumptions, limitations, security considerations, and future enhancements

---

## Screens

### 1. Single Label Review

The single-label workflow allows an agent to upload one label image and enter expected application values.

Fields include:

- Beverage Type
- Brand Name
- Class / Type
- Alcohol Content
- Net Contents
- Name and Address
- Country of Origin

The app displays:

- Overall Status
- Processing Time
- Extracted Fields
- Comparison Results
- Government Warning Check
- Image Quality Notes
- Agent Notes
- CSV Download

### 2. Batch Review

The batch workflow allows an agent to upload multiple label images and receive a simple review summary for each file.

Batch results include:

- File Name
- Brand
- ABV
- Proof
- Warning Status
- Overall Status
- Image Quality
- Notes

Batch results can be downloaded as a CSV file.

### 3. Documentation

The app includes a documentation section covering:

- Purpose
- Approach
- Assumptions
- Limitations
- Security considerations
- Future production enhancements

---

## Local Setup and Run Instructions
- Clone the repository:

```bash
git clone https://github.com/cswackha/ttb-ai-label-verification-app.git
cd ttb-ai-label-verification-app
```

- Install Dependencies:

```bash
pip install -r requirements.txt
```
- Add local secrets:

Create `.streamlit/secrets.toml` and add the following:

```toml
OPENAI_API_KEY = "your-api-key-here"
AI_MODEL = "gpt-5.4-mini"
```

- Run Locally:
```bash
streamlit run app.py
```
