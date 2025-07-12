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

def write_flattened_to_template(data, template_path="templates/Tenant_Template.xlsx"):
    try:
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        # Property section
        ws["E3"] = data.get("Property Address", "")
        ws["E4"] = normalize_date(data.get("Move-in Date", ""))
        ws["E5"] = str(data.get("Monthly Rent", "")).replace("$", "").strip()

        # Representative
        ws["F10"] = data.get("Rep Name", "")
        ws["J9"] = data.get("Rep Phone", "")
        ws["J10"] = data.get("Rep Email", "")

        # Applicant
        ws["F14"] = data.get("FullName", "")
        ws["F15"] = data.get("Email", "")
        ws["F16"] = data.get("PhoneNumber", "")
        ws["F17"] = data.get("SSN", "")
        ws["F21"] = data.get("No of Occupants", "")
        ws["F18"] = data.get("DriverLicenseNumber", "")
        ws["F19"] = normalize_date(data.get("DOB", ""))
        ws["F20"] = calc_age(data.get("DOB", ""))  # Age
        ws["F21"] = str(data.get("No of Occupants", ""))
        ws["F22"] = data.get("No of Children", "")
        ws["F23"] = data.get("Applicant's Current Address", "")
        ws["F24"] = data.get("Landlord or Property Manager's Name", "")
        ws["F25"] = data.get("Landlord Phone", "")
        ws["F27"] = data.get("Applicant's Current Employer", "")
        ws["F28"] = data.get("Employer Address", "")
        ws["F29"] = f"{data.get('Employment Verification Contact', '')} {data.get('Employer Phone', '')}".strip()
        ws["F30"] = normalize_date(data.get("Start Date", ""))
        ws["F31"] = data.get("Gross Monthly Income", "")
        ws["F32"] = data.get("Position", "")

        # Safe vehicle parsing and formatting
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

        ws["F35"] = data.get("Vehicle Monthly Payment", "")

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

def write_multiple_applicants_to_template(df, template_path="templates/Tenant_Template_Multiple.xlsx"):
    try:
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        col_starts = ["F", "I", "L", "O", "R", "U", "X", "AA", "AD", "AG"]
        start_row = 14

        first_row = df.iloc[0]
        ws["E3"] = first_row.get("Property Address", "")
        ws["E4"] = normalize_date(first_row.get("Move-in Date", ""))
        ws["E5"] = str(first_row.get("Monthly Rent", "")).replace("$", "").strip()
        ws["F10"] = first_row.get("Rep Name", "")
        ws["J9"] = first_row.get("Rep Phone", "")
        ws["J10"] = first_row.get("Rep Email", "")

        for idx, (_, row) in enumerate(df.iterrows()):
            if idx >= len(col_starts):
                break
            col = col_starts[idx]

            def write(offset, value):
                ws[f"{col}{start_row + offset}"] = value or ""

            write(0, row.get("FullName"))
            write(1, row.get("Email"))
            write(2, row.get("PhoneNumber"))
            write(3, row.get("SSN"))
            write(4, row.get("DriverLicenseNumber"))
            write(5, normalize_date(row.get("DOB", "")))
            write(6, calc_age(row.get("DOB", "")))  # Age
            write(7, str(row.get("No of Occupants", "")))
            write(8, row.get("No of Children", ""))
            write(9, row.get("Applicant's Current Address"))
            write(10, row.get("Landlord or Property Manager's Name"))
            write(11, row.get("Landlord Phone"))
            write(13, row.get("Applicant's Current Employer"))
            write(14, row.get("Employer Address"))
            write(15, f"{row.get('Employment Verification Contact', '')} {row.get('Employer Phone', '')}".strip())
            write(16, normalize_date(row.get("Start Date", "")))
            write(17, row.get("Gross Monthly Income"))
            write(19, row.get("Position"))

            # Safe vehicle parsing and filtering
            vehicle_types = str(row.get("Vehicle Type", "") or "").split(", ")
            vehicle_makes = str(row.get("Vehicle Make", "") or "").split(", ")
            vehicle_models = str(row.get("Vehicle Model", "") or "").split(", ")
            vehicle_years = str(row.get("Vehicle Year", "") or "").split(", ")

            vehicle_lines = [
                f"{t} {m} {mo} {y}".strip()
                for t, m, mo, y in zip(vehicle_types, vehicle_makes, vehicle_models, vehicle_years)
                if any([t.strip(), m.strip(), mo.strip(), y.strip()])
            ]

            if vehicle_lines:
                ws[f"{col}{start_row + 20}"] = "\n".join(vehicle_lines)
                ws[f"{col}{start_row + 20}"].alignment = openpyxl.styles.Alignment(wrap_text=True)

            write(21, row.get("Vehicle Monthly Payment"))

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        def generate_filename(address):
            cleaned = re.sub(r"[^\w\s]", "", str(address))
            words = cleaned.strip().split()
            word_part = "_".join(words[1:3]) if len(words) >= 3 else "_".join(words[:2]) if len(words) >= 2 else "tenant"
            return f"{word_part}_{datetime.now().strftime('%Y%m%d')}_app.xlsx"

        filename = generate_filename(first_row.get("Property Address", "tenant"))
        return output, filename

    except Exception as e:
        print("❌ Error in write_multiple_applicants_to_template:")
        traceback.print_exc()
        return None
