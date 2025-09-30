from datetime import datetime, timedelta, time
from os import getenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dateutil import tz
from app.models import User, CalendarSettings
from app.database import db_session

def get_teacher_availability(user_id, days=5):
    
    SERVICE_ACCOUNT_FILE = getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not SERVICE_ACCOUNT_FILE:
        raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS is not set")
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)

    
    teacher = db_session.query(User).filter_by(id=user_id, role='teacher').first()
    if not teacher:
        return {}

    

    settings = db_session.query(CalendarSettings).filter_by(teacher_id=teacher.id).first()
    if not settings:
        return {}


    sao_paulo = tz.gettz("America/Sao_Paulo")
    today = datetime.now(tz=sao_paulo).replace(hour=0, minute=0, second=0, microsecond=0)
    end = today
    working_days = []

    while len(working_days) < days:
        weekday = end.weekday()  # 0 = Mon, 6 = Sun

        if (
            (weekday < 5) or
            (weekday == 5 and settings.available_saturday) or
            (weekday == 6 and settings.available_sunday)
        ):
            if settings.show_today or end.date() != today.date():
                working_days.append(end)

        end += timedelta(days=1)

    if not working_days:
        return {}

    end = working_days[-1] + timedelta(days=1)

    # Query Google Calendar busy times
    freebusy_query = {
        "timeMin": today.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": "America/Sao_Paulo",
        "items": [{"id": teacher.email}],
    }
    busy_res = service.freebusy().query(body=freebusy_query).execute()
    busy_periods = busy_res["calendars"][teacher.email]["busy"]

    # Generate available slots
    slots_by_day = {}
    slot_start = time(settings.start_hour)
    slot_end = time(settings.end_hour, 21)

    for day in working_days:
        current = datetime.combine(day.date(), slot_start, tzinfo=sao_paulo)
        end_of_day = datetime.combine(day.date(), slot_end, tzinfo=sao_paulo)
        slots = []
        while current < end_of_day:
            next_slot = current + timedelta(minutes=settings.lesson_duration)
            # Skip if any busy block overlaps
            if not any(b["start"] < next_slot.isoformat() and b["end"] > current.isoformat() for b in busy_periods):
                slots.append((current, next_slot))
            current = next_slot
        slots_by_day[day.date()] = slots

    return slots_by_day
