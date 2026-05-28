"""
Tool functions callable by the LLM during a voice conversation.
Each tool is a simple async function. The agent framework calls these
when the LLM decides a tool is needed.
"""
from datetime import datetime, timedelta
from core.logger import get_logger

logger = get_logger(__name__)


# ── Healthcare tools ──────────────────────────────────────────────────────────

async def book_appointment(
    patient_name: str,
    department: str,
    preferred_date: str,
    doctor_name: str = "",
) -> str:
    """Book a hospital appointment. ONLY call after collecting patient name, department, doctor, date, AND getting explicit confirmation."""
    logger.info(
        "tool_book_appointment",
        patient=patient_name,
        dept=department,
        date=preferred_date,
    )
    # In production: call your hospital HMS API here
    # For demo: return a realistic mock response
    ref_id = f"APL{datetime.now().strftime('%Y%m%d%H%M')}"
    return (
        f"Appointment confirmed for {patient_name} in {department} "
        f"on {preferred_date}. Reference ID: {ref_id}. "
        f"Please arrive 15 minutes early with your ID and insurance card."
    )


async def check_doctor_availability(department: str, date: str) -> str:
    """Look up available doctor slots. ONLY call after the patient has specified which department and date they want."""
    logger.info("tool_check_availability", dept=department, date=date)
    from rag.doctors_data import query_availability
    return query_availability(department, date)


async def get_department_info(department: str) -> str:
    """Get location and details for a specific hospital department. Only call when the patient asks about a department."""
    from rag.doctors_data import get_dept_details
    return get_dept_details(department)


# ── Hospitality tools ─────────────────────────────────────────────────────────

async def book_restaurant(
    guest_name: str,
    restaurant: str,
    date: str,
    time: str,
    guests: int,
) -> str:
    """Book a restaurant table at the hotel."""
    logger.info("tool_book_restaurant", guest=guest_name, restaurant=restaurant)
    ref_id = f"LLP{datetime.now().strftime('%H%M%S')}"
    return (
        f"Table reserved for {guests} at {restaurant} on {date} at {time}. "
        f"Confirmation: {ref_id}. A table by the window has been arranged for you, {guest_name}."
    )


async def check_room_availability(room_type: str, check_in: str, check_out: str) -> str:
    """Check hotel room availability."""
    mock_rooms = {
        "deluxe": "Available — ₹12,000/night, sea view, king bed",
        "suite": "2 suites available — ₹28,000/night, private balcony",
        "premier": "Available — ₹18,000/night, city view",
    }
    return mock_rooms.get(
        room_type.lower(),
        f"{room_type} — please hold while I check with our reservations team."
    )


async def get_amenities(amenity: str = "") -> str:
    """Get hotel amenity information."""
    amenities = {
        "spa": "Tattva Spa — Floor 5, open 7 AM to 10 PM. Treatments from ₹3,500.",
        "pool": "Infinity pool — Rooftop, open 6 AM to 9 PM. Towels provided.",
        "gym": "Fitness centre — Floor 4, open 24 hours. Personal trainer available.",
        "wifi": "Complimentary high-speed WiFi throughout the property. Password at check-in.",
        "parking": "Valet parking available. Complimentary for hotel guests.",
    }
    if amenity:
        return amenities.get(amenity.lower(), "Please contact the concierge desk for details.")
    return "We offer: " + ", ".join(amenities.keys())


# ── Tool registry — maps tool name → function ─────────────────────────────────

TOOL_REGISTRY = {
    "book_appointment": book_appointment,
    "check_doctor_availability": check_doctor_availability,
    "get_department_info": get_department_info,
    "book_restaurant": book_restaurant,
    "check_room_availability": check_room_availability,
    "get_amenities": get_amenities,
}
