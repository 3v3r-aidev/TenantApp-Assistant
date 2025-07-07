import openai
import fitz
import io
from PIL import Image
import json
import base64
import streamlit as st

EXTRACTED_DATA_PATH = "Template_Data_Holder.xlsx"

def extract_images_from_pdf(pdf_path):
    """Extract all pages from PDF as PIL images."""
    images = []
    doc = fitz.open(pdf_path)
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append(img)
    return images


def call_gpt_vision_api(images):
    """Send the image(s) to GPT-4o for structured data extraction."""
    openai.api_key = st.secrets["openai"]["OPENAI_API_KEY"]
    image_parts = []
    for img in images:
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_base64}"
            }
        })

    messages = [
        {
            "role": "system",
            "content": (
                "Extract structured tenant application data and return a JSON object using the exact schema below. "
"All fields must be included, even if null. Do NOT add explanations. Focus especially on extracting "
"**C. Representation and Marketing**, **Employment and Other Income**, and **F. Vehicle Information** sections — these are required.\n\n"

"Return only a valid JSON object with this format:\n\n"

"{\n"
'  "Property Address": string | null,\n'
'  "Move-in Date": string | null,\n'
'  "FullName": string | null,\n'
'  "PhoneNumber": string | null,\n'
'  "Email": string | null,\n'
'  "DOB": string | null,\n'
'  "SSN": string | null,\n'
'  "Applicant\'s Current Address": string | null,\n'
'  "Landlord or Property Manager\'s Name": string | null,\n'
'  "IDType": string | null,\n'
'  "DriverLicenseNumber": string | null,\n'
'  "IDIssuer": string | null,\n'
'  "Nationality": string | null,\n'
'  "FormSource": string | null,\n'
'  "ApplicationDate": string | null,\n'
'  "Phone:Day:": string | null,\n\n'

'  "Applicant\'s Current Address": {\n,
'    "Phone:Day": string | null, \n'}, \n\n

'  "C.Representation and Marketing": {\n'
'    "Name": string | null,\n'
'    "Company": string | null,\n'
'    "E-mail": string | null,\n'
'    "Phone Number": string | null\n'
'  },\n\n'

'  "Employment and Other Income:": {\n'
'    "Applicant\'s Current Employer": string | null,\n'
'    "Current Employer Details": {\n'
'      "Employment Verification Contact:": string | null,\n'
'      "Address": string | null,\n'
'      "Phone:": string | null,\n'
'      "E-mail": string | null,\n'
'      "Position": string | null,\n'
'      "Start Date": string | null,\n'
'      "Gross Monthly Income": string | null\n'
'    },\n'
'    "Child Support": string | null\n'
'  },\n\n'

'  "F. Vehicle Information:": {\n'
'    "Type": string | null,\n'
'    "Year": string | null,\n'
'    "Make": string | null,\n'
'    "Model": string | null,\n'
'    "Monthly Payment": string | null\n'
'  }\n'
"}\n\n"

"Repeat: In the 'Employment and Other Income:' section, you should extract the value of 'Applicant's Current Employer' as a string. "
"Then extract the values from the block under it using labels like 'Address', 'Phone:', and 'Start Date'. "
"In the top-level fields, also extract 'Phone:Day:' if present. Do not skip it. "
"If a value is missing, return null. Do not assume or reuse values from prior examples."

            )
        },
        {
            "role": "user",
            "content": image_parts
        }
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=1000
        )
        content = response.choices[0].message.content or ""
        print("GPT Raw Output:", content)
        return {"GPT_Output": content.strip()}
    except Exception as e:
        return {"error": str(e)}


def process_pdf(pdf_path):
    images = extract_images_from_pdf(pdf_path)
    extracted_data = call_gpt_vision_api(images)
    return extracted_data, {}


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_data = ""
    for page in doc:
        text_data += page.get_text()
    return text_data


def flatten_extracted_data(data):
    """Flattens structured GPT-extracted tenant application data to a flat dict for Excel."""

    employment = data.get("Employment and Other Income:", {})
    employer_name = employment.get("Applicant's Current Employer", "")
    employer_info = employment.get("Current Employer Details", {}) if isinstance(employment.get("Current Employer Details"), dict) else {}

    vehicle = data.get("F. Vehicle Information:", {})
    rep = data.get("C.Representation and Marketing", {})

    # Handle Applicant's Current Address which could be a dict or string
    address = data.get("Applicant's Current Address", "")
    address_phone = ""
    if isinstance(address, dict):
        address_phone = address.get("Phone:Day", "")
        address = ""  # Assume string address is not present if it's nested

    flat = {
        # Top-level
        "Property Address": data.get("Property Address", ""),
        "Move-in Date": data.get("Move-in Date", ""),
        "FullName": data.get("FullName", ""),
        "DOB": data.get("DOB", ""),
        "SSN": data.get("SSN", ""),
        "Email": data.get("Email", ""),
        "PhoneNumber": data.get("PhoneNumber", ""),
        "Applicant's Current Address": address,
        "Landlord Phone": address_phone,
        "Landlord or Property Manager's Name": data.get("Landlord or Property Manager's Name", ""),
        "DriverLicenseNumber": data.get("DriverLicenseNumber", ""),
        "IDType": data.get("IDType", ""),
        "IDIssuer": data.get("IDIssuer", ""),
        "Nationality": data.get("Nationality", ""),
        "FormSource": data.get("FormSource", ""),
        "ApplicationDate": data.get("ApplicationDate", ""),

        # Rep
        "Rep Name": rep.get("Name", ""),
        "Rep Company": rep.get("Company", ""),
        "Rep Email": rep.get("E-mail", ""),
        "Rep Phone": rep.get("Phone Number", ""),

        # Employment
        "Applicant's Current Employer": employer_name,
        "Employment Verification Contact": employer_info.get("Employment Verification Contact:", ""),
        "Employer Address": employer_info.get("Address", ""),
        "Employer Phone": employer_info.get("Phone:", ""),
        "Employer Email": employer_info.get("E-mail", ""),
        "Start Date": employer_info.get("Start Date", ""),
        "Gross Monthly Income": employer_info.get("Gross Monthly Income", ""),
        "Position": employer_info.get("Position", ""),
        "Child Support": employment.get("Child Support", ""),

        # Vehicle
        "Type": vehicle.get("Type", ""),
        "Year": vehicle.get("Year", ""),
        "Make": vehicle.get("Make", ""),
        "Model": vehicle.get("Model", ""),
        "Monthly Payment": vehicle.get("Monthly Payment", "")
    }

    return {k: ("" if v is None else v) for k, v in flat.items()}


def parse_gpt_output(form_data):
    """
    Parses the GPT-4 JSON string from the form_data['GPT_Output'] key and returns a Python dict.
    Strips leading/trailing markdown backticks and safely loads JSON.
    """
    raw = form_data.get("GPT_Output", "").strip()
    print("GPT Raw Output:", raw)

    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.endswith("```"):
        raw = raw[:-3]

    try:
        parsed = json.loads(raw)

        # Patch aliases if any
        if "Employment" in parsed and "Employment and Other Income:" not in parsed:
            parsed["Employment and Other Income:"] = parsed["Employment"]

        if "Vehicle" in parsed and "F. Vehicle Information:" not in parsed:
            parsed["F. Vehicle Information:"] = parsed["Vehicle"]

        if "Representation" in parsed and "C.Representation and Marketing" not in parsed:
            parsed["C.Representation and Marketing"] = parsed["Representation"]

        return parsed

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid GPT JSON string: {e}")
