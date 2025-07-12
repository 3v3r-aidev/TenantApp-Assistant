import base64
import io
import json
from pathlib import Path
from typing import List, Dict, Tuple

import fitz  # PyMuPDF
from PIL import Image
import openai
import streamlit as st

EXTRACTED_DATA_PATH = "Template_Data_Holder.xlsx"


def extract_images_from_pdf(pdf_path: str | Path) -> List[Image.Image]:
    images = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=300, colorspace=fitz.csRGB)
            images.append(Image.open(io.BytesIO(pix.tobytes("png"))))
    return images


def call_gpt_vision_api(images: List[Image.Image]) -> Dict[str, str]:
    openai.api_key = st.secrets["openai"]["OPENAI_API_KEY"]

    image_parts = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        image_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        })

    messages = [
        {
            "role": "system",
            "content": (
                "Extract structured tenant application data and return a JSON object using the exact schema below. "
                "All fields must be included, even if null. Do NOT add explanations.\n\n"
                "**Required focus:** Extract accurately the following sections:\n"
                "- C. Representation and Marketing\n"
                "- Employment and Other Income\n"
                "- E. Occupant Information\n"
                "- F. Vehicle Information\n"
                "- Applicant's Current Address (must be a nested object with Address, Phone:Day, Landlord Name)\n\n"
                "Return only this JSON format:\n"
                "{\n"
                '  "Property Address": string | null,\n'
                '  "Move-in Date": string | null,\n'
                '  "Monthly Rent": string | null,\n'
                '  "FullName": string | null,\n'
                '  "PhoneNumber": string | null,\n'
                '  "Email": string | null,\n'
                '  "DOB": string | null,\n'
                '  "SSN": string | null,\n'
                '  "Applicant\'s Current Address": {\n'
                '    "Address": string | null,\n'
                '    "Phone:Day": string | null,\n'
                '    "Landlord or Property Manager\'s Name": string | null\n'
                '  },\n'
                '  "IDType": string | null,\n'
                '  "DriverLicenseNumber": string | null,\n'
                '  "IDIssuer": string | null,\n'
                '  "Nationality": string | null,\n'
                '  "FormSource": string | null,\n'
                '  "ApplicationDate": string | null,\n'
                '  "C.Representation and Marketing": {\n'
                '    "Name": string | null,\n'
                '    "Company": string | null,\n'
                '    "E-mail": string | null,\n'
                '    "Phone Number": string | null\n'
                '  },\n'
                '  "Employment and Other Income:": {\n'
                '    "Applicant\'s Current Employer": string | null,\n'
                '    "Current Employer Details": {\n'
                '      "Employment Verification Contact": string | null,\n'
                '      "Address": string | null,\n'
                '      "Phone": string | null,\n'
                '      "E-mail": string | null,\n'
                '      "Position": string | null,\n'
                '      "Start Date": string | null,\n'
                '      "Gross Monthly Income": string | null\n'
                '    },\n'
                '    "Child Support": string | null\n'
                '  },\n'
                '  "E. Occupant Information": [\n'
                '    {\n'
                '      "Name": string | null,\n'
                '      "Relationship": string | null,\n'
                '      "DOB": string | null\n'
                '    }\n'
                '  ],\n'
                '  "F. Vehicle Information:": {\n'
                '    "Type": string | null,\n'
                '    "Year": string | null,\n'
                '    "Make": string | null,\n'
                '    "Model": string | null,\n'
                '    "Monthly Payment": string | null\n'
                '  }\n'
                "}"
            )
        },
        {"role": "user", "content": image_parts}
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=1000,
        )
        return {"GPT_Output": response.choices[0].message.content.strip()}
    except Exception as exc:
        return {"error": str(exc)}


def process_pdf(pdf_path: str | Path) -> Tuple[Dict[str, str], Dict]:
    images = extract_images_from_pdf(pdf_path)
    return call_gpt_vision_api(images), {}


def parse_gpt_output(form_data: Dict[str, str | None]) -> Dict:
    raw = (form_data.get("GPT_Output") or "").strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.endswith("```"):
        raw = raw[:-3]
    parsed = json.loads(raw)

    if "Occupants" in parsed and "E. Occupant Information" not in parsed:
        parsed["E. Occupant Information"] = parsed["Occupants"]
    if "Employment" in parsed and "Employment and Other Income:" not in parsed:
        parsed["Employment and Other Income:"] = parsed["Employment"]
    if "Vehicle" in parsed and "F. Vehicle Information:" not in parsed:
        parsed["F. Vehicle Information:"] = parsed["Vehicle"]

    return parsed

def write_flattened_to_template(data, template_path="templates/Tenant_Template.xlsx"):
    try:
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        # Property section
        ws["E3"] = data.get("Property Address", "")
        ws["E4"] = data.get("Move-in Date", "")
        ws["E5"] = data.get("Monthly Rent", "")

        # Representative
        ws["F10"] = data.get("Rep Name", "")
        ws["J9"] = data.get("Rep Phone", "")
        ws["J10"] = data.get("Rep Email", "")

        # Applicant
        ws["F14"] = data.get("FullName", "")
        ws["F15"] = data.get("Email", "")
        ws["F16"] = data.get("PhoneNumber", "")
        ws["F17"] = data.get("SSN", "")
        ws["F18"] = data.get("DriverLicenseNumber", "")
        ws["F19"] = data.get("DOB", "")
        ws["F20"] = calc_age(data.get("DOB", ""))  # Age
        ws["F21"] = data.get("No of Occupants", "")  # New line
        ws["F22"] = data.get("No of Children", "")
        ws["F23"] = data.get("Applicant's Current Address", "")
        ws["F24"] = data.get("Landlord or Property Manager's Name", "")
        ws["F25"] = data.get("Landlord Phone", "")
        ws["F27"] = data.get("Applicant's Current Employer", "")
        ws["F28"] = data.get("Employer Address", "")
        ws["F29"] = f"{data.get('Employment Verification Contact', '')} {data.get('Employer Phone', '')}".strip()
        ws["F30"] = data.get("Start Date", "")
        ws["F31"] = data.get("Gross Monthly Income", "")
        ws["F32"] = data.get("Position", "")

        vehicle_lines = [
            f"{t} {m} {mo} {y}".strip()
            for t, m, mo, y in zip(
                data.get("Vehicle Type", "").split(", "),
                data.get("Vehicle Make", "").split(", "),
                data.get("Vehicle Model", "").split(", "),
                data.get("Vehicle Year", "").split(", "),
            )
        ]
        ws["F34"] = "\n".join(vehicle_lines)
        ws["F34"].alignment = openpyxl.styles.Alignment(wrap_text=True)

        ws["F35"] = data.get("Vehicle Monthly Payment", "")  # fixed key

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        def generate_filename(address):
            cleaned = re.sub(r"[^\w\s]", "", str(address))
            words = cleaned.strip().split()
            word_part = "_".join(words[1:3]) if len(words) >= 3 else "_".join(words[:2]) if len(words) >= 2 else "tenant"
            return f"{word_part}_{datetime.now().strftime('%Y%m%d')}_app.xlsx"

        filename = generate_filename(data.get("Property Address", "tenant"))
        return output, filename

    except Exception as e:
        print("❌ Error in write_flattened_to_template:")
        traceback.print_exc()
        return None

    return {k: ("" if v is None else v) for k, v in flat.items()}


def parse_gpt_output(form_data):
    raw = form_data.get("GPT_Output", "").strip()

    # Remove markdown formatting if present
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.endswith("```"):
        raw = raw[:-3]

    try:
        parsed = json.loads(raw)

        # Patch for consistent keys expected by flatten_extracted_data
        if "Employment" in parsed and "Employment and Other Income:" not in parsed:
            parsed["Employment and Other Income:"] = parsed["Employment"]

        if "Vehicle" in parsed and "F. Vehicle Information:" not in parsed:
            parsed["F. Vehicle Information:"] = parsed["Vehicle"]

        if "Representation" in parsed and "C.Representation and Marketing" not in parsed:
            parsed["C.Representation and Marketing"] = parsed["Representation"]

        if "Occupants" in parsed and "E. Occupant Information" not in parsed:
            parsed["E. Occupant Information"] = parsed["Occupants"]

        if "Occupant Information" in parsed and "E. Occupant Information" not in parsed:
            parsed["E. Occupant Information"] = parsed["Occupant Information"]

        print("GPT Raw Output:", form_data["GPT_Output"])
        return parsed

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid GPT JSON string: {e}")
