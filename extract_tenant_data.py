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
        ws["F21"] = data.get("No of Occupants", "")  # New line
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

        vehicle_lines = [
            f"{t} {m} {mo} {y}".strip()
            for t, m, mo, y in zip(
                data.get("Vehicle Type", "").split(", "),
                data.get("Vehicle Make", "").split(", "),
                data.get("Vehicle Model", "").split(", "),
                data.get("Vehicle Year", "").split(", "),
            )
        ]
        ws["F34"] = "\n".join(vehicle_lines)
        ws["F34"].alignment = openpyxl.styles.Alignment(wrap_text=True)

        ws["F35"] = data.get("Vehicle Monthly Payment", "")  # fixed key

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
