# pipeline/matcher.py
from typing import Optional, Dict, Any, List
from difflib import SequenceMatcher

def calculate_name_similarity(name1: str, name2: str) -> float:
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

def resolve_candidate(
    incoming: Dict[str, Any],
    existing_candidates: List[Dict[str, Any]]
) -> Optional[int]:
    """
    Identifies if an incoming candidate matches an existing record in the database.
    Returns the matching candidate_id or None.
    """
    incoming_phone = incoming.get("phone_normalized")
    incoming_email = incoming.get("email")
    incoming_name = incoming.get("full_name")

    for cand in existing_candidates:
        # Tier 1: Phone match
        if incoming_phone and cand.get("phone_normalized") == incoming_phone:
            return cand["id"]
        
        # Tier 2: Email match
        if incoming_email and cand.get("email") and cand["email"] == incoming_email:
            return cand["id"]
        
        # Tier 3: Fuzzy Name match with Location confirmation
        if incoming_name and cand.get("full_name"):
            name_sim = calculate_name_similarity(incoming_name, cand["full_name"])
            same_loc = (
                incoming.get("location") 
                and cand.get("location") 
                and incoming["location"].lower() == cand["location"].lower()
            )
            if name_sim >= 0.90 or (name_sim >= 0.82 and same_loc):
                return cand["id"]
                
    return None