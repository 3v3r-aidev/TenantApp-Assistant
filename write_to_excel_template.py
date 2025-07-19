import openpyxl
import re
import traceback
from openpyxl import load_workbook
from datetime import datetime
from pathlib import Path
from io import BytesIO
from datetime import datetime, date
import pandas as pd
from openpyxl.styles import Alignment


def calc_age(dob_str: str) -> str | int:
    if not dob_str:
        return ""
    
    try:
        dob_str = str(dob_str).strip()
    except:
        return "Invalid DOB"

    # Check if it's an Excel serial date (pure digits, float-like)
    if re.match(r"^\d+(\.0+)?$", dob_str):
        try:
            dob = datetime(1899, 12, 30) + pd.to_timedelta(float(dob_str), unit="D")
            dob = dob.date()
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except:
            return "Invalid DOB"

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

def normalize_date_string(date_str):
    if not isinstance(date_str, str):
        return date_str
    clean = re.sub(r"[-.]", "/", date_str.strip())
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%Y/%d/%m"):
        try:
            return datetime.strptime(clean, fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue
    return date_str

def normalize_all_dates(data):
    def is_date_field(k): return any(d in k.lower() for d in ["date", "dob", "start", "move", "birth"])
    def normalize(obj):
        if isinstance(obj, dict):
            return {k: normalize_date_string(v) if is_date_field(k) else normalize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [normalize(i) for i in obj]
        return obj
    return normalize(data)


# ───────────────────────────────────────────────────────────────────────────────
# 1. write_flattened_to_template  (adds strict input-type guard)
# ───────────────────────────────────────────────────────────────────────────────
def write_flattened_to_template(
    data,
    template_path="templates/Tenant_Template.xlsx",
    summary_header=None,
):
    try:
        data = normalize_all_dates(data)
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        # ── Property Info ─────────────────────────────
        property_address = str(data.get("Property Address", "") or "").strip()

        # Initialize left header if missing
        if ws.oddHeader.left is None:
            ws.oddHeader.left = openpyxl.worksheet.header_footer.HeaderFooterItem()
        ws.oddHeader.left.text = property_address

        # Initialize center header if summary_header is used
        if summary_header:
            if ws.oddHeader.center is None:
                ws.oddHeader.center = openpyxl.worksheet.header_footer.HeaderFooterItem()
            existing = ws.oddHeader.center.text or ""
            lines = existing.split("\n")
            new_line = f"Date={summary_header}"
            if len(lines) >= 3:
                lines[2] = new_line
            else:
                lines += [""] * (2 - len(lines)) + [new_line]
            ws.oddHeader.center.text = "\n".join(lines)

        ws["E3"] = property_address
        ws["E4"] = data.get("Move-in Date", "")
        ws["E5"] = str(data.get("Monthly Rent", "")).replace("$", "").strip()

        
        if summary_header:
            existing = ws.oddHeader.center.text or ""
            lines = existing.split("\n")
            new_line = f"Date={summary_header}"
            if len(lines) >= 3:
                lines[2] = new_line
            else:
                lines += [""] * (2 - len(lines)) + [new_line]
            ws.oddHeader.center.text = "\n".join(lines)

        # ── Lookup PropertyInfo ─────────────────────────
        try:
            prop_df = pd.read_excel("PropertyInfo.xlsx", header=None, dtype=str)
            addr_prefix = " ".join(property_address.strip().lower().split()[:3])
            mask = prop_df[2].fillna("").str.lower().apply(
                lambda x: " ".join(x.split()[:3])
            ) == addr_prefix
            match = prop_df[mask]
            if not match.empty:
                ws["G3"] = match.iloc[0, 1]
                ws["G7"] = match.iloc[0, 3]
        except Exception as e:
            print(f"Warning: Failed lookup – {e}")

        # ── Representative & Applicant Fields ─────────
        ws["F10"] = data.get("Rep Name", "")
        ws["J9"] = data.get("Rep Phone", "")
        ws["J10"] = data.get("Rep Email", "")

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

        # ── Vehicle Info ───────────────────────────────
        v_types = str(data.get("Vehicle Type", "") or "").split(",")
        v_makes = str(data.get("Vehicle Make", "") or "").split(",")
        v_models = str(data.get("Vehicle Model", "") or "").split(",")
        v_years = str(data.get("Vehicle Year", "") or "").split(",")

        vehicle_lines = [
            f"{t.strip()} {m.strip()} {mo.strip()} {y.strip()}".strip()
            for t, m, mo, y in zip(v_types, v_makes, v_models, v_years)
            if any([t.strip(), m.strip(), mo.strip(), y.strip()])
        ]
        ws["F34"] = "\n".join(vehicle_lines)
        ws["F34"].alignment = Alignment(wrap_text=True)

        # ── Vehicle Payments ───────────────────────────
        v_payments = str(data.get("Vehicle Monthly Payment", "")).split(",")
        cleaned_values = [p.replace("$", "").replace(",", "").strip() for p in v_payments if p.strip()]
        numeric_values = [float(p) for p in cleaned_values if p.replace(".", "", 1).isdigit()]
        total_payment = sum(numeric_values)
        ws["F35"] = total_payment if len(numeric_values) > 1 else (numeric_values[0] if numeric_values else "")

        # ── Gross/Net Ratios ───────────────────────────
        rent_val = data.get("Monthly Rent", "")
        gross_val = data.get("Gross Monthly Income", "")

        rent_str = str(rent_val).replace("$", "").replace(",", "").strip() if rent_val is not None else ""
        gross_str = str(gross_val).replace("$", "").replace(",", "").strip() if gross_val is not None else ""

        try:
            rent = float(rent_str) if rent_str else 0
        except:
            rent = 0
        try:
            gross = float(gross_str) if gross_str else 0
        except:
            gross = 0

        co_total = 0
        for app in data.get("Co-applicants", []):
            if isinstance(app, dict):
                val = str(app.get("Gross Monthly Income", "") or "").replace("$", "").replace(",", "").strip()
                try:
                    co_total += float(val)
                except:
                    pass

        net_total = gross + co_total
        gross_ratio = f"{gross / rent:.2f}" if rent > 0 else ""
        net_ratio = f"{net_total / rent:.2f}" if rent > 0 else ""

        ws["J3"] = gross_ratio
        ws["J4"] = net_ratio

        # ── Save & Generate Output ───────────────────────
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        def generate_filename(address):
            cleaned = re.sub(r"[^\w\s]", "", str(address))
            words = cleaned.strip().split()
            word_part = (
                "_".join(words[1:3]) if len(words) >= 3 else
                "_".join(words[:2]) if len(words) >= 2 else
                "tenant"
            )
            return f"{word_part}_{datetime.now():%Y%m%d}_app.xlsx"

        return output, generate_filename(property_address)

    except Exception:
        print("❌ Error in write_flattened_to_template:")
        traceback.print_exc()
        return None, None
  
# ───────────────────────────────────────────────────────────────────────────────
# 2. write_multiple_applicants_to_template  (adds per-row type guard)
# ───────────────────────────────────────────────────────────────────────────────
def write_multiple_applicants_to_template(
    df,
    template_path="templates/Tenant_Template_Multiple.xlsx",
    summary_header=None,
):
    try:
        first_row = normalize_all_dates(df.iloc[0].to_dict())
        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        # ── Property Info ─────────────────────────────
        property_address = str(first_row.get("Property Address", "") or "").strip()

        # Initialize left header if missing
        if ws.oddHeader.left is None:
            ws.oddHeader.left = openpyxl.worksheet.header_footer.HeaderFooterItem()
        ws.oddHeader.left.text = property_address

        # Initialize center header if summary_header is used
        if summary_header:
            if ws.oddHeader.center is None:
                ws.oddHeader.center = openpyxl.worksheet.header_footer.HeaderFooterItem()
            existing = ws.oddHeader.center.text or ""
            lines = existing.split("\n")
            new_line = f"Date={summary_header}"
            if len(lines) >= 3:
                lines[2] = new_line
            else:
                lines += [""] * (2 - len(lines)) + [new_line]
            ws.oddHeader.center.text = "\n".join(lines)

        ws["E3"] = property_address
        ws["E4"] = first_row.get("Move-in Date", "")
        ws["E5"] = str(first_row.get("Monthly Rent", "")).replace("$", "").strip()
        ws["F10"] = first_row.get("Rep Name", "")
        ws["J9"] = first_row.get("Rep Phone", "")
        ws["J10"] = first_row.get("Rep Email", "")

        # ── Gross Ratio Calculation (only) ──────────────────────────────
        rent_val = first_row.get("Monthly Rent", "")
        gross_val = first_row.get("Gross Monthly Income", "")

        rent_str = str(rent_val).replace("$", "").replace(",", "").strip() if rent_val is not None else ""
        gross_str = str(gross_val).replace("$", "").replace(",", "").strip() if gross_val is not None else ""

        try:
            rent = float(rent_str) if rent_str else 0
        except:
            rent = 0
        try:
            gross = float(gross_str) if gross_str else 0
        except:
            gross = 0

        gross_ratio = f"{gross / rent:.2f}" if rent > 0 else ""
        ws["J3"] = gross_ratio
        ws["J4"] = ""

        # ── Fill applicant columns ──────────────────────────────────────
        col_starts = ["F", "I", "L", "O", "R", "U", "X", "AA", "AD", "AG"]
        start_row = 14

        for idx, (_, row_series) in enumerate(df.iterrows()):
            if idx >= len(col_starts):
                break

            if not hasattr(row_series, "to_dict"):
                raise TypeError(f"Row {idx} must be Series, got {type(row_series)}")

            row = normalize_all_dates(row_series.to_dict())
            col = col_starts[idx]

            def write(offset, value):
                ws[f"{col}{start_row + offset}"] = value or ""

            write(0, row.get("FullName"))
            write(1, row.get("Email"))
            write(2, row.get("PhoneNumber"))
            write(3, row.get("SSN"))
            write(4, row.get("DriverLicenseNumber"))
            write(5, row.get("DOB"))
            write(6, calc_age(row.get("DOB", "")))
            write(7, str(row.get("No of Occupants", "")))
            write(8, row.get("No of Children", ""))
            write(9, row.get("Applicant's Current Address"))
            write(10, row.get("Landlord or Property Manager's Name"))
            write(11, row.get("Landlord Phone"))
            write(13, row.get("Applicant's Current Employer"))
            write(14, row.get("Employer Address"))
            write(15, f"{row.get('Employment Verification Contact', '')} {row.get('Employer Phone', '')}".strip())
            write(16, row.get("Start Date"))
            write(17, row.get("Gross Monthly Income"))
            write(19, row.get("Position"))

            v_types  = str(row.get("Vehicle Type", "") or "").split(",")
            v_makes  = str(row.get("Vehicle Make", "") or "").split(",")
            v_models = str(row.get("Vehicle Model", "") or "").split(",")
            v_years  = str(row.get("Vehicle Year", "") or "").split(",")

            vehicle_lines = [
                f"{t.strip()} {m.strip()} {mo.strip()} {y.strip()}".strip()
                for t, m, mo, y in zip(v_types, v_makes, v_models, v_years)
                if any([t.strip(), m.strip(), mo.strip(), y.strip()])
            ]

            vehicle_cell = f"{col}{start_row + 20}"
            ws[vehicle_cell] = "\n".join(vehicle_lines) if vehicle_lines else ""
            ws[vehicle_cell].alignment = openpyxl.styles.Alignment(wrap_text=True)

            v_payments = str(row.get("Vehicle Monthly Payment", "")).split(",")
            cleaned_vals = [p.replace("$", "").replace(",", "").strip() for p in v_payments if p.strip()]
            numeric_vals = [float(p) for p in cleaned_vals if p.replace(".", "", 1).isdigit()]
            total_payment = sum(numeric_vals) if len(numeric_vals) > 1 else (numeric_vals[0] if numeric_vals else "")
            write(21, total_payment)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        def generate_filename(address):
            cleaned = re.sub(r"[^\w\s]", "", str(address))
            words = cleaned.strip().split()
            word_part = (
                "_".join(words[1:3]) if len(words) >= 3 else
                "_".join(words[:2]) if len(words) >= 2 else
                "tenant"
            )
            return f"{word_part}_{datetime.now():%Y%m%d}_app.xlsx"

        return output, generate_filename(property_address)       
      
    except Exception:
        print("❌ Error in write_multiple_applicants_to_template:")
        traceback.print_exc()
        return None, None

# ───────────────────────────────────────────────────────────────────────────────
# 3. write_to_summary_template  (now type-safe)
# ───────────────────────────────────────────────────────────────────────────────
def write_to_summary_template(
    flat_data,
    output_path,
    summary_template_path="templates/App_Summary_Template.xlsx",
) -> None:
    """
    Writes one applicant’s key facts into App_Summary_Template.xlsx.
    """
    # ── Ensure dict-like before any .get() ────────────────────────────────
    if isinstance(flat_data, dict):
        pass
    elif hasattr(flat_data, "to_dict"):  # e.g. pandas Series/DataFrame row
        flat_data = flat_data.to_dict()
    else:
        raise TypeError(
            f"write_to_summary_template expected dict/Series, got {type(flat_data)}"
        )

    flat_data = normalize_all_dates(flat_data)
    wb = load_workbook(summary_template_path)
    ws = wb.active

    # Hidden _Meta sheet + counter logic
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

    # ---------- Safely parse rent and income --------------------------
    rent_val = flat_data.get("Monthly Rent", "")
    rent_str = str(rent_val).replace("$", "").replace(",", "").strip() if rent_val is not None else ""

    gross_val = flat_data.get("Gross Monthly Income", "")
    gross_str = str(gross_val).replace("$", "").replace(",", "").strip() if gross_val is not None else ""

    try:
        rent = float(rent_str) if rent_str else 0
    except:
        rent = 0
    try:
        gross = float(gross_str) if gross_str else 0
    except:
        gross = 0

    # ---------- Safe Co-applicant aggregate ---------------------------
    co_total = 0
    for app in flat_data.get("Co-applicants", []):
        if not isinstance(app, dict):
            continue
        val = app.get("Gross Monthly Income", "")
        val = str(val).replace("$", "").replace(",", "").strip() if val is not None else ""
        try:
            co_total += float(val) if val else 0
        except:
            continue

    net_total = gross + co_total

    gross_ratio = f"{gross / rent:.2f}" if rent > 0 else ""
    net_ratio = f"{net_total / rent:.2f}" if rent > 0 else ""

    # ---------- Build vehicle and animal multiline strings -------------------
    # VEHICLES → B12
    vehicle_lines = []
    if isinstance(flat_data.get("F. Vehicle Information:"), list):
        for v in flat_data["F. Vehicle Information:"]:
            if not isinstance(v, dict):
                continue
            line = " ".join(
                str(v.get(k, "")).strip()
                for k in ("Type", "Year", "Make", "Model")
                if v.get(k)
            ).strip()
            if line:
                vehicle_lines.append(line)
    else:
        v_types  = str(flat_data.get("Vehicle Type", "")  or "").split(",")
        v_years  = str(flat_data.get("Vehicle Year", "")  or "").split(",")
        v_makes  = str(flat_data.get("Vehicle Make", "")  or "").split(",")
        v_models = str(flat_data.get("Vehicle Model", "") or "").split(",")
        for t, y, mke, mdl in zip(v_types, v_years, v_makes, v_models):
            line = f"{t.strip()} {y.strip()} {mke.strip()} {mdl.strip()}".strip()
            if line:
                vehicle_lines.append(line)
    vehicle = "\n".join(vehicle_lines)

    # ANIMALS → B13
    animal_lines = []
    if isinstance(flat_data.get("G. Animals"), list):
        for a in flat_data["G. Animals"]:
            if not isinstance(a, dict):
                continue
            line = " | ".join(
                f"{label}: {a.get(key)}" for label, key in [
                    ("Type & Breed", "Type and Breed"),
                    ("Name", "Name"),
                    ("Color", "Color"),
                    ("Weight", "Weight"),
                    ("Age", "Age in Yrs"),
                    ("Gender", "Gender")
                ] if a.get(key)
            )
            if line:
                animal_lines.append(line)
    else:
        default_animals = flat_data.get("Animal Details", flat_data.get("No of Animals", ""))
        if isinstance(default_animals, str) and default_animals.strip():
            animal_lines.append(default_animals.strip())
    animals = "\n".join(animal_lines)

    # Field-to-cell map
    write_map = {
        "B2": flat_data.get("Property Address", ""),
        "B3": flat_data.get("Monthly Rent", ""),
        "B4": flat_data.get("Move-in Date", ""),
        "B5": flat_data.get("Application Fee", ""),
        "B6": f"{gross_ratio}/{net_ratio}",
        "B7": flat_data.get("No of Occupants", ""),
        "B8": flat_data.get("Rent", ""),
        "B9": flat_data.get("Applicant's Current Employer", ""),
        "B12": vehicle,
        "B13": animals,
    }

    for cell, value in write_map.items():
        ws[cell] = value

    # ✅ Also write ratios to J3 and J4 (optional but consistent with other templates)
    ws["J3"] = gross_ratio
    ws["J4"] = net_ratio

    wb.save(output_path)

