import openpyxl
import re
import traceback
from io import BytesIO
from datetime import datetime, date

def calc_age(dob_str: str) -> str | int:
    """Return age in years or '' if invalid/blank."""
    if not dob_str:
        return ""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            dob = datetime.strptime(dob_str, fmt).date()
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except ValueError:
            continue
    return "Invalid DOB"

def normalize_date(date_str: str) -> str:
    """Normalize date to MM/DD/YYYY regardless of separator."""
    if not date_str or not isinstance(date_str, str):
        return ""
    date_str = date_str.replace("-", "/").replace(".", "/").strip()
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%m/%d/%Y")
        except ValueError:
            continue
    return date_str  # fallback to original if no format matches

def lookup_property_info(address: str, reference_file="PropertyInfo.xlsx"):
    try:
        if not address:
            return None, None

        wb_info = openpyxl.load_workbook(reference_file, data_only=True)
        ws_info = wb_info.active

        address_prefix = " ".join(address.strip().lower().split()[:3])

        for row in ws_info.iter_rows(min_row=2):
            c_val = str(row[2].value).strip().lower() if row[2].value else ""
            c_prefix = " ".join(c_val.split()[:3])
            if address_prefix == c_prefix:
                p_number = row[1].value  # Column B
                sqft = row[3].value      # Column D
                return p_number, sqft
        return None, None
    except Exception as e:
        print("❌ Error in lookup_property_info:", e)
        return None, None

def write_flattened_to_template(data, template_path="templates/Tenant_Template.xlsx"):
    try:
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        # Property section
        property_address = data.get("Property Address", "")
        ws.oddHeader.left.text = property_address  # Write property address to page header
        ws["E3"] = property_address
        ws["E4"] = data.get("Move-in Date", "")
        ws["E5"] = str(data.get("Monthly Rent", "")).replace("$", "").strip()

        # PropertyInfo lookup and write to G3 and G7
        p_number, sqft = lookup_property_info(property_address)
        if p_number:
            ws["G3"] = p_number
        if sqft:
            ws["G7"] = sqft

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
        ws["F21"] = str(data.get("No of Occupants", ""))
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

        # Multiline vehicle info
        vehicle_types = str(data.get("Vehicle Type", "") or "").split(", ")
        vehicle_makes = str(data.get("Vehicle Make", "") or "").split(", ")
        vehicle_models = str(data.get("Vehicle Model", "") or "").split(", ")
        vehicle_years = str(data.get("Vehicle Year", "") or "").split(", ")

        vehicle_lines = [
            f"{t} {m} {mo} {y}".strip()
            for t, m, mo, y in zip(vehicle_types, vehicle_makes, vehicle_models, vehicle_years)
            if any([t.strip(), m.strip(), mo.strip(), y.strip()])
        ]

        if vehicle_lines:
            ws["F34"] = "\n".join(vehicle_lines)
            ws["F34"].alignment = openpyxl.styles.Alignment(wrap_text=True)
        else:
            ws["F34"] = ""

        # Total monthly vehicle payment
        ws["F35"] = data.get("Vehicle Monthly Payment", "")

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        def generate_filename(address):
            cleaned = re.sub(r"[^\w\s]", "", str(address))
            words = cleaned.strip().split()
            word_part = "_".join(words[1:3]) if len(words) >= 3 else "_".join(words[:2]) if len(words) >= 2 else "tenant"
            return f"{word_part}_{datetime.now().strftime('%Y%m%d')}_app.xlsx"

        filename = generate_filename(property_address)
        return output, filename

    except Exception as e:
        print("❌ Error in write_flattened_to_template:")
        traceback.print_exc()
        return None
