import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from datetime import datetime

# Ordered fields matching Excel row 4 to 36
field_order = [
    "Form Name", "Form Email", "Form Cell Phone", "Form SSN", "Form DL No.",
    "Form DOB", "Form Age", "Form Occupants", "Form Children", "Form Address",
    "Landlord Name", "Landlord Phone", "Current Address Info", "Employer",
    "Employer Address", "Supervisor Name/Phone", "Employment Date/Years",
    "Gross Monthly Income", "Other Income", "Position", "Car Info",
    "Monthly Car Payment", "Commute Time"
]

def get_column_pair(index):
    """Returns Excel column letters for left/right cell pair (F/G, I/J, etc.)."""
    start_col = 6 + index * 3  # F = col 6, I = 9, etc.
    return get_column_letter(start_col), get_column_letter(start_col + 1)

def write_to_excel_template(data_file, template_file, output_file):
    df = pd.read_excel(data_file)

    if df.empty:
        raise ValueError("❌ No data found in the input file.")

    if len(df) > 10:
        raise ValueError("❌ Cannot write more than 10 applicants in one template.")

    wb = load_workbook(template_file)
    ws = wb.active

    # Write global property fields from first applicant
    ws["E3"] = df.iloc[0].get("Property Address", "")
    ws["E4"] = df.iloc[0].get("Move-in Date", "")

    for idx, row in df.iterrows():
        col1, col2 = get_column_pair(idx)
        print(f"📥 Writing Applicant {idx + 1} to columns {col1}/{col2}")
        for i, field in enumerate(field_order):
            cell_row = 4 + i
            value = row.get(field, "")
            ws[f"{col1}{cell_row}"] = value

    wb.save(output_file)
    print(f"✅ Excel template updated: {output_file}")
