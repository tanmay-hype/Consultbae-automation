# pipeline/normalizer.py
import re
from typing import Optional, List, Tuple

def normalize_phone(phone_raw: any) -> Optional[str]:
    """
    Sanitizes Indian phone numbers into a standard 10-digit format.
    Strips country code (+91, 91), leading zeros, spaces, and punctuation.
    """
    if not phone_raw or str(phone_raw).strip().lower() in ["nan", "none", "null", ""]:
        return None
    
    digits = re.sub(r"\D", "", str(phone_raw))
    
    # Handle country codes and leading zeroes
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    
    if len(digits) == 10 and digits[0] in "6789":
        return digits
    return None

def normalize_email(email_raw: any) -> Optional[str]:
    """Cleans email addresses, converts to lowercase, and strips junk strings."""
    if not email_raw or str(email_raw).strip().lower() in ["nan", "none", "null", "n/a", "-", ""]:
        return None
    email = str(email_raw).strip().lower()
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return email if re.match(email_regex, email) else None

def normalize_name(name_raw: any) -> str:
    """Standardizes names by stripping honorifics and converting to title case."""
    if not name_raw or str(name_raw).strip().lower() in ["nan", "none", "null", ""]:
        return "Unknown Applicant"
    name = str(name_raw).strip()
    name = re.sub(r"^(mr\.|ms\.|mrs\.|dr\.)\s+", "", name, flags=re.IGNORECASE)
    return " ".join(part.capitalize() for part in name.split())

def parse_experience(exp_raw: any) -> float:
    """Parses experience strings ('3 yrs', '24 months', 'Fresher') to float years."""
    if not exp_raw or str(exp_raw).strip().lower() in ["nan", "none", "fresher", "0", ""]:
        return 0.0
    text = str(exp_raw).lower()
    
    # Months check
    months_match = re.search(r"(\d+(\.\d+)?)\s*m", text)
    if months_match:
        return round(float(months_match.group(1)) / 12.0, 2)
    
    # Years check
    years_match = re.search(r"(\d+(\.\d+)?)", text)
    if years_match:
        return round(float(years_match.group(1)), 2)
    return 0.0

def normalize_skills(skills_raw: any) -> List[str]:
    """Splits multi-delimiter skill strings, standardizes casing, and deduplicates."""
    if not skills_raw or str(skills_raw).strip().lower() in ["nan", "none", "null", ""]:
        return []
    raw_tokens = re.split(r"[,/|;]+", str(skills_raw))
    cleaned = set()
    for token in raw_tokens:
        t = token.strip().lower()
        if t and len(t) > 1:
            cleaned.add(t)
    return sorted(list(cleaned))