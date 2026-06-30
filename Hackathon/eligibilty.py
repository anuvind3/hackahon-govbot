# ─────────────────────────────────────────
# SCHEME 1 — PM-KISAN (Farmer support)
# ─────────────────────────────────────────

def check_pmkisan(user_answers: dict) -> dict:
    owns_land = user_answers.get("owns_land", False)
    land_hectares = user_answers.get("land_hectares", 0)
    is_govt_employee = user_answers.get("is_govt_employee", False)
    is_taxpayer = user_answers.get("is_taxpayer", False)
    is_professional = user_answers.get("is_professional", False)

    if not owns_land:
        return {"eligible": False, "reason": "You must own cultivable land to qualify for PM-KISAN."}

    if land_hectares > 2:
        return {"eligible": False, "reason": "PM-KISAN is for small and marginal farmers with up to 2 hectares of land."}

    if is_govt_employee:
        return {"eligible": False, "reason": "Government employees are excluded from PM-KISAN."}

    if is_taxpayer:
        return {"eligible": False, "reason": "Income tax payers are not eligible for PM-KISAN."}

    if is_professional:
        return {"eligible": False, "reason": "Professionals such as doctors, lawyers, and CAs are excluded from PM-KISAN."}

    return {
        "eligible": True,
        "reason": f"You own {land_hectares} hectares of cultivable land and do not fall under any excluded category. You qualify for ₹6,000/year under PM-KISAN, paid in three instalments of ₹2,000."
    }


# ─────────────────────────────────────────
# SCHEME 2 — PM Scholarship Scheme (PMSS)
# For wards of ex-servicemen / ex-coast guard
# ─────────────────────────────────────────

def check_pmss(user_answers: dict) -> dict:
    is_ward_of_exserviceman = user_answers.get("is_ward_of_exserviceman", False)
    class12_percentage = user_answers.get("class12_percentage", 0)
    annual_family_income = user_answers.get("annual_family_income", 0)
    is_pursuing_professional = user_answers.get("is_pursuing_professional", False)

    if not is_ward_of_exserviceman:
        return {"eligible": False, "reason": "PM Scholarship Scheme is only for wards of ex-servicemen or ex-coast guard personnel."}

    if class12_percentage < 60:
        return {"eligible": False, "reason": "You need a minimum of 60% in Class 12 to qualify for PMSS."}

    if annual_family_income > 600000:
        return {"eligible": False, "reason": "Annual family income must be below ₹6,00,000 to qualify for PMSS."}

    if not is_pursuing_professional:
        return {"eligible": False, "reason": "PMSS is only for students pursuing professional degrees such as engineering, medical, MBA, or MCA."}

    return {
        "eligible": True,
        "reason": f"You are a ward of an ex-serviceman with {class12_percentage}% in Class 12 and a family income of ₹{annual_family_income}/year. You qualify for PMSS — ₹2,500/month for boys and ₹3,000/month for girls."
    }


# ─────────────────────────────────────────
# SCHEME 3 — Ayushman Bharat PM-JAY
# Health insurance up to ₹5 lakh/year
# ─────────────────────────────────────────

def check_pmjay(user_answers: dict) -> dict:
    annual_family_income = user_answers.get("annual_family_income", 0)
    has_govt_health_insurance = user_answers.get("has_govt_health_insurance", False)
    is_govt_employee = user_answers.get("is_govt_employee", False)
    family_size = user_answers.get("family_size", 0)

    if is_govt_employee:
        return {"eligible": False, "reason": "Government employees already have CGHS coverage and are excluded from Ayushman Bharat PM-JAY."}

    if has_govt_health_insurance:
        return {"eligible": False, "reason": "You are already covered under a government health scheme and are not eligible for PM-JAY."}

    if annual_family_income > 500000:
        return {"eligible": False, "reason": "Ayushman Bharat PM-JAY is for economically weaker families. Annual income must be below ₹5,00,000."}

    if family_size == 0:
        return {"eligible": False, "reason": "Please provide a valid family size to check eligibility."}

    return {
        "eligible": True,
        "reason": f"Your family of {family_size} with an annual income of ₹{annual_family_income} qualifies for Ayushman Bharat PM-JAY. You are entitled to free health coverage of up to ₹5,00,000 per year at empanelled hospitals."
    }


# ─────────────────────────────────────────
# MASTER ROUTER — Member C calls this
# ─────────────────────────────────────────

def check_eligibility(scheme: str, user_answers: dict) -> dict:
    scheme = scheme.lower().strip()

    if scheme == "pmkisan":
        return check_pmkisan(user_answers)
    elif scheme == "pmss":
        return check_pmss(user_answers)
    elif scheme == "pmjay":
        return check_pmjay(user_answers)
    else:
        return {"eligible": False, "reason": f"Scheme '{scheme}' is not supported yet."}


# ─────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("── PM-KISAN ──")
    print(check_eligibility("pmkisan", {"owns_land": True, "land_hectares": 1.5, "is_govt_employee": False, "is_taxpayer": False, "is_professional": False}))
    print(check_eligibility("pmkisan", {"owns_land": True, "land_hectares": 3.0, "is_govt_employee": False, "is_taxpayer": False, "is_professional": False}))

    print("\n── PM Scholarship ──")
    print(check_eligibility("pmss", {"is_ward_of_exserviceman": True, "class12_percentage": 75, "annual_family_income": 450000, "is_pursuing_professional": True}))
    print(check_eligibility("pmss", {"is_ward_of_exserviceman": False, "class12_percentage": 80, "annual_family_income": 300000, "is_pursuing_professional": True}))

    print("\n── Ayushman Bharat ──")
    print(check_eligibility("pmjay", {"annual_family_income": 250000, "has_govt_health_insurance": False, "is_govt_employee": False, "family_size": 4}))
    print(check_eligibility("pmjay", {"annual_family_income": 250000, "has_govt_health_insurance": False, "is_govt_employee": True, "family_size": 3}))