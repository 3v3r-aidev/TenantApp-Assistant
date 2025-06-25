import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

# Ordered fields to match row 4–36
field_order = [
    "Form Name", "Form Email", "Form Cell Phone", "Form SSN", "Form DL No.",
    "Form DOB", "Form Age", "Form Occupants", "Form Children", "Form Address",
    "Landlord Name", "Landlord Phone", "Current Address Info", "Employer",
    "Employer Address", "Supervisor Name/Phone", "Employment Date/Years",
    "Gross Monthly Income", "Other Income", "Position", "Car Info",
    "Monthly Car Payment", "Commute Time"
]

# Compute which column pair to use for each applicant
def get_column_pair(index):
    start_col = 6 + index * 3  # F=6, I=9, L=12, etc.
    return get_column_letter(start_col), get_column_letter(start_col + 1)

# Main write function
def write_to_excel_template(data_file, template_file, output_file):
    df = pd.read_excel(data_file)
    wb = load_workbook(template_file)
    ws = wb.active

    # Write global header values from the first applicant only
    if not df.empty:
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
    print(f"✅ Data written to: {output_file}")
