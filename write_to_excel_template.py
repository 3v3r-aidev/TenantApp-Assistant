import openpyxl
import re
import traceback
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from datetime import datetime
from pathlib import Path
from io import BytesIO
from datetime import datetime, date
import pandas as pd 

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
        # ✅ Normalize date fields correctly
        data = normalize_all_dates(data)

        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        # ── Property Info ─────────────────────────────────────────────
        prop_address = first_row.get("Property Address", "")
        prop_str = str(prop_address) if prop_address is not None else ""
        ws.oddHeader.left.text = prop_str

        ws["E3"] = property_address
        ws["E4"] = data.get("Move-in Date", "")
        ws["E5"] = str(data.get("Monthly Rent", "")).replace("$", "").strip()

        # ✅ Set center header with 3 lines
        if summary_header:
            ws.oddHeader.center.text = (
                "Rental Application Checklist\n"
                "Processed by: Daniela\n"
                f"Date={summary_header}"
            )

        # ✅ Lookup PropertyInfo.xlsx for G3 and G7 (match on first 3 words)
        try:
            prop_df = pd.read_excel("PropertyInfo.xlsx", header=None, dtype=str)

            # Build lowercase 3-word prefix for the current address
            addr_prefix = " ".join(property_address.strip().lower().split()[:3])

            # Create a mask where Column-C’s 3-word prefix matches
            mask = prop_df[2].fillna("").str.lower().apply(
                lambda x: " ".join(x.split()[:3])
            ) == addr_prefix

            match = prop_df[mask]
            if not match.empty:
                ws["G3"] = match.iloc[0, 1]  # Column B → G3
                ws["G7"] = match.iloc[0, 3]  # Column D → G7
        except Exception as e:
            print(f"Warning: Failed to match property in PropertyInfo.xlsx – {e}")

        # ── Representative ──────────────────────────────────────────
        ws["F10"] = data.get("Rep Name", "")
        ws["J9"] = data.get("Rep Phone", "")
        ws["J10"] = data.get("Rep Email", "")

        # ── Applicant Info ──────────────────────────────────────────
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

        # ── Vehicle Info (All Vehicles) ──────────────────────────────
        v_types = str(data.get("Vehicle Type", "") or "").split(",")
        v_makes = str(data.get("Vehicle Make", "") or "").split(",")
        v_models = str(data.get("Vehicle Model", "") or "").split(",")
        v_years = str(data.get("Vehicle Year", "") or "").split(",")

        vehicle_lines = [
            f"{t.strip()} {m.strip()} {mo.strip()} {y.strip()}".strip()
            for t, m, mo, y in zip(v_types, v_makes, v_models, v_years)
            if any([t.strip(), m.strip(), mo.strip(), y.strip()])
        ]
        ws["F34"] = "\n".join(vehicle_lines) if vehicle_lines else ""
        ws["F34"].alignment = openpyxl.styles.Alignment(wrap_text=True)

        # ── Vehicle Monthly Payment (Sum or single, now handles non-numeric) ──
        v_payments = str(data.get("Vehicle Monthly Payment", "")).split(",")
        cleaned_values = [p.replace("$", "").replace(",", "").strip() for p in v_payments if p.strip()]

        numeric_values = []
        for p in cleaned_values:
            try:
                numeric_values.append(float(p))
            except:
                continue

        if numeric_values:
            total_payment = sum(numeric_values)
            ws["F35"] = total_payment if len(numeric_values) > 1 else numeric_values[0]
        else:
            # If no numeric payments, write first non-empty string (e.g. "Paid Off")
            non_numeric = [p for p in cleaned_values if p]
            ws["F35"] = non_numeric[0] if non_numeric else ""

        # ── Save to BytesIO ─────────────────────────────────────────
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        def generate_filename(address):
            cleaned = re.sub(r"[^\w\s]", "", str(address))
            words = cleaned.strip().split()
            word_part = "_".join(words[1:3]) if len(words) >= 3 else "_".join(words[:2]) if len(words) >= 2 else "tenant"
            return f"{word_part}_{datetime.now().strftime('%Y%m%d')}_app.xlsx"

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
    """
    Writes up to 10 applicants into Tenant_Template_Multiple.xlsx.
    """
    try:
        # ✅ Normalize first row
        first_row = normalize_all_dates(df.iloc[0].to_dict())

        wb = openpyxl.load_workbook(template_path)
        ws = wb.active

        # ── Property Info ─────────────────────────────────────────────
        property_address = data.get("Property Address", "")
        prop_str = str(property_address) if property_address is not None else ""
        ws.oddHeader.left.text = prop_str
        
        ws["E3"] = property_address
        ws["E4"] = data.get("Move-in Date", "")
        ws["E5"] = str(data.get("Monthly Rent", "")).replace("$", "").strip()

        # ✅ Set center header with 3 lines
        if summary_header:
            ws.oddHeader.center.text = (
                "Rental Application Checklist\n"
                "Processed by: Daniela\n"
                f"Date={summary_header}"
            )

        # ✅ Lookup PropertyInfo.xlsx for G3 and G7 (match on first 3 words)
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
            print(f"Warning: Failed to match property in PropertyInfo.xlsx – {e}")

        ws["E3"] = property_address
        ws["E4"] = first_row.get("Move-in Date", "")
        ws["E5"] = str(first_row.get("Monthly Rent", "")).replace("$", "").strip()
        ws["F10"] = first_row.get("Rep Name", "")
        ws["J9"] = first_row.get("Rep Phone", "")
        ws["J10"] = first_row.get("Rep Email", "")

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

            v_types = str(row.get("Vehicle Type", "") or "").split(",")
            v_makes = str(row.get("Vehicle Make", "") or "").split(",")
            v_models = str(row.get("Vehicle Model", "") or "").split(",")
            v_years = str(row.get("Vehicle Year", "") or "").split(",")

            vehicle_lines = [
                f"{t.strip()} {m.strip()} {mo.strip()} {y.strip()}".strip()
                for t, m, mo, y in zip(v_types, v_makes, v_models, v_years)
                if any([t.strip(), m.strip(), mo.strip(), y.strip()])
            ]

            vehicle_cell = f"{col}{start_row + 20}"
            ws[vehicle_cell] = "\n".join(vehicle_lines) if vehicle_lines else ""
            ws[vehicle_cell].alignment = openpyxl.styles.Alignment(wrap_text=True)

            # ✅ Vehicle Monthly Payment: robust non-numeric handling
            v_payments = str(row.get("Vehicle Monthly Payment", "")).split(",")
            cleaned_vals = [p.replace("$", "").replace(",", "").strip() for p in v_payments if p.strip()]

            numeric_vals = []
            for p in cleaned_vals:
                try:
                    numeric_vals.append(float(p))
                except:
                    continue

            if numeric_vals:
                total_payment = sum(numeric_vals)
                write(21, total_payment if len(numeric_vals) > 1 else numeric_vals[0])
            else:
                non_numeric = [p for p in cleaned_vals if p]
                write(21, non_numeric[0] if non_numeric else "")

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        cleaned = re.sub(r"[^\w\s]", "", property_address)
        words = cleaned.strip().split()
        word_part = (
            "_".join(words[1:3]) if len(words) >= 3
            else "_".join(words[:2]) if len(words) >= 2
            else "tenant"
        )
        filename = f"{word_part}_{datetime.now().strftime('%Y%m%d')}_app.xlsx".lower()

        return output, filename

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
    if isinstance(flat_data, dict):
        pass
    elif hasattr(flat_data, "to_dict"):
        flat_data = flat_data.to_dict()
    else:
        raise TypeError(f"write_to_summary_template expected dict/Series, got {type(flat_data)}")

    flat_data = normalize_all_dates(flat_data)
    wb = load_workbook(summary_template_path)
    ws = wb.active

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

    rent_str = flat_data.get("Monthly Rent", "").replace("$", "").replace(",", "").strip()
    gross_str = flat_data.get("Gross Monthly Income", "").replace("$", "").replace(",", "").strip()
    try:
        rent = float(rent_str) if rent_str else 0
    except:
        rent = 0
    try:
        gross = float(gross_str) if gross_str else 0
    except:
        gross = 0

    co_total = 0
    for app in flat_data.get("Co-applicants", []):
        if not isinstance(app, dict):
            continue
        val = str(app.get("Gross Monthly Income", "")).replace("$", "").replace(",", "").strip()
        try:
            co_total += float(val) if val else 0
        except:
            continue
    net_total = gross + co_total

    gross_ratio = f"{gross / rent:.2f}" if rent > 0 else ""
    net_ratio = f"{net_total / rent:.2f}" if rent > 0 else ""

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
        v_types = str(flat_data.get("Vehicle Type", "") or "").split(",")
        v_years = str(flat_data.get("Vehicle Year", "") or "").split(",")
        v_makes = str(flat_data.get("Vehicle Make", "") or "").split(",")
        v_models = str(flat_data.get("Vehicle Model", "") or "").split(",")
        for t, y, mke, mdl in zip(v_types, v_years, v_makes, v_models):
            line = f"{t.strip()} {y.strip()} {mke.strip()} {mdl.strip()}".strip()
            if line:
                vehicle_lines.append(line)
    vehicle = "\n".join(vehicle_lines)

def write_to_summary_template(
    flat_data,
    output_path,
    summary_template_path="templates/App_Summary_Template.xlsx",
) -> None:
    """
    Writes one applicant’s key facts into App_Summary_Template.xlsx.
    """
    if isinstance(flat_data, dict):
        pass
    elif hasattr(flat_data, "to_dict"):
        flat_data = flat_data.to_dict()
    else:
        raise TypeError(f"write_to_summary_template expected dict/Series, got {type(flat_data)}")

    flat_data = normalize_all_dates(flat_data)
    wb = load_workbook(summary_template_path)
    ws = wb.active

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

    rent_str = flat_data.get("Monthly Rent", "").replace("$", "").replace(",", "").strip()
    gross_str = flat_data.get("Gross Monthly Income", "").replace("$", "").replace(",", "").strip()
    try:
        rent = float(rent_str) if rent_str else 0
    except:
        rent = 0
    try:
        gross = float(gross_str) if gross_str else 0
    except:
        gross = 0

    co_total = 0
    for app in flat_data.get("Co-applicants", []):
        if not isinstance(app, dict):
            continue
        val = str(app.get("Gross Monthly Income", "")).replace("$", "").replace(",", "").strip()
        try:
            co_total += float(val) if val else 0
        except:
            continue
    net_total = gross + co_total

    gross_ratio = f"{gross / rent:.2f}" if rent > 0 else ""
    net_ratio = f"{net_total / rent:.2f}" if rent > 0 else ""

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
        v_types = str(flat_data.get("Vehicle Type", "") or "").split(",")
        v_years = str(flat_data.get("Vehicle Year", "") or "").split(",")
        v_makes = str(flat_data.get("Vehicle Make", "") or "").split(",")
        v_models = str(flat_data.get("Vehicle Model", "") or "").split(",")
        for t, y, mke, mdl in zip(v_types, v_years, v_makes, v_models):
            line = f"{t.strip()} {y.strip()} {mke.strip()} {mdl.strip()}".strip()
            if line:
                vehicle_lines.append(line)
    vehicle = "\n".join(vehicle_lines)

    # ✅ ANIMALS → B13 (uses pre-flattened summary)
    animals = flat_data.get("Animal Summary", "")

