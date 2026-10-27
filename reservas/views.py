import json
from datetime import datetime, timedelta, time
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.dateformat import format as date_format
from django.utils.dateparse import parse_datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST
from .demand import build_demand_forecast
from .forms import UserProfileForm
from .models import Availability, Booking, BookingCancellation, Resource, UserProfile


# Horario por defecto (si no hay Availability definida)
DEFAULT_START = time(9, 0)   # 09:00
DEFAULT_END = time(21, 0)    # 21:00


def calendario(request, resource_id):
    """
    Muestra un calendario semanal de reservas para un recurso.
    """
    resource = get_object_or_404(Resource, id=resource_id)

    hoy = datetime.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())  # Lunes
    dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]

    reservas = Booking.objects.filter(
        resource=resource,
        start_time__date__gte=inicio_semana,
        start_time__date__lte=inicio_semana + timedelta(days=6)
    ).order_by('start_time')

    reservas_por_dia = {date_format(dia, 'Y-m-d'): [] for dia in dias_semana}
    for reserva in reservas:
        clave = date_format(reserva.start_time, 'Y-m-d')
        reservas_por_dia[clave].append(reserva)

    return render(request, 'reservas/calendario.html', {
        'resource': resource,
        'dias_semana': dias_semana,
        'reservas_por_dia': reservas_por_dia,
    })


def calendario_navegable(request, resource_id):
    """
    Calendario semanal con botones de semana anterior/siguiente.
    """
    resource = get_object_or_404(Resource, id=resource_id)

    hoy = datetime.today()
    delta = 0
    if request.GET.get('week') == 'prev':
        delta = -7
    elif request.GET.get('week') == 'next':
        delta = 7

    inicio_semana = (hoy - timedelta(days=hoy.weekday())) + timedelta(days=delta)
    dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]

    reservas = Booking.objects.filter(
        resource=resource,
        start_time__date__gte=inicio_semana,
        start_time__date__lte=inicio_semana + timedelta(days=6)
    ).order_by('start_time')

    reservas_por_dia = {date_format(dia, 'Y-m-d'): [] for dia in dias_semana}
    for reserva in reservas:
        clave = date_format(reserva.start_time, 'Y-m-d')
        reservas_por_dia[clave].append(reserva)

    return render(request, 'reservas/calendario.html', {
        'resource': resource,
        'dias_semana': dias_semana,
        'reservas_por_dia': reservas_por_dia,
    })


@ensure_csrf_cookie
def calendario_full(request, resource_id):
    """
    Calendario interactivo con FullCalendar.
    """
    resource = get_object_or_404(Resource, id=resource_id)

    reservas = Booking.objects.filter(resource=resource).order_by('start_time')
    bloqueos = Availability.objects.filter(resource=resource)

    # Lista de reservas
    reservas_json = [
        {
            "start": reserva.start_time.isoformat(),
            "end": reserva.end_time.isoformat(),
            "title": f"Reservado por {reserva.user.username}",
            "color": "#10b981",  # Verde reservas
        }
        for reserva in reservas
    ]

    # Lista de bloqueos (rojo)
    bloqueos_json = [
        {
            "start": bloqueo.start_time.isoformat(),
            "end": bloqueo.end_time.isoformat(),
        }
        for bloqueo in bloqueos
    ]

    default_repeat_weeks = 0
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile:
            default_repeat_weeks = profile.default_repeat_weeks

    return render(request, 'reservas/calendario_full.html', {
        'resource': resource,
        'reservas_json': json.dumps(reservas_json),
        'bloqueos_json': json.dumps(bloqueos_json),
        'is_authenticated': request.user.is_authenticated,
        'default_repeat_weeks': default_repeat_weeks,
    })



@require_POST
def api_crear_reserva(request):
    """
    Endpoint para crear una nueva reserva, con soporte para repeticiones semanales.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Debes iniciar sesión para reservar.'}, status=403)

    try:
        data = json.loads(request.body)
        resource_id = int(data.get('resource_id'))
        start_time = parse_datetime(data.get('start_time', ''))
        end_time = parse_datetime(data.get('end_time', ''))
        repeat_weeks = int(data.get('repeat_weeks', 0))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'error': 'Los datos de la reserva no son válidos.'}, status=400)

    if start_time is None or end_time is None or start_time >= end_time:
        return JsonResponse({'success': False, 'error': 'El intervalo de la reserva no es válido.'}, status=400)
    if timezone.is_naive(start_time):
        start_time = timezone.make_aware(start_time)
    if timezone.is_naive(end_time):
        end_time = timezone.make_aware(end_time)
    if start_time <= timezone.now():
        return JsonResponse({'success': False, 'error': 'La reserva debe comenzar en el futuro.'}, status=400)
    if repeat_weeks < 0 or repeat_weeks > 12:
        return JsonResponse({'success': False, 'error': 'La repetición debe estar entre 0 y 12 semanas.'}, status=400)

    occurrences = [
        (start_time + timedelta(weeks=index), end_time + timedelta(weeks=index))
        for index in range(repeat_weeks + 1)
    ]

    with transaction.atomic():
        try:
            resource = Resource.objects.select_for_update().get(id=resource_id)
        except Resource.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'El recurso solicitado no existe.'}, status=404)

        for index, (start, end) in enumerate(occurrences, start=1):
            if Availability.objects.filter(
                resource=resource,
                start_time__lt=end,
                end_time__gt=start,
            ).exists():
                return JsonResponse({
                    'success': False,
                    'error': f'La semana {index} coincide con un horario bloqueado.',
                }, status=409)
            if Booking.objects.filter(
                resource=resource,
                start_time__lt=end,
                end_time__gt=start,
            ).exists():
                return JsonResponse({
                    'success': False,
                    'error': f'La semana {index} coincide con una reserva existente.',
                }, status=409)

        bookings = Booking.objects.bulk_create([
            Booking(
                user=request.user,
                resource=resource,
                start_time=start,
                end_time=end,
            )
            for start, end in occurrences
        ])

    return JsonResponse({
        'success': True,
        'reservas': [
            {'id': booking.id, 'start': booking.start_time.isoformat(), 'end': booking.end_time.isoformat()}
            for booking in bookings
        ],
    }, status=201)


def login_view(request):
    """
    Vista para el inicio de sesión de usuarios.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, 'reservas/login.html')


def logout_view(request):
    """
    Cerrar sesión.
    """
    logout(request)
    return redirect('/login/')


@login_required
def profile_view(request):
    """Permite al cliente administrar datos reutilizables y preferencias."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos y preferencias fueron actualizados.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "reservas/profile.html", {"form": form})


@staff_member_required(login_url="login")
def demand_forecast(request):
    """Panel administrativo de demanda histórica y previsión semanal."""
    try:
        weeks = int(request.GET.get("weeks", 8))
    except (TypeError, ValueError):
        weeks = 8
    weeks = min(max(weeks, 4), 52)
    report = build_demand_forecast(weeks=weeks)
    report["resource_datasets"] = [
        {"label": resource["name"], "data": resource["weekly_counts"]}
        for resource in report["resources"]
    ]
    return render(request, "reservas/demand_forecast.html", report)


@login_required
def my_bookings(request):
    """Lista las reservas del usuario sin exponer las de otras cuentas."""
    now = timezone.now()
    bookings = Booking.objects.filter(user=request.user).select_related("resource")
    return render(request, "reservas/my_bookings.html", {
        "upcoming_bookings": bookings.filter(start_time__gt=now).order_by("start_time"),
        "past_bookings": bookings.filter(start_time__lte=now).order_by("-start_time")[:10],
        "cancellation_deadline": now + timedelta(hours=24),
    })


@login_required
@require_POST
def cancel_booking(request, booking_id):
    """Cancela una reserva propia si faltan al menos 24 horas para su inicio."""
    booking = get_object_or_404(
        Booking.objects.select_related("resource"),
        id=booking_id,
        user=request.user,
    )
    if booking.start_time < timezone.now() + timedelta(hours=24):
        messages.error(request, "La reserva solo puede cancelarse con al menos 24 horas de anticipación.")
        return redirect("my_bookings")

    with transaction.atomic():
        BookingCancellation.objects.create(
            user=request.user,
            resource_name=booking.resource.name,
            start_time=booking.start_time,
            end_time=booking.end_time,
        )
        booking.delete()
    messages.success(request, "La reserva fue cancelada correctamente.")
    return redirect("my_bookings")

def api_reservas(request, resource_id):
    """
    API que devuelve todas las reservas de un recurso en formato JSON.
    """
    reservas = Booking.objects.filter(resource_id=resource_id).order_by('start_time')
    eventos = [
        {
            "title": f"Reservado por {reserva.user.username}",
            "start": reserva.start_time.isoformat(),
            "end": reserva.end_time.isoformat(),
            "color": "#10b981",  # Verde
        }
        for reserva in reservas
    ]
    return JsonResponse(eventos, safe=False)

def home(request):
    """
    Vista principal que muestra todas las pistas (resources).
    """
    resources = Resource.objects.all()  # Obtenemos todas las pistas
    preferred_resource_id = None
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
        if profile:
            preferred_resource_id = profile.preferred_resource_id
    return render(request, 'reservas/home.html', {
        'resources': resources,
        'preferred_resource_id': preferred_resource_id,
    })


