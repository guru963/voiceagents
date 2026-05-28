# E:\Voice agents\voiceagent-studio\agent\rag\doctors_data.py
import json

DOCTORS_DATABASE = {
    "cardiology": {
        "description": "Floor 3, Block A. Specialises in heart conditions, cardiovascular health, and ECG/Echocardiogram testing.",
        "doctors": [
            {
                "name": "Dr. Ramesh Kumar",
                "specialty": "Interventional Cardiology",
                "free_slots": {
                    "monday": ["10:00 AM", "11:00 AM", "02:00 PM"],
                    "tuesday": ["09:00 AM", "10:30 AM", "01:30 PM"],
                    "wednesday": ["10:00 AM", "11:00 AM", "02:00 PM"],
                    "thursday": ["09:00 AM", "10:30 AM", "01:30 PM"],
                    "friday": ["10:00 AM", "11:00 AM", "02:00 PM"],
                    "saturday": ["09:00 AM", "11:00 AM"],
                    "sunday": []
                }
            },
            {
                "name": "Dr. Priya Nair",
                "specialty": "Non-Invasive Cardiology",
                "free_slots": {
                    "monday": ["09:00 AM", "01:00 PM", "03:00 PM"],
                    "tuesday": ["10:00 AM", "11:30 AM", "02:30 PM"],
                    "wednesday": ["09:00 AM", "01:00 PM", "03:00 PM"],
                    "thursday": ["10:00 AM", "11:30 AM", "02:30 PM"],
                    "friday": ["09:00 AM", "01:00 PM", "03:00 PM"],
                    "saturday": ["10:00 AM", "12:00 PM"],
                    "sunday": []
                }
            }
        ]
    },
    "orthopaedics": {
        "description": "Floor 2, Block B. Joint replacements, fracture care, bone health, and physical therapy coordination.",
        "doctors": [
            {
                "name": "Dr. Suresh Iyer",
                "specialty": "Joint Replacement",
                "free_slots": {
                    "monday": ["11:30 AM", "01:30 PM", "04:00 PM"],
                    "tuesday": ["10:00 AM", "12:00 PM", "03:00 PM"],
                    "wednesday": ["11:30 AM", "01:30 PM", "04:00 PM"],
                    "thursday": ["10:00 AM", "12:00 PM", "03:00 PM"],
                    "friday": ["11:30 AM", "01:30 PM", "04:00 PM"],
                    "saturday": ["09:00 AM", "11:00 AM"],
                    "sunday": []
                }
            },
            {
                "name": "Dr. Maheshwari Rao",
                "specialty": "Spine & Pediatric Orthopaedics",
                "free_slots": {
                    "monday": ["10:00 AM", "12:00 PM", "03:00 PM"],
                    "tuesday": ["11:30 AM", "01:30 PM", "04:00 PM"],
                    "wednesday": ["10:00 AM", "12:00 PM", "03:00 PM"],
                    "thursday": ["11:30 AM", "01:30 PM", "04:00 PM"],
                    "friday": ["10:00 AM", "12:00 PM", "03:00 PM"],
                    "saturday": ["10:00 AM", "12:00 PM"],
                    "sunday": []
                }
            }
        ]
    },
    "general": {
        "description": "Floor 1, Block A. Routine health checkups, chronic disease management, and general diagnosis.",
        "doctors": [
            {
                "name": "Dr. Anita Sharma",
                "specialty": "General Medicine",
                "free_slots": {
                    "monday": ["09:00 AM", "10:30 AM", "02:00 PM"],
                    "tuesday": ["11:00 AM", "03:00 PM", "04:30 PM"],
                    "wednesday": ["09:00 AM", "10:30 AM", "02:00 PM"],
                    "thursday": ["11:00 AM", "03:00 PM", "04:30 PM"],
                    "friday": ["09:00 AM", "10:30 AM", "02:00 PM"],
                    "saturday": ["09:00 AM", "11:30 AM"],
                    "sunday": []
                }
            },
            {
                "name": "Dr. Kiran Patel",
                "specialty": "Family Medicine",
                "free_slots": {
                    "monday": ["11:00 AM", "03:00 PM", "04:30 PM"],
                    "tuesday": ["09:00 AM", "10:30 AM", "02:00 PM"],
                    "wednesday": ["11:00 AM", "03:00 PM", "04:30 PM"],
                    "thursday": ["09:00 AM", "10:30 AM", "02:00 PM"],
                    "friday": ["11:00 AM", "03:00 PM", "04:30 PM"],
                    "saturday": ["10:00 AM", "01:00 PM"],
                    "sunday": []
                }
            }
        ]
    },
    "pediatrics": {
        "description": "Floor 2, Block C. Child health, vaccinations, and pediatric emergency services.",
        "doctors": [
            {
                "name": "Dr. Rohan Das",
                "specialty": "General Pediatrics",
                "free_slots": {
                    "monday": ["10:00 AM", "01:00 PM", "04:00 PM"],
                    "tuesday": ["09:30 AM", "11:30 AM", "02:30 PM"],
                    "wednesday": ["10:00 AM", "01:00 PM", "04:00 PM"],
                    "thursday": ["09:30 AM", "11:30 AM", "02:30 PM"],
                    "friday": ["10:00 AM", "01:00 PM", "04:00 PM"],
                    "saturday": ["09:00 AM", "12:00 PM"],
                    "sunday": []
                }
            },
            {
                "name": "Dr. Aisha Khan",
                "specialty": "Neonatology",
                "free_slots": {
                    "monday": ["09:30 AM", "11:30 AM", "02:30 PM"],
                    "tuesday": ["10:00 AM", "01:00 PM", "04:00 PM"],
                    "wednesday": ["09:30 AM", "11:30 AM", "02:30 PM"],
                    "thursday": ["10:00 AM", "01:00 PM", "04:00 PM"],
                    "friday": ["09:30 AM", "11:30 AM", "02:30 PM"],
                    "saturday": ["10:00 AM", "01:00 PM"],
                    "sunday": []
                }
            }
        ]
    },
    "dermatology": {
        "description": "Floor 1, Block B. Skin, hair, and nail treatments, including allergy testing.",
        "doctors": [
            {
                "name": "Dr. Vikram Sen",
                "specialty": "Clinical Dermatology",
                "free_slots": {
                    "monday": ["10:00 AM", "12:30 PM", "03:30 PM"],
                    "tuesday": ["09:00 AM", "11:00 AM", "02:00 PM"],
                    "wednesday": ["10:00 AM", "12:30 PM", "03:30 PM"],
                    "thursday": ["09:00 AM", "11:00 AM", "02:00 PM"],
                    "friday": ["10:00 AM", "12:30 PM", "03:30 PM"],
                    "saturday": ["09:00 AM", "12:00 PM"],
                    "sunday": []
                }
            }
        ]
    }
}

def query_availability(department: str, date: str) -> str:
    """Helper to query the doctors database for a specific department and date."""
    dept_key = department.lower().strip()
    date_key = date.lower().strip()
    
    # Try to extract the day of week if a full date/string is provided
    # e.g., "Monday, June 1st" -> "monday"
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        if day in date_key:
            date_key = day
            break
            
    if dept_key not in DOCTORS_DATABASE:
        available_depts = ", ".join(DOCTORS_DATABASE.keys())
        return f"Department '{department}' not found. Available departments: {available_depts}."
        
    dept_info = DOCTORS_DATABASE[dept_key]
    results = []
    
    for doc in dept_info["doctors"]:
        # default to monday if date parsing couldn't map to a weekday
        day_slots = doc["free_slots"].get(date_key)
        if day_slots is None:
            # check if they just passed a day or name, default to monday for simplicity in mock
            day_slots = doc["free_slots"].get("monday", [])
            date_display = "Monday"
        else:
            date_display = date.capitalize()
            
        if day_slots:
            slots_str = ", ".join(day_slots)
            results.append(f"{doc['name']} ({doc['specialty']}): {slots_str} on {date_display}")
        else:
            results.append(f"{doc['name']} ({doc['specialty']}): No slots available on {date_display}")
            
    return f"Available slots in {department} on {date}: " + " | ".join(results)

def get_dept_details(department: str) -> str:
    dept_key = department.lower().strip()
    if dept_key not in DOCTORS_DATABASE:
        return f"Department {department} not found."
    return f"{department.capitalize()} Department: {DOCTORS_DATABASE[dept_key]['description']}"


def get_slots_list(department: str, date: str) -> list[str]:
    """Helper to query the doctors database and return a list of formatted slots, e.g. ['Dr. Ramesh Kumar - 10:00 AM', ...]"""
    dept_key = department.lower().strip()
    date_key = date.lower().strip()
    
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        if day in date_key:
            date_key = day
            break
            
    if dept_key not in DOCTORS_DATABASE:
        return []
        
    slots = []
    for doc in DOCTORS_DATABASE[dept_key]["doctors"]:
        day_slots = doc["free_slots"].get(date_key)
        if day_slots is None:
            # fallback to monday if day not found
            day_slots = doc["free_slots"].get("monday", [])
        for slot in day_slots:
            slots.append(f"{doc['name']} - {slot}")
    return slots

