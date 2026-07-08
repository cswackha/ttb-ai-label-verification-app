 TTB Alcohol Label Verification Prototype

This prototype assists TTB compliance agents by extracting label information from alcohol beverage label images and comparing it against application-provided values. It is designed as a human-in-the-loop review aid, not an automated approval system.

The app supports single-label review and basic batch upload. It checks common label elements such as brand name, class/type, alcohol content, net contents, name/address, country of origin, and the government health warning statement.

The tool uses AI for text extraction and structured interpretation, then applies deterministic comparison rules for consistency, transparency, and repeatability.

The prototype does not approve or reject labels automatically. It highlights likely matches, mismatches, missing information, image quality concerns, and items requiring human review.

## Features

- Single label artwork upload
- Expected application data entry
- AI-assisted extraction from uploaded label artwork
- Deterministic comparison rules
- Government health warning strict check
- ABV/proof equivalency check, such as 45% ABV = 90 proof
- Image quality notes for glare, blur, angle, crop, low contrast, or unreadable areas
- Human-in-the-loop agent notes
- Batch upload support
- CSV export
- Processing time display
- Fallback/error handling when extraction fails or the API key is missing
- Documentation of assumptions, limitations, security considerations, and future enhancements

## Screens

1. **Single Label Review**
   - Upload Label
   - Enter expected application values
   - Run Verification
   - View overall status, processing time, extracted fields, comparison results, government warning check, and notes
   - Download Results as CSV

2. **Batch Review**
   - Upload multiple label images
   - Extract Brand, ABV, Proof, Warning status, Overall Status, Image Quality, Notes
   - Download Results as CSV

3. **Documentation**
   - Purpose, approach, limitations, security considerations, and future enhancements

## Tech Stack

- Python
- Streamlit
- OpenAI vision-capable model for extraction
- Pandas for table display and CSV export

## Local Setup in VS Code

### 1. Create the project folder

```bash
mkdir ttb-label-verification-prototype
cd ttb-label-verification-prototype
```

### 2. Create a virtual environment

Windows PowerShell:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your OpenAI API key

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Then edit `.env`:

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### 5. Run the app locally

```bash
streamlit run app.py
```

Open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## GitHub Setup

```bash
git init
git add .
git commit -m "Initial TTB label verification prototype"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ttb-label-verification-prototype.git
git push -u origin main
```

## Deploy to Streamlit Community Cloud

1. Push the repository to GitHub.
2. Go to Streamlit Community Cloud.
3. Select **New app**.
4. Choose the GitHub repository.
5. Set the main file path to:

```text
app.py
```

6. Add secrets in Streamlit app settings:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_MODEL = "gpt-4o-mini"
```

7. Deploy the app and copy the public app URL for the Treasury submission.

## How the App Makes Decisions

AI is used only to extract text and structure the label information. The comparison and review status are determined by Python rules.

### Text fields

The app compares brand name, class/type, net contents, name/address, and country of origin using:

- Exact match
- Case-insensitive and punctuation-insensitive likely match
- Similarity-based likely match
- Missing value
- Mismatch
- Needs review when one value contains another but is not exact

Example:

| Label | Application | Result | Reason |
|---|---|---|---|
| STONE'S THROW | Stone's Throw | Likely Match | Same text after case and punctuation normalization. |

### Alcohol content

The app parses ABV and proof values and checks equivalency.

Example:

| Label | Application | Result | Reason |
|---|---|---|---|
| 90 proof | 45% ABV | Likely Match | 45% ABV equals about 90 proof. |

### Government warning

The government warning statement is checked strictly. The app allows whitespace and line breaks to vary, but wording, capitalization, and required phrases must be preserved.

Required warning text used by the prototype:

```text
GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
```

Example:

| Label | Expected | Result | Reason |
|---|---|---|---|
| Government Warning: | GOVERNMENT WARNING: | Fail | Required heading is missing or not in all caps. |

## Assumptions

- This is a take-home prototype, not a production compliance system.
- Uploaded artwork is used only for prototype assessment.
- Label image quality may affect extraction accuracy.
- The app supports common label elements from the assignment scope.
- Country of origin is expected when relevant for imported products.
- Batch mode is intentionally simple and does not yet match against a CSV of application records.

## Limitations

- Does not approve or reject labels automatically.
- Does not validate every TTB rule or exception.
- Does not perform full field-of-vision analysis.
- Does not integrate with COLA Online or internal TTB systems.
- Does not store permanent audit logs.
- Does not include authentication or role-based access control.
- AI extraction may be incomplete for blurry, angled, low-contrast, or cropped images.

## Security Considerations

This prototype uses OpenAI for assessment purposes. A production version should use an agency-approved environment, approved model endpoint, authentication, authorization, audit logging, retention controls, encryption, monitoring, data minimization, and security review before handling sensitive or non-public application data.

Recommended production controls:

- Agency-approved model endpoint or hosted OCR/model environment
- Authentication and role-based access control
- Audit logging for uploads, extraction results, reviewer actions, and exports
- Retention and deletion controls
- Encryption in transit and at rest
- Malware scanning for uploaded files
- PII/sensitive data handling review
- Human reviewer sign-off workflow
- Model evaluation and regression testing

## Future Enhancements

- CSV upload for matching many application records to many label files
- Field-of-vision check for distilled spirits label elements
- Confidence score per field
- Reviewer approval/sign-off workflow
- Exportable PDF report
- Integration with COLA Online or internal case management systems
- Configurable rule sets by beverage type
- Better image pre-processing before extraction
- Agency-hosted model endpoint and audit trail