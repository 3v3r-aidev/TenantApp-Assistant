import base64
import io
import json
from pathlib import Path
from typing import List, Dict, Tuple
import fitz  # PyMuPDF
from PIL import Image
import openai
import streamlit as st
from datetime import datetime


EXTRACTED_DATA_PATH = "Template_Data_Holder.xlsx"


def extract_images_from_pdf(pdf_path: str | Path) -> List[Image.Image]:
    images = []
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                pix = page.get_pixmap(dpi=300, colorspace=fitz.csRGB)
                images.append(Image.open(io.BytesIO(pix.tobytes("png"))))
    except Exception as e:
        print(f"❌ Failed to extract images: {e}")
    return images


def call_gpt_vision_api(images: List[Image.Image]) -> Dict[str, str]:
    try:
        openai.api_key = st.secrets["openai"]["OPENAI_API_KEY"]
    except Exception as key_err:
        return {"error": f"Missing OpenAI API key: {key_err}"}

    image_parts = []
    for img in images:
        try:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()
            image_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"}
            })
        except Exception as img_err:
            print(f"⚠️ Error encoding image: {img_err}")

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
                "- F. Vehicle Information (must return as a list with Monthly Payment per vehicle)\n"
                "- G. Animals (list if \"Will any animals be kept on the Property?\" is \"Yes\")\n"
                "- Applicant's Current Address (must be a nested object with Address, Phone:Day, Landlord Name)\n"
                "- Co-applicants: list all co-applicants with their Name and Relationship\n\n"
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
                '  "Co-applicants": [\n'
                '    {"Name": string | null, "Relationship": string | null}\n'
                '  ],\n'
                '  "Applicant\'s Current Address": {\n'
                '    "Address": string | null,\n'
                '    "Phone:Day": string | null,\n'
                '    "Landlord or Property Manager\'s Name": string | null,\n'
                '    "Rent": string | null\n'
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
                '  "F. Vehicle Information:": [\n'
                '    {\n'
                '      "Type": string | null,\n'
                '      "Year": string | null,\n'
                '      "Make": string | null,\n'
                '      "Model": string | null,\n'
                '      "Monthly Payment": string | null\n'
                '    }\n'
                '  ],\n'
                '  "G. Animals": [\n'
                '    {\n'
                '      "Type and Breed": string | null,\n'
                '      "Name": string | null,\n'
                '      "Color": string | null,\n'
                '      "Weight": string | null,\n'
                '      "Age in Yrs": string | null,\n'
                '      "Gender": string | null\n'
                '    }\n'
                '  ]\n'
                '}\n\n'
                "Instruction for G. Animals:If the field 'Will any animals (dogs, cats, birds, reptiles, fish, other types of animals) be kept on the Property?' has a checkbox values of Yes: "
                "'Go to the field, 'If yes, list all animals to be kept on the Property': Extract Type and Breed, Name, Color, Weight, Age in Yrs, and Gender."
                "Return as a structured list of dictionaries."
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
        if hasattr(response, "choices") and response.choices:
            return {"GPT_Output": response.choices[0].message.content.strip()}
        else:
            return {"error": "No GPT choices returned"}
    except Exception as exc:
        return {"error": str(exc)}

def extract_text_from_first_page(pdf_path: str | Path) -> str:
    try:
        with fitz.open(pdf_path) as doc:
            return doc[0].get_text().strip()
    except Exception:
        return ""

def detect_form_type(text: str, ocr_used: bool = False) -> str:
    if ocr_used:
        return "handwritten_form"
    if "05-15-24" in text or "07-08-22" in text:
        return "standard_form"
    elif "2-1-18" in text or "Declawed?" in text:
        return "handwritten_form"
    return "unknown"

def call_handwritten_prompt(images: List[Image.Image]) -> Dict[str, str]:
    # For now, reuse the same prompt as standard
    return call_gpt_vision_api(images)

def process_pdf(pdf_path: str | Path) -> Tuple[Dict[str, str], Dict]:
    images = extract_images_from_pdf(pdf_path)
    text = extract_text_from_first_page(pdf_path)

    form_type = detect_form_type(text)

    if form_type == "standard_form":
        return call_gpt_vision_api(images), {}
    elif form_type == "handwritten_form":
        return call_handwritten_prompt(images), {}
    else:
        return {"error": "Unsupported or unknown form type"}, {}

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
    if "Animals" in parsed and "G. Animals" not in parsed:
        parsed["G. Animals"] = parsed["Animals"]

    return parsed
    
def clean_vehicle_data(vehicles: List[Dict]) -> List[Dict]:
    """Filter out vehicle entries where all key fields are empty or whitespace."""
    cleaned = []
    for v in vehicles:
        if not isinstance(v, dict):
            continue
        if any(str(v.get(k, "") or "").strip() for k in ["Type", "Year", "Make", "Model", "Monthly Payment"]):
            cleaned.append(v)
    return cleaned


def normalize_date_string(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%m/%d/%Y")
    except Exception:
        try:
            date_obj = datetime.strptime(date_str, "%Y/%m/%d")
            return date_obj.strftime("%m/%d/%Y")
        except Exception:
            return date_str


def normalize_all_dates(data):
    def is_date_field(k): return any(d in k.lower() for d in ["date", "dob", "start", "move", "birth"])
    def normalize(obj):
        if isinstance(obj, dict):
            return {k: normalize_date_string(v) if is_date_field(k) else normalize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [normalize(i) for i in obj]
        return obj
    return normalize(data)

def flatten_extracted_data(data: Dict) -> Dict[str, str]:
    employment = data.get("Employment and Other Income:", {})
    employer_info = employment.get("Current Employer Details", {}) if isinstance(employment.get("Current Employer Details"), dict) else {}
    rep = data.get("C.Representation and Marketing", {})
    addr_block = data.get("Applicant's Current Address", {})

    address_str = addr_block.get("Address", "") if isinstance(addr_block, dict) else addr_block
    address_phone = addr_block.get("Phone:Day", "") if isinstance(addr_block, dict) else ""
    landlord_name = addr_block.get("Landlord or Property Manager's Name", "") if isinstance(addr_block, dict) else ""

    occupants = data.get("E. Occupant Information", [])
    children_count = 0
    if not isinstance(occupants, list):
        occupants = []
    for o in occupants:
        if isinstance(o, dict):
            relationship = str(o.get("Relationship", "") or "").strip().lower()
            if relationship in ("son", "daughter"):
                children_count += 1

    co_applicants = data.get("Co-applicants", [])
    co_applicant_count = 0
    if isinstance(co_applicants, list):
        co_applicant_count = sum(1 for person in co_applicants if person.get("Name"))
    total_occupants = 1 + co_applicant_count

    vehicles = data.get("F. Vehicle Information:", [])
    if isinstance(vehicles, dict):
        vehicles = [vehicles]
    elif not isinstance(vehicles, list):
        vehicles = []
    vehicles = clean_vehicle_data(vehicles)

    vehicle_types, vehicle_years, vehicle_makes, vehicle_models, vehicle_payments = [], [], [], [], []
    payment_floats = []

    for v in vehicles:
        type_ = str(v.get("Type", "") or "").strip()
        year = str(v.get("Year", "") or "").strip()
        make = str(v.get("Make", "") or "").strip()
        model = str(v.get("Model", "") or "").strip()
        payment = str(v.get("Monthly Payment", "") or "").strip()

        vehicle_types.append(type_)
        vehicle_years.append(year)
        vehicle_makes.append(make)
        vehicle_models.append(model)
        vehicle_payments.append(payment)

        try:
            payment_value = float(payment.replace("$", "").replace(",", ""))
            payment_floats.append(payment_value)
        except:
            pass

    total_vehicle_payment = f"{sum(payment_floats):.2f}" if payment_floats else ""

    # ---- Animals processing ----
    animals = data.get("G. Animals", [])
    if isinstance(animals, dict):
        animals = [animals]
    elif not isinstance(animals, list):
        animals = []

    cleaned_animals = []
    for a in animals:
        if not isinstance(a, dict):
            continue
        if any(str(a.get(k, "") or "").strip() for k in ["Type and Breed", "Name", "Color", "Weight", "Age in Yrs", "Gender"]):
            cleaned_animals.append(a)
    no_of_animals = len(cleaned_animals)

    # Format cleaned animals into multi-line summary for Excel (e.g., B13)
    animal_lines = []
    for a in cleaned_animals:
        parts = []
        for key in ["Type and Breed", "Name", "Color", "Weight", "Age in Yrs", "Gender"]:
            val = str(a.get(key, "")).strip()
            if val:
                parts.append(f"{key}: {val}")
        if parts:
            animal_lines.append(" | ".join(parts))
    animal_summary = "\n".join(animal_lines) if animal_lines else ""
    # ----------------------------

    flat = {
        "Property Address": data.get("Property Address", ""),
        "Move-in Date": data.get("Move-in Date", ""),
        "Monthly Rent": data.get("Monthly Rent", ""),
        "FullName": data.get("FullName", ""),
        "PhoneNumber": data.get("PhoneNumber", ""),
        "Email": data.get("Email", ""),
        "DOB": data.get("DOB", ""),
        "SSN": data.get("SSN", ""),
        "Co-applicants": co_applicants,
        "Applicant's Current Address": address_str,
        "Landlord Phone": address_phone,
        "Landlord or Property Manager's Name": landlord_name,
        "IDType": data.get("IDType", ""),
        "DriverLicenseNumber": data.get("DriverLicenseNumber", ""),
        "IDIssuer": data.get("IDIssuer", ""),
        "Nationality": data.get("Nationality", ""),
        "FormSource": data.get("FormSource", ""),
        "ApplicationDate": data.get("ApplicationDate", ""),
        "Rep Name": rep.get("Name", ""),
        "Rep Company": rep.get("Company", ""),
        "Rep Email": rep.get("E-mail", ""),
        "Rep Phone": rep.get("Phone Number", ""),
        "Applicant's Current Employer": employment.get("Applicant's Current Employer", ""),
        "Employment Verification Contact": employer_info.get("Employment Verification Contact", ""),
        "Employer Address": employer_info.get("Address", ""),
        "Employer Phone": employer_info.get("Phone", ""),
        "Employer Email": employer_info.get("E-mail", ""),
        "Position": employer_info.get("Position", ""),
        "Start Date": employer_info.get("Start Date", ""),
        "Gross Monthly Income": employer_info.get("Gross Monthly Income", ""),
        "Child Support": employment.get("Child Support", ""),
        "Vehicle Type": ", ".join(vehicle_types),
        "Vehicle Year": ", ".join(vehicle_years),
        "Vehicle Make": ", ".join(vehicle_makes),
        "Vehicle Model": ", ".join(vehicle_models),
        "Vehicle Monthly Payment": total_vehicle_payment,
        "No of Children": children_count,
        "No of Occupants": total_occupants,
        "No of Animals": no_of_animals,
        "G. Animals": cleaned_animals,
        "Animal Summary": animal_summary  # ✅ Now flattened and ready for writing to B13
    }

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

        if "Animals" in parsed and "G. Animals" not in parsed:
            parsed["G. Animals"] = parsed["Animals"]

        print("GPT Raw Output:", form_data["GPT_Output"])
        return parsed

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid GPT JSON string: {e}")
