import base64
import json

import streamlit as st
from openai import OpenAI


# Connect to OpenAI using the API key stored in .streamlit/secrets.toml
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------

st.set_page_config(
    page_title="TTB Label Verifier",
    page_icon="🔎",
    layout="centered",
)

st.title("TTB Label Verification")

st.write(
    "Verify alcohol beverage label information against "
    "application data."
)


# ---------------------------------------------------------
# APPLICATION INFORMATION
# ---------------------------------------------------------

st.subheader("Application Information")

brand_name = st.text_input("Brand Name")

class_type = st.text_input("Class / Type")

alcohol_content = st.text_input(
    "Alcohol Content",
    placeholder="Example: 45% ABV",
)

net_contents = st.text_input(
    "Net Contents",
    placeholder="Example: 750 mL",
)

st.divider()


# ---------------------------------------------------------
# LABEL IMAGE
# ---------------------------------------------------------

st.subheader("Label Image")

st.write(
    "Upload an image of the alcohol beverage label to verify."
)

uploaded_file = st.file_uploader(
    "Upload label",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    st.image(
        uploaded_file,
        caption="Uploaded Label",
        width=400,
    )

st.divider()

verify_button = st.button(
    "Verify Label",
    type="primary",
    use_container_width=True,
)


# ---------------------------------------------------------
# AI LABEL ANALYSIS
# ---------------------------------------------------------

def analyze_label(uploaded_file):
    image_bytes = uploaded_file.getvalue()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """
Read this alcohol beverage label.

Extract these four fields:

- brand_name
- class_type
- alcohol_content
- net_contents

Return ONLY valid JSON in this exact format:

{
    "brand_name": "",
    "class_type": "",
    "alcohol_content": "",
    "net_contents": ""
}

If a field cannot be read, return an empty string for that field.

Do not guess.
""",
                    },
                    {
                        "type": "input_image",
                        "image_url": (
                            f"data:{uploaded_file.type};"
                            f"base64,{base64_image}"
                        ),
                    },
                ],
            }
        ],
    )

    return json.loads(response.output_text)


# ---------------------------------------------------------
# NORMALIZATION
# ---------------------------------------------------------

def normalize_text(value):
    return (
        value.lower()
        .replace(".", "")
        .replace("'", "")
        .strip()
    )


def normalize_alcohol(value):
    return (
        value.lower()
        .replace("alc/vol", "")
        .replace("alc./vol.", "")
        .replace("alc./vol", "")
        .replace("abv", "")
        .replace("alcohol by volume", "")
        .strip()
    )


# ---------------------------------------------------------
# VERIFICATION
# ---------------------------------------------------------

def verify_label(application_data, label_data):
    results = []

    for field, expected_value in application_data.items():
        label_value = label_data.get(field, "")

        if field == "alcohol_content":
            expected_clean = normalize_alcohol(expected_value)
            label_clean = normalize_alcohol(label_value)

        else:
            expected_clean = normalize_text(expected_value)
            label_clean = normalize_text(label_value)

        if not expected_clean or not label_clean:
            status = "FAIL"

        elif (
            expected_clean == label_clean
            or expected_clean in label_clean
            or label_clean in expected_clean
        ):
            status = "PASS"

        else:
            status = "FAIL"

        results.append(
            {
                "field": field,
                "status": status,
                "expected": expected_value,
                "found": label_value,
            }
        )

    return results


# ---------------------------------------------------------
# APPLICATION DATA
# ---------------------------------------------------------

application_data = {
    "brand_name": brand_name,
    "class_type": class_type,
    "alcohol_content": alcohol_content,
    "net_contents": net_contents,
}


# ---------------------------------------------------------
# RUN VERIFICATION
# ---------------------------------------------------------

if verify_button:

    if uploaded_file is None:
        st.error(
            "Please upload a label image before verification."
        )

    else:

        with st.spinner("Analyzing label with AI..."):
            label_data = analyze_label(uploaded_file)

        results = verify_label(
            application_data,
            label_data,
        )

        st.subheader("Verification Results")

        for result in results:

            field_name = (
                result["field"]
                .replace("_", " ")
                .title()
            )

            if result["status"] == "PASS":

                st.success(
                    f'PASS — {field_name}'
                )

            else:

                st.error(
                    f'FAIL — {field_name}: '
                    f'Expected "{result["expected"]}", '
                    f'found "{result["found"]}"'
                )