def check_worker_eligibility(data):
    dob = data.get("dob", "")
    if dob:
        year = int(dob.split("-")[0])
        age = 2025 - year
        if age < 18:
            return False, "Applicant must be at least 18 years old"
    return True, "Eligible"
