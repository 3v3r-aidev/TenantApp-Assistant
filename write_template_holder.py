import os
import pandas as pd
import openpyxl
from datetime import datetime
from io import BytesIO
import re


def append_to_template_holder(data_dict, holder_path="templates/Template_Data_Holder.xlsx"):
    expected_columns = [
        "Property Address", "Move-in Date", "FullName", "PhoneNumber", "Email", "DOB", "SSN",
        "Applicant's Current Address", "Landlord or Property Manager's Name", "Phone:Day:",
        "Applicant's Current Employer", "Employment Verification Contact:", "Position",
        "Employed from", "Employed to", "Gross Monthly Income", "Type", "Year", "Make", "Model",
        "Monthly Payment", "IDType", "DriverLicenseNumber", "IDIssuer", "Nationality"
    ]

    if os.path.exists(holder_path):
        df_existing = pd.read_excel(holder_path)
    else:
        df_existing = pd.DataFrame(columns=expected_columns)

    df_new = pd.DataFrame([data_dict])
    df_new = df_new.reindex(columns=expected_columns, fill_value=None)
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined.to_excel(holder_path, index=False, engine='openpyxl')
    print(f"Appended to {holder_path}")


def generate_output_filename(property_address, prefix="Tenant"):
    date_str = datetime.now().strftime("%Y-%m-%d")
    words = property_address.split()
    suffix = f"{words[1]}_{words[2]}" if len(words) >= 3 else words[1] if len(words) >= 2 else "Unknown"
    return f"{prefix}_{date_str}_{suffix}.xlsx"


def write_flattened_to_template(data, template_path="templates/Tenant_Template.xlsx"):
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active

    ws["E3"] = data.get("Property Address")
    ws["E4"] = data.get("Move-in Date")

    ws["F14"] = data.get("FullName")
    ws["F15"] = data.get("Email")
    ws["F16"] = data.get("PhoneNumber")
    ws["F17"] = data.get("SSN")
    ws["F18"] = data.get("DriverLicenseNumber")
    ws["F19"] = data.get("DOB")
    ws["F23"] = data.get("Applicant's Current Address")
    ws["F24"] = data.get("Landlord or Property Manager's Name")
    ws["F25"] = data.get("Phone:Day:")
    ws["F27"] = data.get("Applicant's Current Employer")
    ws["F29"] = data.get("Employment Verification Contact:")
    ws["F30"] = f"{data.get('Employed from')} to {data.get('Employed to')}"
    ws["F31"] = data.get("Gross Monthly Income")
    ws["F32"] = data.get("Position")
    ws["F33"] = f"{data.get('Make')} {data.get('Model')} {data.get('Year')}"
    ws["F34"] = data.get("Monthly Payment")

   
def write_multiple_applicants_to_template(df, template_path="templates/Tenant_Template.xlsx"):
    if len(df) >= 3:
        template_path = "templates/Tenant_Temp_Multiple.xlsx"

    wb = openpyxl.load_workbook(template_path)
    ws = wb.active

    col_starts = ["F", "I", "L", "O", "R", "U", "X", "AA", "AD", "AG"]
    start_row = 14

    first_row = df.iloc[0]
    ws["E3"] = first_row.get("Property Address")
    ws["E4"] = first_row.get("Move-in Date")

    for idx, (_, row) in enumerate(df.iterrows()):
        if idx >= len(col_starts):
            break
        col = col_starts[idx]

        def write(row_offset, value):
            ws[f"{col}{start_row + row_offset}"] = value

        write(0, row.get("FullName"))
        write(1, row.get("Email"))
        write(2, row.get("PhoneNumber"))
        write(3, row.get("SSN"))
        write(4, row.get("DriverLicenseNumber"))
        write(5, row.get("DOB"))
        write(9, row.get("Applicant's Current Address"))
        write(10, row.get("Landlord or Property Manager's Name"))
        write(11, row.get("Phone:Day:"))
        write(13, row.get("Applicant's Current Employer"))
        write(15, row.get("Employment Verification Contact:"))
        write(16, f"{row.get('Employed from')} to {row.get('Employed to')}")
        write(18, row.get("Gross Monthly Income"))
        write(19, row.get("Position"))
        write(20, f"{row.get('Make')} {row.get('Model')} {row.get('Year')}")
        write(21, row.get("Monthly Payment"))

    # ✅ MEMORY-ONLY: Save to in-memory bytes buffer
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # ✅ Filename logic: use 2nd and 3rd words of address
    def generate_filename(address):
        cleaned = re.sub(r'[^\w\s]', '', str(address))
        words = cleaned.strip().split()
        word_part = "_".join(words[1:3]) if len(words) >= 3 else "_".join(words[:2]) if len(words) >= 2 else "tenant"
        return f"{word_part}_{datetime.now().strftime('%Y%m%d')}_app.xlsx"

    filename = generate_filename(first_row.get("Property Address"))
    return output, filename



