import openai
import base64
import io
import streamlit as st
from typing import Tuple, Dict, List
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
from extract_tenant_data import extract_images_from_pdf, call_gpt_vision_api

# === Handwritten Form GPT Prompt Wrapper ===
def call_handwritten_prompt(images: List[Image.Image]) -> Dict[str, str]:
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
                "Extract structured tenant application data and return a JSON object using the schema below. "
                "This form is a handwritten TXR-2003 (2-1-18) residential lease application. "
                "You must interpret handwriting accurately and include all fields even if they appear blank. Do NOT add any explanations.\n\n"
                "**Focus areas to extract:**\n"
                "- Property Address, Move-in Date, Monthly Rent, Security Deposit\n"
                "- Applicant Info: Full Name, Email, Phone, SSN, DOB, DL No., Issuer, Nationality\n"
                "- Co-Applicants and Occupants: Name, Relationship, Age, DOB\n"
                "- Current Address block (with Phone:Day, Landlord Name, Rent)\n"
                "- Employment section (Employer name, Supervisor, Contact, Position, Start Date, Income)\n"
                "- Previous Employment (if listed)\n"
                "- Vehicle Information: list of vehicles with Type, Year, Make, Model, Monthly Payment\n"
                "- Animal Information: Extract only if 'Will any pets...?' is checked Yes. List Type, Name, Color, Weight, Age, Gender\n"
                "- C. Representation and Marketing (Agent name, email, phone)\n"
                "- Application Date (signature date on last page)\n\n"
                "Return in this JSON schema:\n"
                "{\n"
                '  "Property Address": string | null,\n'
                '  "Move-in Date": string | null,\n'
                '  "Monthly Rent": string | null,\n'
                '  "FullName": string | null,\n'
                '  "PhoneNumber": string | null,\n'
                '  "Email": string | null,\n'
                '  "DOB": string | null,\n'
                '  "SSN": string | null,\n'
                '  "Co-applicants": [ {"Name": string | null, "Relationship": string | null} ],\n'
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
                '  "FormSource": "TXR-2003 (2-1-18)",\n'
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
                '    "Child Support": null\n'
                '  },\n'
                '  "E. Occupant Information": [ {"Name": string | null, "Relationship": string | null, "DOB": string | null} ],\n'
                '  "F. Vehicle Information:": [ {"Type": string | null, "Year": string | null, "Make": string | null, "Model": string | null, "Monthly Payment": string | null} ],\n'
                '  "G. Animals": [ {"Type and Breed": string | null, "Name": string | null, "Color": string | null, "Weight": string | null, "Age in Yrs": string | null, "Gender": string | null} ]\n'
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
    except Exception as e:
        return {"error": str(e)}

# === Other Utilities ===

def extract_text_from_first_page(pdf_path: Path) -> str:
    try:
        with fitz.open(pdf_path) as doc:
            return doc[0].get_text().strip()
    except:
        return ""

def detect_form_type(text: str, ocr_used: bool = False) -> str:
    if ocr_used:
        return "handwritten_form"
    if "05-15-24" in text or "07-08-22" in text:
        return "standard_form"
    elif "2-1-18" in text or "Declawed?" in text:
        return "handwritten_form"
    return "unknown"

def extract_standard_form(images: List[Image.Image]) -> Dict[str, str]:
    return call_gpt_vision_api(images)

def extract_handwritten_form(images: List[Image.Image]) -> Dict[str, str]:
    return call_handwritten_prompt(images)

def extract_data_by_form_type(pdf_path: Path) -> Tuple[Dict[str, str], Dict]:
    images = extract_images_from_pdf(pdf_path)
    text = extract_text_from_first_page(pdf_path)

    form_type = detect_form_type(text)

    if form_type == "standard_form":
        return extract_standard_form(images), {}
    elif form_type == "handwritten_form":
        return extract_handwritten_form(images), {}
    else:
        return {"error": "Unsupported or unknown form type"}, {}
