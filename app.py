import streamlit as st
from openai import OpenAI
import base64
import json
import re

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(
    page_title="TTB Label Verifier",
    page_icon="🔎",
    layout="centered"
)

# Standard TTB government health warning
STANDARD_GOVERNMENT_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women "
    "should not drink alcoholic beverages during pregnancy because of the "
    "risk of birth defects. (2) Consumption of alcoholic beverages impairs "
    "your ability to drive a car or operate machinery, and may cause health problems."
)


# ---------------------------------------------------------
# User Interface
# ---------------------------------------------------------

st.title("TTB Label Verification")

st.write(
    "Verify alcohol beverage label information against "
    "application data."
)

st.subheader("Application Information")

brand_name = st.text_input("Brand Name")

class_type = st.text_input("Class / Type")

alcohol_content = st.text_input(
    "Alcohol Content",
    placeholder="Example: 45% ABV"
)

net_contents = st.text_input(
    "Net Contents",
    placeholder="Example: 750 mL"
)

st.divider()

st.subheader("Label Image")

st.write(
    "Upload an image of the alcohol beverage label to verify."
)

uploaded_file = st.file_uploader(
    "Upload label",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.image(
        uploaded_file,
        caption="Uploaded Label",
        width=400
    )

st.divider()

verify_button = st.button(
    "Verify Label",
    type="primary",
    use_container_width=True
)


# ---------------------------------------------------------
# AI Label Analysis
# ---------------------------------------------------------

def analyze_label(uploaded_file):

    image_bytes = uploaded_file.getvalue()

    base64_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """
Read this alcohol beverage label carefully.

Extract these five fields:

- brand_name
- class_type
- alcohol_content
- net_contents
- government_warning

For government_warning:
Transcribe the warning exactly as it appears on the label.
Preserve capitalization, punctuation, parentheses, and wording.
Do not correct errors in the warning.

Return ONLY valid JSON in this exact format:

{
    "brand_name": "",
    "class_type": "",
    "alcohol_content": "",
    "net_contents": "",
    "government_warning": ""
}

If a field cannot be read, return an empty string for that field.
Do not guess.
"""
                    },
                    {
                        "type": "input_image",
                        "image_url": (
                            f"data:{uploaded_file.type};base64,"
                            f"{base64_image}"
                        )
                    }
                ]
            }
        ]
    )

    return json.loads(response.output_text)


# ---------------------------------------------------------
# Verification Logic
# ---------------------------------------------------------

def normalize_whitespace(value):
    """
    Ignore differences caused only by line wrapping
    or multiple spaces in the image.
    """
    return re.sub(r"\s+", " ", value).strip()


def normalize_general(value):
    """
    Normalization for ordinary application fields.
    """
    return normalize_whitespace(value).lower()


def normalize_alcohol(value):
    """
    Treat common alcohol-content wording as equivalent.
    Example:
    45% ABV
    45% Alc./Vol.
    """
    value = value.lower()

    value = value.replace("alc./vol.", "")
    value = value.replace("alc/vol", "")
    value = value.replace("alc. / vol.", "")
    value = value.replace("abv", "")

    return normalize_whitespace(value)


def verify_label(application_data, label_data):

    results = []

    # ---------------------------
    # Application fields
    # ---------------------------

    for field, expected_value in application_data.items():

        label_value = label_data.get(field, "")

        if field == "alcohol_content":

            expected_clean = normalize_alcohol(expected_value)
            label_clean = normalize_alcohol(label_value)

            if (
                expected_clean
                and label_clean
                and (
                    expected_clean in label_clean
                    or label_clean in expected_clean
                )
            ):
                status = "PASS"
            else:
                status = "FAIL"

        else:

            expected_clean = normalize_general(expected_value)
            label_clean = normalize_general(label_value)

            # Allows obvious presentation differences such as:
            # "Bourbon Whiskey"
            # vs.
            # "Kentucky Straight Bourbon Whiskey"

            if (
                expected_clean
                and label_clean
                and (
                    expected_clean in label_clean
                    or label_clean in expected_clean
                )
            ):
                status = "PASS"
            else:
                status = "FAIL"

        results.append({
            "field": field,
            "status": status,
            "expected": expected_value,
            "found": label_value
        })

    # ---------------------------
    # Government Warning
    # ---------------------------

    warning_found = label_data.get(
        "government_warning",
        ""
    )

    # Ignore line wrapping from the physical label,
    # but preserve capitalization and punctuation.
    expected_warning = normalize_whitespace(
        STANDARD_GOVERNMENT_WARNING
    )

    found_warning = normalize_whitespace(
        warning_found
    )

    if found_warning == expected_warning:
        warning_status = "PASS"
    else:
        warning_status = "FAIL"

    results.append({
        "field": "government_warning",
        "status": warning_status,
        "expected": STANDARD_GOVERNMENT_WARNING,
        "found": warning_found
    })

    return results


# ---------------------------------------------------------
# Application Data
# ---------------------------------------------------------

application_data = {
    "brand_name": brand_name,
    "class_type": class_type,
    "alcohol_content": alcohol_content,
    "net_contents": net_contents
}


# ---------------------------------------------------------
# Run Verification
# ---------------------------------------------------------

if verify_button:

    if uploaded_file is None:

        st.error(
            "Please upload a label image before verification."
        )

    elif not all([
        brand_name,
        class_type,
        alcohol_content,
        net_contents
    ]):

        st.error(
            "Please complete all application information "
            "before verification."
        )

    else:

        try:

            with st.spinner(
                "Analyzing label with AI..."
            ):

                label_data = analyze_label(
                    uploaded_file
                )

            results = verify_label(
                application_data,
                label_data
            )

            st.subheader(
                "Verification Results"
            )

            for result in results:

                field_name = (
                    result["field"]
                    .replace("_", " ")
                    .title()
                )

                if result["status"] == "PASS":

                    st.success(
                        f"PASS — {field_name}"
                    )

                else:

                    st.error(
                        f'FAIL — {field_name}: '
                        f'Expected "{result["expected"]}", '
                        f'found "{result["found"]}"'
                    )

        except Exception as error:

            st.error(
                "The label could not be analyzed. "
                "Please try again."
            )

            with st.expander(
                "Technical details"
            ):
                st.write(error)