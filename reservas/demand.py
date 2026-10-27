from collections import Counter
from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Booking, Resource


WEEKDAY_NAMES = (
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
)


def _start_of_week(day):
    return day - timedelta(days=day.weekday())


def _aware_start(day):
    return timezone.make_aware(datetime.combine(day, time.min))


def build_demand_forecast(weeks=8, today=None):
    """Resume semanas completas y proyecta la siguiente con una media móvil de 4."""
    today = today or timezone.localdate()
    current_week = _start_of_week(today)
    first_week = current_week - timedelta(weeks=weeks)
    week_starts = [first_week + timedelta(weeks=index) for index in range(weeks)]

    bookings = Booking.objects.filter(
        start_time__gte=_aware_start(first_week),
        start_time__lt=_aware_start(current_week),
    ).select_related("resource")

    counts_by_resource_week = Counter()
    counts_by_weekday = Counter()
    for booking in bookings:
        local_start = timezone.localtime(booking.start_time)
        week_start = _start_of_week(local_start.date())
        counts_by_resource_week[(booking.resource_id, week_start)] += 1
        counts_by_weekday[local_start.weekday()] += 1

    resources = []
    for resource in Resource.objects.order_by("name"):
        weekly_counts = [counts_by_resource_week[(resource.id, week)] for week in week_starts]
        recent_counts = weekly_counts[-min(4, weeks):]
        forecast = round(sum(recent_counts) / len(recent_counts), 2) if recent_counts else 0
        resources.append({
            "id": resource.id,
            "name": resource.name,
            "total": sum(weekly_counts),
            "weekly_counts": weekly_counts,
            "forecast": forecast,
        })

    weekday_counts = [counts_by_weekday[index] for index in range(7)]
    busiest_weekday = None
    if any(weekday_counts):
        busiest_index = max(range(7), key=weekday_counts.__getitem__)
        busiest_weekday = {
            "name": WEEKDAY_NAMES[busiest_index],
            "count": weekday_counts[busiest_index],
        }

    return {
        "weeks": weeks,
        "week_labels": [week.strftime("%d/%m") for week in week_starts],
        "resources": resources,
        "weekday_names": list(WEEKDAY_NAMES),
        "weekday_counts": weekday_counts,
        "busiest_weekday": busiest_weekday,
        "total_bookings": sum(weekday_counts),
    }
