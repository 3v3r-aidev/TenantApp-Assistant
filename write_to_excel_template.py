import openpyxl
import re
from io import BytesIO
from datetime import datetime
from openpyxl.utils import get_column_letter
import pandas as pd


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
        ws["J9"]  = data.get("Rep Phone", "")
        ws["J10"] = data.get("Rep Email", "")

        # Applicant section
        ws["F14"] = data.get("FullName", "")
        ws["F15"] = data.get("Email", "")
        ws["F16"] = data.get("PhoneNumber", "")
        ws["F17"] = data.get("SSN", "")
        ws["F18"] = data.get("DriverLicenseNumber", "")
        ws["F19"] = data.get("DOB", "")
        ws["F23"] = data.get("Applicant's Current Address", "")
        ws["F24"] = data.get("Landlord or Property Manager's Name", "")
        ws["F25"] = data.get("Landlord Phone", "")
        ws["F27"] = data.get("Applicant's Current Employer","")
        ws["F28"] = data.get("Employer Address", "")
        ws["F29"] = f"{data.get('Employment Verification Contact', '')} {data.get('Employer Phone', '')}".strip()
        ws["F30"] = data.get("Start Date", "")
        ws["F31"] = data.get("Gross Monthly Income", "")
        ws["F32"] = data.get("Position", "")
        ws["F33"] = f"{data.get('Make', '')} {data.get('Model', '')} {data.get('Year', '')}".strip()
        ws["F34"] = data.get("Monthly Payment", "")

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        def generate_filename(address):
            cleaned = re.sub(r'[^\w\s]', '', str(address))
            words = cleaned.strip().split()
            word_part = "_".join(words[1:3]) if len(words) >= 3 else "_".join(words[:2]) if len(words) >= 2 else "tenant"
            return f"{word_part}_{datetime.now().strftime('%Y%m%d')}_app.xlsx"

        filename = generate_filename(data.get("Property Address", "tenant"))
        return output, filename

    except Exception as e:
        print(f"❌ Error in write_flattened_to_template: {e}")
        return None


def write_multiple_applicants_to_template(df, template_path="templates/Tenant_Temp_Multiple.xlsx"):
    try:
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        col_starts = ["F", "I", "L", "O", "R", "U", "X", "AA", "AD", "AG"]
        start_row = 14

        first_row = df.iloc[0]
        ws["E3"] = first_row.get("Property Address", "")
        ws["E4"] = first_row.get("Move-in Date", "")
        ws["E5"] = first_row.get("Monthly Rent", "")

        # Representative details (added)
        ws["F10"] = first_row.get("Rep Name", "")
        ws["J9"]  = first_row.get("Rep Phone", "")
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
            write(5, row.get("DOB"))
            write(9, row.get("Applicant's Current Address"))
            write(10, row.get("Landlord or Property Manager's Name"))
            write(11, row.get("Landlord Phone"))
            write(13, row.get("Applicant's Current Employer"))   
            write(14, row.get("Employer Address"))
            write(15, f"{row.get("Employment Verification Contact", '')} {row.get("Employer Phone")}".strip())
            write(16, row.get("Start Date"))
            write(17, row.get("Gross Monthly Income"))
            write(19, row.get("Position"))
            write(20, f"{row.get('Make', '')} {row.get('Model', '')} {row.get('Year', '')}".strip())
            write(21, row.get("Monthly Payment"))

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        def generate_filename(address):
            cleaned = re.sub(r'[^\w\s]', '', str(address))
            words = cleaned.strip().split()
            word_part = "_".join(words[1:3]) if len(words) >= 3 else "_".join(words[:2]) if len(words) >= 2 else "tenant"
            return f"{word_part}_{datetime.now().strftime('%Y%m%d')}_app.xlsx"

        filename = generate_filename(first_row.get("Property Address", "tenant"))
        return output, filename

    except Exception as e:
        print(f"❌ Error in write_multiple_applicants_to_template: {e}")
        return None
