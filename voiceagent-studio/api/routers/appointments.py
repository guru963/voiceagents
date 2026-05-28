from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import create_client
from core.config import get_settings
from core.logger import get_logger
import uuid
from datetime import datetime

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


def get_supabase():
    return create_client(settings.supabase_url, settings.supabase_service_key)


class AppointmentCreateRequest(BaseModel):
    agent_id: str
    category: str
    ref_id: str
    guest_name: str
    title: str
    appointment_date: str
    appointment_time: Optional[str] = None
    details: dict = {}
    status: str = "confirmed"


class AppointmentUpdateRequest(BaseModel):
    status: str


@router.get("/")
async def list_appointments(month: Optional[str] = None):
    """List appointments, optionally filtered by month (YYYY-MM)."""
    try:
        supabase = get_supabase()
        query = supabase.table("appointments").select("*").order("appointment_date", desc=False)
        if month:
            # Filter by month: appointment_date starts with YYYY-MM
            start = f"{month}-01"
            # Calculate end of month
            year, mon = int(month.split("-")[0]), int(month.split("-")[1])
            if mon == 12:
                end = f"{year + 1}-01-01"
            else:
                end = f"{year}-{mon + 1:02d}-01"
            query = query.gte("appointment_date", start).lt("appointment_date", end)
        result = query.execute()
        return {"appointments": result.data}
    except Exception as e:
        logger.error("list_appointments_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")


@router.post("/")
async def create_appointment(req: AppointmentCreateRequest):
    """Create a new appointment."""
    try:
        supabase = get_supabase()
        result = supabase.table("appointments").insert({
            "agent_id": req.agent_id,
            "category": req.category,
            "ref_id": req.ref_id,
            "guest_name": req.guest_name,
            "title": req.title,
            "appointment_date": req.appointment_date,
            "appointment_time": req.appointment_time,
            "details": req.details,
            "status": req.status,
        }).execute()
        logger.info("appointment_created", ref_id=req.ref_id)
        return {"appointment": result.data[0] if result.data else {}}
    except Exception as e:
        logger.error("create_appointment_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create appointment")


@router.delete("/{appointment_id}")
async def delete_appointment(appointment_id: str):
    """Delete/cancel an appointment."""
    try:
        supabase = get_supabase()
        supabase.table("appointments").delete().eq("id", appointment_id).execute()
        return {"deleted": appointment_id}
    except Exception as e:
        logger.error("delete_appointment_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete appointment")


@router.patch("/{appointment_id}")
async def update_appointment(appointment_id: str, req: AppointmentUpdateRequest):
    """Update appointment status."""
    try:
        supabase = get_supabase()
        result = supabase.table("appointments").update({
            "status": req.status,
        }).eq("id", appointment_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"appointment": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_appointment_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update appointment")
