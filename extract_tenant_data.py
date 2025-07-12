def flatten_extracted_data(data: Dict) -> Dict[str, str]:
    employment = data.get("Employment and Other Income:", {})
    employer_info = employment.get("Current Employer Details", {}) if isinstance(employment.get("Current Employer Details"), dict) else {}
    rep = data.get("C.Representation and Marketing", {})
    addr_block = data.get("Applicant's Current Address", {})

    address_str = addr_block.get("Address", "") if isinstance(addr_block, dict) else addr_block
    address_phone = addr_block.get("Phone:Day", "") if isinstance(addr_block, dict) else ""
    landlord_name = addr_block.get("Landlord or Property Manager's Name", "") if isinstance(addr_block, dict) else ""

    # Occupant and child counts
    occupants = data.get("E. Occupant Information", [])
    children_count = 0
    if not isinstance(occupants, list):
        occupants = []

    for o in occupants:
        if isinstance(o, dict):
            relationship = o.get("Relationship", "").strip().lower()
            if relationship in ("son", "daughter"):
                children_count += 1

    total_occupants = 1 + len(occupants)  # applicant + listed occupants

    # Handle single or multiple vehicle entries
    vehicles = data.get("F. Vehicle Information:", [])
    if isinstance(vehicles, dict):
        vehicles = [vehicles]  # wrap single entry
    elif not isinstance(vehicles, list):
        vehicles = []

    # Join multiple vehicle entries into readable strings
    vehicle_types = ", ".join(v.get("Type", "") for v in vehicles if isinstance(v, dict))
    vehicle_years = ", ".join(v.get("Year", "") for v in vehicles if isinstance(v, dict))
    vehicle_makes = ", ".join(v.get("Make", "") for v in vehicles if isinstance(v, dict))
    vehicle_models = ", ".join(v.get("Model", "") for v in vehicles if isinstance(v, dict))
    vehicle_payments = ", ".join(v.get("Monthly Payment", "") for v in vehicles if isinstance(v, dict))

    flat = {
        "Property Address": data.get("Property Address", ""),
        "Move-in Date": data.get("Move-in Date", ""),
        "Monthly Rent": data.get("Monthly Rent", ""),
        "FullName": data.get("FullName", ""),
        "PhoneNumber": data.get("PhoneNumber", ""),
        "Email": data.get("Email", ""),
        "DOB": data.get("DOB", ""),
        "SSN": data.get("SSN", ""),
        "Applicant's Current Address": address_str,
        "Landlord Phone": address_phone,
        "Landlord or Property Manager's Name": landlord_name,
        "IDType": data.get("IDType", ""),
        "DriverLicenseNumber": data.get("DriverLicenseNumber", ""),
        "IDIssuer": data.get("IDIssuer", ""),
        "Nationality": data.get("Nationality", ""),
        "FormSource": data.get("FormSource", ""),
        "ApplicationDate": data.get("ApplicationDate", ""),
        "Rep Name": rep.get("Name", ""),
        "Rep Company": rep.get("Company", ""),
        "Rep Email": rep.get("E-mail", ""),
        "Rep Phone": rep.get("Phone Number", ""),
        "Applicant's Current Employer": employment.get("Applicant's Current Employer", ""),
        "Employment Verification Contact": employer_info.get("Employment Verification Contact", ""),
        "Employer Address": employer_info.get("Address", ""),
        "Employer Phone": employer_info.get("Phone", ""),
        "Employer Email": employer_info.get("E-mail", ""),
        "Position": employer_info.get("Position", ""),
        "Start Date": employer_info.get("Start Date", ""),
        "Gross Monthly Income": employer_info.get("Gross Monthly Income", ""),
        "Child Support": employment.get("Child Support", ""),
        "Vehicle Type": vehicle_types,
        "Vehicle Year": vehicle_years,
        "Vehicle Make": vehicle_makes,
        "Vehicle Model": vehicle_models,
        "Vehicle Monthly Payment": vehicle_payments,
        "No of Children": children_count,
        "No of Occupants": total_occupants,
    }

    return {k: ("" if v is None else v) for k, v in flat.items()}
