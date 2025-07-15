import openpyxl
import re
import traceback
from openpyxl import load_workbook
from datetime import datetime
from pathlib import Path
from io import BytesIO
from datetime import datetime, date


def calc_age(dob_str: str) -> str | int:
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

def normalize_date(date_str):
    if not date_str:
        return ""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue
    return date_str  # fallback to original if parsing fails

def write_flattened_to_template(data, template_path="templates/Tenant_Template.xlsx", summary_header=None):
    try:
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        # Property section
        property_address = data.get("Property Address", "")
        ws.oddHeader.left.text = property_address  # Left header
        ws["E3"] = property_address
        ws["E4"] = data.get("Move-in Date", "")
        ws["E5"] = str(data.get("Monthly Rent", "")).replace("$", "").strip()

        # Write to center header (line 3 only, if summary_header is passed)
        if summary_header:
            existing = ws.oddHeader.center.text or ""
            lines = existing.split("\n")[:2]
            lines.append(f"Date={summary_header}")
            ws.oddHeader.center.text = "\n".join(lines)

        # PropertyInfo lookup
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
        ws["F20"] = calc_age(data.get("DOB", ""))
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

        # Total vehicle monthly payment
        ws["F35"] = data.get("Vehicle Monthly Payment", "")

        # Save to buffer
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
        return None, None


def write_multiple_applicants_to_template(
    df,
    template_path="templates/Tenant_Template_Multiple.xlsx",
    summary_header: str | None = None,
):
    """
    Fill the multi-applicant template with rows from `df` (max 10 applicants).
    Optionally append `summary_header` (e.g. APP-637-2025-07-16-104533)
    as line-3 of the center page header.
    Returns: (BytesIO_output, generated_filename)  or  (None, None) on error
    """
    try:
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        # ── Left header (property address) ──
        first_row = df.iloc[0]
        property_address = first_row.get("Property Address", "")
        ws.oddHeader.left.text = property_address

        # ── Center header (keep lines 1-2, add line-3) ──
        if summary_header:
            existing = ws.oddHeader.center.text or ""
            lines = existing.split("\n")[:2]  # keep up to 2 existing lines
            lines.append(f"Date={summary_header}")
            ws.oddHeader.center.text = "\n".join(lines)

        # ── Top-level fields ──
        ws["E3"] = property_address
        ws["E4"] = normalize_date(first_row.get("Move-in Date", ""))
        ws["E5"] = str(first_row.get("Monthly Rent", "")).replace("$", "").strip()
        ws["F10"] = first_row.get("Rep Name", "")
        ws["J9"]  = first_row.get("Rep Phone", "")
        ws["J10"] = first_row.get("Rep Email", "")

        # Column starting letters for each applicant block (max 10)
        col_starts = ["F", "I", "L", "O", "R", "U", "X", "AA", "AD", "AG"]
        start_row = 14

        for idx, (_, row) in enumerate(df.iterrows()):
            if idx >= len(col_starts):
                break  # template supports max 10
            col = col_starts[idx]

            def write(offset: int, value):
                ws[f"{col}{start_row + offset}"] = value or ""

            write(0,  row.get("FullName"))
            write(1,  row.get("Email"))
            write(2,  row.get("PhoneNumber"))
            write(3,  row.get("SSN"))
            write(4,  row.get("DriverLicenseNumber"))
            write(5,  normalize_date(row.get("DOB", "")))
            write(6,  calc_age(row.get("DOB", "")))
            write(7,  str(row.get("No of Occupants", "")))
            write(8,  row.get("No of Children", ""))
            write(9,  row.get("Applicant's Current Address"))
            write(10, row.get("Landlord or Property Manager's Name"))
            write(11, row.get("Landlord Phone"))
            write(13, row.get("Applicant's Current Employer"))
            write(14, row.get("Employer Address"))
            write(15, f"{row.get('Employment Verification Contact', '')} {row.get('Employer Phone', '')}".strip())
            write(16, normalize_date(row.get("Start Date", "")))
            write(17, row.get("Gross Monthly Income"))
            write(19, row.get("Position"))

            # ── Vehicle details (multi-line) ──
            v_types  = str(row.get("Vehicle Type", "")  or "").split(", ")
            v_makes  = str(row.get("Vehicle Make", "")  or "").split(", ")
            v_models = str(row.get("Vehicle Model", "") or "").split(", ")
            v_years  = str(row.get("Vehicle Year", "")  or "").split(", ")

            vehicle_lines = [
                f"{t} {m} {mo} {y}".strip()
                for t, m, mo, y in zip(v_types, v_makes, v_models, v_years)
                if any([t.strip(), m.strip(), mo.strip(), y.strip()])
            ]

            target = f"{col}{start_row + 20}"
            if vehicle_lines:
                ws[target] = "\n".join(vehicle_lines)
                ws[target].alignment = openpyxl.styles.Alignment(wrap_text=True)
            else:
                ws[target] = ""

            # Total vehicle payment
            write(21, row.get("Vehicle Monthly Payment"))

        # ── Save workbook to BytesIO ──
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Filename generator
        cleaned = re.sub(r"[^\w\s]", "", property_address)
        words = cleaned.strip().split()
        word_part = "_".join(words[1:3]) if len(words) >= 3 else "_".join(words[:2]) if len(words) >= 2 else "tenant"
        filename = f"{word_part}_{datetime.now().strftime('%Y%m%d')}_app.xlsx".lower()

        return output, filename

    except Exception as e:
        print("❌ Error in write_multiple_applicants_to_template:")
        traceback.print_exc()
        return None, None  # always return tuple


def write_to_summary_template(
    flat_data: dict,
    output_path: str | Path,
    summary_template_path: str | Path = "templates/App_Summary_Template.xlsx",
) -> None:
    wb = load_workbook(summary_template_path)
    ws = wb.active

    # Counter logic with forced test-mode = 636
    meta_ws = wb["_Meta"] if "_Meta" in wb.sheetnames else wb.create_sheet("_Meta")
    if "_Meta" not in wb.sheetnames:
        wb.move_sheet(meta_ws, offset=len(wb.sheetnames))
        meta_ws.sheet_state = "hidden"
        meta_ws["A1"] = "counter"

    TEST_MODE = True
    TEST_START_VALUE = 636
    counter = TEST_START_VALUE if TEST_MODE else (meta_ws["B1"].value or TEST_START_VALUE) + 1
    meta_ws["B1"] = counter

    ws["B1"] = datetime.now().strftime(f"APP-{counter}-%Y-%m-%d-%H%M%S")

    # Monthly Rent (denominator)
    rent_str = flat_data.get("Monthly Rent", "").replace("$", "").replace(",", "").strip()
    try:
        rent = float(rent_str) if rent_str else 0
    except ValueError:
        rent = 0

    # Gross Monthly Income: Primary
    gross_str = flat_data.get("Gross Monthly Income", "").replace("$", "").replace(",", "").strip()
    try:
        gross = float(gross_str) if gross_str else 0
    except ValueError:
        gross = 0

    # Net Income = sum of all applicant gross income
    co_applicants = flat_data.get("Co-applicants", [])
    co_gross_total = 0
    for applicant in co_applicants:
        value = str(applicant.get("Gross Monthly Income", "")).replace("$", "").replace(",", "").strip()
        try:
            co_gross_total += float(value) if value else 0
        except:
            continue
    net_total = gross + co_gross_total

    gross_ratio = f"{gross / rent:.2f}" if rent > 0 else ""
    net_ratio = f"{net_total / rent:.2f}" if rent > 0 else ""

    # Field-to-cell map 
    write_map = {
        "Address": ("B2", flat_data.get("Property Address", "")),
        "Rent": ("B3", flat_data.get("Monthly Rent", "")),
        "Move-in date": ("B4", flat_data.get("Move-in Date", "")),
        "Application Fee": ("B5", flat_data.get("Application Fee", "")),
        "Gross/Net Ratio": ("B6", f"{gross_ratio}/{net_ratio}"),
        "No Of Occupants": ("B7", flat_data.get("No of Occupants", "")),
        "Current Rent": ("B8", flat_data.get("Rent", "")),
        "Employment": ("B9", flat_data.get("Applicant's Current Employer", "")),

        # ✅ Cars and Pets now use fully detailed strings from flattened data
        "Cars": ("B12", flat_data.get("Vehicle Details", flat_data.get("Vehicle Make", ""))),
        "Pets": ("B13", flat_data.get("Animal Details", flat_data.get("No of Animals", ""))),
    }

    for _, (cell, value) in write_map.items():
        ws[cell] = value

    wb.save(output_path)

