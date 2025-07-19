import os
import pandas as pd
import openpyxl
from datetime import datetime
from io import BytesIO
import re

def write_to_template_holder(data_dict, holder_path="templates/Template_Data_Holder.xlsx"):
    if not isinstance(data_dict, dict) or not data_dict:
        raise ValueError("No applicant data was provided. Please make sure all required fields are filled before saving.")

    expected_columns = [
        "Property Address", "Move-in Date", "FullName", "PhoneNumber", "Email", "DOB", "SSN",
        "Applicant's Current Address", "Landlord Phone", "Landlord or Property Manager's Name", "Rent", "No of Children", "No of Occupants",
        "IDType", "DriverLicenseNumber", "IDIssuer", "Nationality", "FormSource", "ApplicationDate",
        "Rep Name", "Rep Company", "Rep Email", "Rep Phone",
        "Applicant's Current Employer", "Employment Verification Contact", "Employer Address",
        "Employer Phone", "Employer Email", "Position", "Start Date", "Gross Monthly Income",
        "Child Support", "Vehicle Type", "Vehicle Year", "Vehicle Make", "Vehicle Model", "Vehicle Monthly Payment", "No of Animals", "G. Animals", "Animal Summary"
    ]

    df_new = pd.DataFrame([data_dict])
    df_new = df_new.reindex(columns=expected_columns, fill_value=None)
    df_new = df_new.fillna("").applymap(lambda x: str(x).strip() if isinstance(x, str) else x)  # Clean all cells

    try:
        df_new.to_excel(holder_path, index=False, engine='openpyxl')
        print(f"✅ Replaced contents of {holder_path}")
    except Exception as e:
        print(f"❌ Failed to write to template holder: {e}")
        raise
