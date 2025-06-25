import openai
import fitz  
import io
from PIL import Image
import json
import os
import base64
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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
                " You are a document parser. Extract structured data from tenant application forms and ID documents."
                " Return a JSON object with: Property Address, Move-in Date, FullName, DOB, SSN, Email, PhoneNumber, "
                " Applicant's Current Address, Landlord or Property Manager's Name, Phone:Day:"
                " DriverLicenseNumber, IDType, IDIssuer, Nationality, FormSource, ApplicationDate."
                " Under C.Represenation and Marketing, extract Name, Company, E-mail, Phone Number"
                " Under Employment and Other Income:, Applicant's Current Employer, Employment Verification Contact:, Phone, Employed to, Employed from,Gross Monthly Income, Position" 
                " Under F. Vehicle Information: Type, Year, Make, Model, Monthly Payment"
                " If a field is not found, return null. The result must be JSON and match the field names exactly."
            ),
        },
        {
            "role": "user",
            "content": image_parts
        },
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        return json.loads(content) if content.startswith('{') else {"GPT_Output": content}
    except Exception as e:
        return {"error": str(e)}


def process_pdf(pdf_path):
    images = extract_images_from_pdf(pdf_path)
    extracted_data = call_gpt_vision_api(images)
    return extracted_data, {}


def save_to_excel_appended(data_dict):
    """Append a new row to the Excel file without overwriting existing data."""
    new_df = pd.DataFrame([data_dict])
    if os.path.exists(EXTRACTED_DATA_PATH):
        existing_df = pd.read_excel(EXTRACTED_DATA_PATH)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df
    combined_df.to_excel(EXTRACTED_DATA_PATH, index=False)


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text_data = ""
    for page in doc:
        text_data += page.get_text()
    return text_data

def flatten_extracted_data(data):
    """Flattens nested tenant data into a single-level dictionary for Excel."""
    flat = {
        "Property Address": data.get("Property Address"),
        "Move-in Date": data.get("Move-in Date"),
        "FullName": data.get("FullName"),
        "DOB": data.get("DOB"),
        "SSN": data.get("SSN"),
        "Email": data.get("Email"),
        "PhoneNumber": data.get("PhoneNumber"),
        "Applicant's Current Address": data.get("Applicant's Current Address"),
        "Landlord or Property Manager's Name": data.get("Landlord or Property Manager's Name"),
        "Phone:Day:": data.get("Phone:Day"),
        "DriverLicenseNumber": data.get("DriverLicenseNumber"),
        "IDType": data.get("IDType"),
        "IDIssuer": data.get("IDIssuer"),
        "Nationality": data.get("Nationality"),

        # Employment Info
        "Applicant's Current Employer": data.get("Employment and Other Income:", {}).get("Applicant's Current Employer"),
        "Employment Verification Contact:": data.get("Employment and Other Income:", {}).get("Employment Verification Contact:"),
        "Phone": data.get("Employment and Other Income:", {}).get("Phone"),
        "Employed from": data.get("Employment and Other Income:", {}).get("Employed from"),
        "Employed to": data.get("Employment and Other Income:", {}).get("Employed to"),
        "Gross Monthly Income": data.get("Employment and Other Income:", {}).get("Gross Monthly Income"),
        "Position": data.get("Employment and Other Income:", {}).get("Position"),

        # Vehicle Info
        "Type": data.get("F. Vehicle Information:", {}).get("Type"),
        "Year": data.get("F. Vehicle Information:", {}).get("Year"),
        "Make": data.get("F. Vehicle Information:", {}).get("Make"),
        "Model": data.get("F. Vehicle Information:", {}).get("Model"),
        "Monthly Payment": data.get("F. Vehicle Information:", {}).get("Monthly Payment")
    }
    return flat

def parse_gpt_output(form_data):
    """
    Parses the GPT-4 JSON string from the form_data['GPT_Output'] key and returns a Python dict.
    Strips leading/trailing markdown backticks and safely loads JSON.
    """
    raw = form_data.get("GPT_Output", "").strip()

    # Remove markdown formatting if present
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.endswith("```"):
        raw = raw[:-3]

    try:
        parsed = json.loads(raw)
        return parsed
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid GPT JSON string: {e}")
