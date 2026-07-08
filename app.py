"""TTB Alcohol Label Verification Prototype

Streamlit app for AI-assisted extraction and deterministic comparison of
alcohol beverage label artwork against application-provided values.
"""

from __future__ import annotations

import base64
import json
import os
import re
import string
import time
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st
from openai import OpenAI

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

APP_TITLE = "TTB Alcohol Label Verification Prototype"

GOVERNMENT_WARNING_REQUIRED = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not "
    "drink alcoholic beverages during pregnancy because of the risk of birth "
    "defects. (2) Consumption of alcoholic beverages impairs your ability to "
    "drive a car or operate machinery, and may cause health problems."
)

EXTRACTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "brand_name": {"type": "string"},
        "class_type": {"type": "string"},
        "alcohol_content": {"type": "string"},
        "proof": {"type": "string"},
        "net_contents": {"type": "string"},
        "producer_bottler_name": {"type": "string"},
        "address": {"type": "string"},
        "country_of_origin": {"type": "string"},
        "government_warning_text": {"type": "string"},
        "unreadable_areas": {"type": "array", "items": {"type": "string"}},
        "confidence_notes": {"type": "string"},
        "image_quality": {"type": "string", "enum": ["Good", "Review Needed"]},
        "image_quality_reason": {"type": "string"},
    },
    "required": [
        "brand_name",
        "class_type",
        "alcohol_content",
        "proof",
        "net_contents",
        "producer_bottler_name",
        "address",
        "country_of_origin",
        "government_warning_text",
        "unreadable_areas",
        "confidence_notes",
        "image_quality",
        "image_quality_reason",
    ],
}

EXTRACTION_PROMPT = f"""
You are assisting a TTB alcohol beverage label compliance agent.
Extract only text that appears on the uploaded label artwork. Do not infer legal compliance.

Return structured fields for:
- brand_name
- class_type
- alcohol_content
- proof
- net_contents
- producer_bottler_name
- address
- country_of_origin
- government_warning_text
- unreadable_areas
- confidence_notes
- image_quality: Good or Review Needed
- image_quality_reason

Important:
- If a field is not visible, return an empty string.
- Preserve capitalization for the government warning statement.
- Preserve punctuation for the government warning statement.
- Use unreadable_areas to identify glare, blur, angled text, low resolution, cropped areas, or text blocked by artwork.
- Use image_quality = "Review Needed" if glare, blur, shadows, crop, low contrast, or angle could affect extraction.
- Do not approve or reject the label. Extraction only.

Reference warning text for comparison context only:
{GOVERNMENT_WARNING_REQUIRED}
""".strip()

FIELD_DISPLAY = {
    "brand_name": "Brand Name",
    "class_type": "Class / Type",
    "alcohol_content": "Alcohol Content",
    "net_contents": "Net Contents",
    "name_address": "Name and Address",
    "country_of_origin": "Country of Origin",
}

COMPARISON_ORDER = [
    "brand_name",
    "class_type",
    "alcohol_content",
    "net_contents",
    "name_address",
    "country_of_origin",
    "government_warning",
]


def get_openai_api_key() -> str:
    """Return API key from environment or Streamlit secrets."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key

    try:
        return str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        return ""


def get_model_name() -> str:
    """Return OpenAI model name from env/secrets or use a fast vision-capable default."""
    model = os.getenv("OPENAI_MODEL", "").strip()
    if model:
        return model
    try:
        secret_model = str(st.secrets.get("OPENAI_MODEL", "")).strip()
        if secret_model:
            return secret_model
    except Exception:
        pass
    return "gpt-4o-mini"


def image_to_data_url(uploaded_file: Any) -> str:
    bytes_data = uploaded_file.getvalue()
    mime_type = uploaded_file.type or "image/png"
    encoded = base64.b64encode(bytes_data).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def blank_extraction(error_message: str = "") -> Dict[str, Any]:
    return {
        "brand_name": "",
        "class_type": "",
        "alcohol_content": "",
        "proof": "",
        "net_contents": "",
        "producer_bottler_name": "",
        "address": "",
        "country_of_origin": "",
        "government_warning_text": "",
        "unreadable_areas": [],
        "confidence_notes": error_message,
        "image_quality": "Review Needed" if error_message else "Good",
        "image_quality_reason": error_message,
    }


def extract_label_fields(uploaded_file: Any) -> Tuple[Dict[str, Any], str]:
    """Extract label fields from an uploaded image using OpenAI vision."""
    api_key = get_openai_api_key()
    if not api_key:
        return (
            blank_extraction("OPENAI_API_KEY is not configured. Add it locally or in Streamlit secrets."),
            "Missing API key",
        )

    try:
        client = OpenAI(api_key=api_key)
        data_url = image_to_data_url(uploaded_file)
        response = client.responses.create(
            model=get_model_name(),
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": EXTRACTION_PROMPT},
                        {"type": "input_image", "image_url": data_url, "detail": "auto"},
                    ],
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ttb_label_extraction",
                    "schema": EXTRACTION_SCHEMA,
                    "strict": True,
                }
            },
        )
        extraction = json.loads(response.output_text)

        # Defensive fill in case model/API changes return a partial payload.
        base = blank_extraction()
        base.update(extraction)
        return base, ""
    except Exception as exc:  # noqa: BLE001 - prototype should show graceful fallback
        return blank_extraction(f"Extraction failed: {exc}"), str(exc)


def collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_text(value: str) -> str:
    value = collapse_whitespace(value).lower()
    value = value.translate(str.maketrans("", "", string.punctuation))
    return re.sub(r"\s+", " ", value).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def parse_abv(value: str) -> float | None:
    value = value or ""
    patterns = [
        r"(\d+(?:\.\d+)?)\s*%\s*(?:alc\.?/?vol\.?|abv|alcohol by volume)?",
        r"(?:alc\.?/?vol\.?|abv|alcohol by volume)\s*(\d+(?:\.\d+)?)\s*%?",
    ]
    for pattern in patterns:
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


def parse_proof(value: str) -> float | None:
    value = value or ""
    match = re.search(r"(\d+(?:\.\d+)?)\s*proof", value, flags=re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def compare_text(field_name: str, expected: str, extracted: str) -> Dict[str, str]:
    expected = collapse_whitespace(expected)
    extracted = collapse_whitespace(extracted)
    display = FIELD_DISPLAY.get(field_name, field_name)

    if not expected:
        return {
            "Field": display,
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Not Provided",
            "Reason": "No expected application value was entered for this field.",
        }

    if not extracted:
        return {
            "Field": display,
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Missing",
            "Reason": "Expected application value was entered, but no matching label text was extracted.",
        }

    if expected == extracted:
        return {
            "Field": display,
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Match",
            "Reason": "Exact text match.",
        }

    if normalize_text(expected) == normalize_text(extracted):
        return {
            "Field": display,
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Likely Match",
            "Reason": "Same text after case and punctuation normalization.",
        }

    score = similarity(expected, extracted)
    if score >= 0.85:
        return {
            "Field": display,
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Likely Match",
            "Reason": f"Text is very similar after normalization. Similarity score: {score:.2f}.",
        }

    if normalize_text(expected) in normalize_text(extracted) or normalize_text(extracted) in normalize_text(expected):
        return {
            "Field": display,
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Needs Review",
            "Reason": "One value appears to contain the other, but the text is not an exact match.",
        }

    return {
        "Field": display,
        "Expected": expected,
        "Extracted": extracted,
        "Result": "Mismatch",
        "Reason": "Extracted label text does not match the application value.",
    }


def compare_alcohol_content(expected: str, extracted_abv_text: str, extracted_proof_text: str) -> Dict[str, str]:
    expected = collapse_whitespace(expected)
    extracted_combined = collapse_whitespace(f"{extracted_abv_text} {extracted_proof_text}")

    if not expected:
        return {
            "Field": "Alcohol Content",
            "Expected": expected,
            "Extracted": extracted_combined,
            "Result": "Not Provided",
            "Reason": "No expected alcohol content was entered.",
        }

    if not extracted_combined:
        return {
            "Field": "Alcohol Content",
            "Expected": expected,
            "Extracted": extracted_combined,
            "Result": "Missing",
            "Reason": "Expected alcohol content was entered, but alcohol content was not extracted from the label.",
        }

    expected_abv = parse_abv(expected)
    expected_proof = parse_proof(expected)
    extracted_abv = parse_abv(extracted_abv_text)
    extracted_proof = parse_proof(extracted_proof_text or extracted_abv_text)

    if expected_abv is not None and extracted_abv is not None:
        if abs(expected_abv - extracted_abv) <= 0.2:
            return {
                "Field": "Alcohol Content",
                "Expected": expected,
                "Extracted": extracted_combined,
                "Result": "Match",
                "Reason": f"ABV values are equivalent within tolerance: {expected_abv:g}% vs {extracted_abv:g}%.",
            }

    if expected_proof is not None and extracted_proof is not None:
        if abs(expected_proof - extracted_proof) <= 0.5:
            return {
                "Field": "Alcohol Content",
                "Expected": expected,
                "Extracted": extracted_combined,
                "Result": "Match",
                "Reason": f"Proof values are equivalent within tolerance: {expected_proof:g} proof vs {extracted_proof:g} proof.",
            }

    if expected_abv is not None and extracted_proof is not None:
        equivalent_proof = expected_abv * 2
        if abs(equivalent_proof - extracted_proof) <= 0.5:
            return {
                "Field": "Alcohol Content",
                "Expected": expected,
                "Extracted": extracted_combined,
                "Result": "Likely Match",
                "Reason": f"ABV/proof equivalency detected: {expected_abv:g}% ABV equals about {equivalent_proof:g} proof.",
            }

    if expected_proof is not None and extracted_abv is not None:
        equivalent_abv = expected_proof / 2
        if abs(equivalent_abv - extracted_abv) <= 0.2:
            return {
                "Field": "Alcohol Content",
                "Expected": expected,
                "Extracted": extracted_combined,
                "Result": "Likely Match",
                "Reason": f"Proof/ABV equivalency detected: {expected_proof:g} proof equals about {equivalent_abv:g}% ABV.",
            }

    # Fall back to text comparison if numeric parsing did not resolve it.
    return compare_text("alcohol_content", expected, extracted_combined)


def compare_government_warning(extracted_warning: str) -> Dict[str, str]:
    extracted = collapse_whitespace(extracted_warning)
    expected = GOVERNMENT_WARNING_REQUIRED

    if not extracted:
        return {
            "Field": "Government Warning",
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Fail",
            "Reason": "Required government health warning statement was not extracted from the label.",
        }

    # Strict check: whitespace may vary on labels, but capitalization and wording should not.
    if collapse_whitespace(extracted) == collapse_whitespace(expected):
        return {
            "Field": "Government Warning",
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Match",
            "Reason": "Required warning statement matches exactly after whitespace normalization.",
        }

    if "GOVERNMENT WARNING:" not in extracted:
        return {
            "Field": "Government Warning",
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Fail",
            "Reason": "Required heading 'GOVERNMENT WARNING:' is missing or not in all caps.",
        }

    required_phrases = [
        "According to the Surgeon General",
        "women should not drink alcoholic beverages during pregnancy",
        "risk of birth defects",
        "impairs your ability to drive a car or operate machinery",
        "may cause health problems",
    ]
    missing_phrases = [phrase for phrase in required_phrases if phrase not in extracted]
    if missing_phrases:
        return {
            "Field": "Government Warning",
            "Expected": expected,
            "Extracted": extracted,
            "Result": "Fail",
            "Reason": "Warning text is missing required wording: " + "; ".join(missing_phrases),
        }

    return {
        "Field": "Government Warning",
        "Expected": expected,
        "Extracted": extracted,
        "Result": "Needs Review",
        "Reason": "Warning contains major required phrases, but wording, punctuation, or capitalization is not an exact match.",
    }


def run_comparison(expected: Dict[str, str], extraction: Dict[str, Any]) -> List[Dict[str, str]]:
    producer_address = collapse_whitespace(
        f"{extraction.get('producer_bottler_name', '')} {extraction.get('address', '')}"
    )

    results = [
        compare_text("brand_name", expected.get("brand_name", ""), extraction.get("brand_name", "")),
        compare_text("class_type", expected.get("class_type", ""), extraction.get("class_type", "")),
        compare_alcohol_content(
            expected.get("alcohol_content", ""),
            extraction.get("alcohol_content", ""),
            extraction.get("proof", ""),
        ),
        compare_text("net_contents", expected.get("net_contents", ""), extraction.get("net_contents", "")),
        compare_text("name_address", expected.get("name_address", ""), producer_address),
        compare_text("country_of_origin", expected.get("country_of_origin", ""), extraction.get("country_of_origin", "")),
        compare_government_warning(extraction.get("government_warning_text", "")),
    ]
    return results


def determine_overall_status(comparison_rows: List[Dict[str, str]], extraction: Dict[str, Any]) -> str:
    results = [row["Result"] for row in comparison_rows]

    if "Fail" in results:
        return "Fail"

    # Required application fields that should fail if the entered value mismatches or is missing.
    fail_results = {"Missing", "Mismatch"}
    required_fields = {
        "Brand Name",
        "Class / Type",
        "Alcohol Content",
        "Net Contents",
        "Name and Address",
    }
    for row in comparison_rows:
        if row["Field"] in required_fields and row["Result"] in fail_results:
            return "Fail"

    if extraction.get("image_quality") == "Review Needed":
        return "Needs Review"

    review_results = {"Likely Match", "Needs Review", "Missing", "Mismatch"}
    if any(result in review_results for result in results):
        return "Needs Review"

    return "Pass"


def status_badge(status: str) -> None:
    if status == "Pass":
        st.success("Overall Status: Pass")
    elif status == "Fail":
        st.error("Overall Status: Fail")
    else:
        st.warning("Overall Status: Needs Review")


def extraction_to_display(extraction: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Brand Name": extraction.get("brand_name", ""),
        "Class / Type": extraction.get("class_type", ""),
        "Alcohol Content": extraction.get("alcohol_content", ""),
        "Proof": extraction.get("proof", ""),
        "Net Contents": extraction.get("net_contents", ""),
        "Producer / Bottler": extraction.get("producer_bottler_name", ""),
        "Address": extraction.get("address", ""),
        "Country of Origin": extraction.get("country_of_origin", ""),
        "Government Warning Text": extraction.get("government_warning_text", ""),
        "Unreadable Areas": "; ".join(extraction.get("unreadable_areas", []) or []),
        "Confidence Notes": extraction.get("confidence_notes", ""),
        "Image Quality": extraction.get("image_quality", ""),
        "Image Quality Reason": extraction.get("image_quality_reason", ""),
    }


def csv_download_button(df: pd.DataFrame, file_name: str, label: str) -> None:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv,
        file_name=file_name,
        mime="text/csv",
        use_container_width=True,
    )


def single_label_review() -> None:
    st.header("Single Label Review")
    st.caption("Upload one label image, enter expected application values, and run verification.")

    uploaded_file = st.file_uploader(
        "Upload Label",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False,
        key="single_upload",
    )

    st.subheader("Expected Application Values")
    col1, col2 = st.columns(2)
    with col1:
        beverage_type = st.selectbox(
            "Beverage Type",
            ["Distilled Spirits", "Wine", "Malt Beverage"],
        )
        brand_name = st.text_input("Brand Name")
        class_type = st.text_input("Class / Type")
        alcohol_content = st.text_input("Alcohol Content", placeholder="Example: 45% ABV or 90 proof")
    with col2:
        net_contents = st.text_input("Net Contents", placeholder="Example: 750 mL")
        name_address = st.text_area("Name and Address", height=80)
        country_of_origin = st.text_input("Country of Origin", placeholder="Required for imports when applicable")

    agent_notes = st.text_area("Agent Notes", height=80, placeholder="Optional human review notes")

    run_button = st.button("Run Verification", type="primary", use_container_width=True)

    if run_button:
        if not uploaded_file:
            st.error("Please upload a label image before running verification.")
            return

        expected = {
            "beverage_type": beverage_type,
            "brand_name": brand_name,
            "class_type": class_type,
            "alcohol_content": alcohol_content,
            "net_contents": net_contents,
            "name_address": name_address,
            "country_of_origin": country_of_origin,
        }

        start = time.perf_counter()
        with st.spinner("Extracting label information and applying comparison rules..."):
            extraction, error_message = extract_label_fields(uploaded_file)
            comparison_rows = run_comparison(expected, extraction)
            elapsed = time.perf_counter() - start
            overall_status = determine_overall_status(comparison_rows, extraction)

        st.divider()
        status_badge(overall_status)
        st.metric("Processing Time", f"{elapsed:.2f} seconds")

        if error_message:
            st.error("Fallback/Error Handling: " + error_message)

        quality = extraction.get("image_quality", "Review Needed")
        quality_reason = extraction.get("image_quality_reason", "")
        if quality == "Good":
            st.info("Image Quality: Good")
        else:
            st.warning(
                "Image Quality: Review Needed. Image quality may affect verification. Agent review recommended. "
                + quality_reason
            )

        st.subheader("Extracted Fields")
        extraction_df = pd.DataFrame(
            [{"Field": key, "Extracted Value": value} for key, value in extraction_to_display(extraction).items()]
        )
        st.dataframe(extraction_df, use_container_width=True, hide_index=True)

        st.subheader("Comparison Results")
        comparison_df = pd.DataFrame(comparison_rows)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        st.subheader("Government Warning Check")
        warning_row = [row for row in comparison_rows if row["Field"] == "Government Warning"][0]
        if warning_row["Result"] == "Match":
            st.success(warning_row["Reason"])
        elif warning_row["Result"] == "Fail":
            st.error(warning_row["Reason"])
        else:
            st.warning(warning_row["Reason"])

        export_df = comparison_df.copy()
        export_df.insert(0, "File Name", uploaded_file.name)
        export_df.insert(1, "Beverage Type", beverage_type)
        export_df.insert(2, "Overall Status", overall_status)
        export_df["Processing Time Seconds"] = round(elapsed, 2)
        export_df["Agent Notes"] = agent_notes
        csv_download_button(export_df, "single_label_verification_results.csv", "Download Results")


def batch_review() -> None:
    st.header("Batch Review")
    st.caption(
        "Upload multiple label images. This first version extracts key fields and checks the government warning for each file."
    )

    uploaded_files = st.file_uploader(
        "Upload Labels",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="batch_upload",
    )

    if st.button("Run Batch Verification", type="primary", use_container_width=True):
        if not uploaded_files:
            st.error("Please upload one or more label images before running batch verification.")
            return

        rows: List[Dict[str, Any]] = []
        progress = st.progress(0)
        start_all = time.perf_counter()

        for idx, uploaded_file in enumerate(uploaded_files, start=1):
            start_one = time.perf_counter()
            with st.spinner(f"Processing {uploaded_file.name}..."):
                extraction, error_message = extract_label_fields(uploaded_file)
                warning = compare_government_warning(extraction.get("government_warning_text", ""))
                elapsed_one = time.perf_counter() - start_one

                status = "Pass"
                notes: List[str] = []
                if warning["Result"] == "Fail":
                    status = "Fail"
                    notes.append(warning["Reason"])
                elif warning["Result"] == "Needs Review":
                    status = "Needs Review"
                    notes.append(warning["Reason"])

                if extraction.get("image_quality") == "Review Needed" and status != "Fail":
                    status = "Needs Review"
                    notes.append("Image quality may affect verification. Agent review recommended.")

                if error_message:
                    status = "Needs Review" if status != "Fail" else status
                    notes.append(error_message)

                rows.append(
                    {
                        "File Name": uploaded_file.name,
                        "Brand": extraction.get("brand_name", ""),
                        "ABV": extraction.get("alcohol_content", ""),
                        "Proof": extraction.get("proof", ""),
                        "Warning": warning["Result"],
                        "Overall Status": status,
                        "Image Quality": extraction.get("image_quality", ""),
                        "Notes": " ".join(notes) or extraction.get("confidence_notes", ""),
                        "Processing Time Seconds": round(elapsed_one, 2),
                    }
                )
            progress.progress(idx / len(uploaded_files))

        total_elapsed = time.perf_counter() - start_all
        st.metric("Total Processing Time", f"{total_elapsed:.2f} seconds")
        batch_df = pd.DataFrame(rows)
        st.dataframe(batch_df, use_container_width=True, hide_index=True)
        csv_download_button(batch_df, "batch_label_verification_results.csv", "Download Results")


def documentation_tab() -> None:
    st.header("Prototype Notes")
    st.markdown(
        """
        **Purpose**  
        This prototype assists TTB compliance agents by extracting label information from alcohol beverage label images and comparing it against application-provided values. It is a human-in-the-loop review aid, not an automated approval system.

        **Approach**  
        - AI is used for text extraction and structured interpretation.
        - Python rules perform deterministic comparison.
        - The tool flags matches, likely matches, mismatches, missing values, warning failures, and image quality concerns.

        **Security Considerations**  
        This prototype may send uploaded label artwork to OpenAI for assessment purposes. A production version should use an agency-approved environment, approved model endpoint, authentication, authorization, audit logging, retention controls, encryption, monitoring, and security review before handling sensitive or non-public application data.

        **Limitations**  
        - Extraction accuracy depends on image quality.
        - The prototype does not validate every TTB labeling rule.
        - It does not make approval decisions.
        - Batch mode extracts fields and checks warning text; it does not yet match against a CSV of application records.

        **Future Enhancements**  
        - CSV upload for application records.
        - Field-of-vision checks for distilled spirits.
        - Confidence scoring per extracted field.
        - Audit trail and reviewer sign-off.
        - Role-based access control.
        - Integration with COLA Online or internal workflow systems.
        - Agency-hosted OCR/model endpoint.
        """
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🏷️", layout="wide")
    st.title(APP_TITLE)
    st.write(
        "AI-assisted extraction plus deterministic comparison rules for alcohol beverage label review."
    )

    with st.sidebar:
        st.subheader("Prototype Controls")
        st.write("Use plain workflow buttons: Upload Label, Run Verification, Download Results.")
        st.caption("Human-in-the-loop review aid only. Not an automated approval system.")
        if not get_openai_api_key():
            st.warning("OPENAI_API_KEY is not configured. Extraction will show a fallback error.")
        else:
            st.success("OpenAI API key configured.")
        st.caption(f"Model: {get_model_name()}")

    tab1, tab2, tab3 = st.tabs(["Single Label Review", "Batch Review", "Documentation"])
    with tab1:
        single_label_review()
    with tab2:
        batch_review()
    with tab3:
        documentation_tab()


if __name__ == "__main__":
    main()