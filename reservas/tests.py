from datetime import datetime, time, timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Availability,
    Booking,
    BookingCancellation,
    InAppNotification,
    Resource,
    UserProfile,
    WaitlistEntry,
)
from .demand import build_demand_forecast


class ReservationBaselineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cliente", password="segura-123")
        self.resource = Resource.objects.create(
            name="Sala Norte",
            description="Sala de reuniones",
        )
        self.start = timezone.now() + timedelta(days=1)
        self.end = self.start + timedelta(hours=1)

    def test_home_lists_existing_resources(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sala Norte")

    def test_home_filters_resources_by_name(self):
        Resource.objects.create(name="Cancha Sur", description="Pista")

        response = self.client.get(reverse("home"), {"buscar": "nOrTe"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sala Norte")
        self.assertNotContains(response, "Cancha Sur")

    def test_home_shows_message_when_resource_search_has_no_matches(self):
        response = self.client.get(reverse("home"), {"buscar": "Auditorio"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se encontraron recursos con ese nombre.")

    def test_booking_validation_rejects_overlap(self):
        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=self.start,
            end_time=self.end,
        )
        overlapping = Booking(
            user=self.user,
            resource=self.resource,
            start_time=self.start + timedelta(minutes=30),
            end_time=self.end + timedelta(minutes=30),
        )

        with self.assertRaises(ValidationError):
            overlapping.full_clean()

    def test_booking_api_requires_authentication(self):
        response = self.client.post(
            reverse("api_crear_reserva"),
            data={
                "resource_id": self.resource.id,
                "start_time": self.start.isoformat(),
                "end_time": self.end.isoformat(),
                "repeat_weeks": 0,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])

    def test_events_api_returns_created_booking(self):
        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=self.start,
            end_time=self.end,
        )

        response = self.client.get(reverse("api_reservas", args=[self.resource.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Ocupado")


class ReservationIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cliente-integridad", password="segura-123")
        self.resource = Resource.objects.create(name="Sala Segura")
        self.start = timezone.now() + timedelta(days=10)
        self.end = self.start + timedelta(hours=1)

    def payload(self, **overrides):
        data = {
            "resource_id": self.resource.id,
            "start_time": self.start.isoformat(),
            "end_time": self.end.isoformat(),
            "repeat_weeks": 0,
        }
        data.update(overrides)
        return data

    def test_api_enforces_csrf_for_authenticated_user(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username="cliente-integridad", password="segura-123")

        response = client.post(
            reverse("api_crear_reserva"),
            data=self.payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Booking.objects.exists())


    def test_calendar_provides_csrf_cookie_and_valid_token_creates_booking(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username="cliente-integridad", password="segura-123")
        client.get(reverse("calendario_full", args=[self.resource.id]))
        token = client.cookies["csrftoken"].value

        response = client.post(
            reverse("api_crear_reserva"),
            data=self.payload(),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Booking.objects.count(), 1)

    def test_valid_booking_creates_in_app_confirmation(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("api_crear_reserva"),
            data=self.payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        notification = InAppNotification.objects.get(user=self.user)
        self.assertEqual(notification.message, "Reserva confirmada: 1 horario para Sala Segura.")
        self.assertEqual(
            notification.link,
            reverse("calendario_full", args=[self.resource.id]),
        )

    def test_rejected_booking_does_not_create_confirmation(self):
        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=self.start,
            end_time=self.end,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("api_crear_reserva"),
            data=self.payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertFalse(InAppNotification.objects.exists())

    def test_recurring_booking_creates_one_grouped_confirmation(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("api_crear_reserva"),
            data=self.payload(repeat_weeks=2),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Booking.objects.count(), 3)
        self.assertEqual(InAppNotification.objects.filter(user=self.user).count(), 1)
        self.assertEqual(
            InAppNotification.objects.get(user=self.user).message,
            "Reservas confirmadas: 3 horarios para Sala Segura.",
        )

    def test_recurring_booking_is_atomic_when_later_week_conflicts(self):
        Booking.objects.create(
            user=self.user,
            resource=self.resource,
            start_time=self.start + timedelta(weeks=1),
            end_time=self.end + timedelta(weeks=1),
        )
        self.client.login(username="cliente-integridad", password="segura-123")

        response = self.client.post(
            reverse("api_crear_reserva"),
            data=self.payload(repeat_weeks=2),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertFalse(Booking.objects.filter(start_time=self.start).exists())

    def test_backend_rejects_administratively_blocked_interval(self):
        Availability.objects.create(
            resource=self.resource,
            start_time=self.start - timedelta(minutes=30),
            end_time=self.end + timedelta(minutes=30),
        )
        self.client.login(username="cliente-integridad", password="segura-123")

        response = self.client.post(
            reverse("api_crear_reserva"),
            data=self.payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertFalse(Booking.objects.exists())
        self.assertIn("bloqueado", response.json()["error"])

    def test_api_rejects_invalid_interval_and_repeat_limit(self):
        self.client.login(username="cliente-integridad", password="segura-123")

        invalid_interval = self.client.post(
            reverse("api_crear_reserva"),
            data=self.payload(end_time=self.start.isoformat()),
            content_type="application/json",
        )
        invalid_repeat = self.client.post(
            reverse("api_crear_reserva"),
            data=self.payload(repeat_weeks=13),
            content_type="application/json",
        )

        self.assertEqual(invalid_interval.status_code, 400)
        self.assertEqual(invalid_repeat.status_code, 400)
        self.assertFalse(Booking.objects.exists())


class CalendarAvailabilityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="propietario", password="segura-123")
        self.viewer = User.objects.create_user(username="visitante", password="segura-456")
        self.resource = Resource.objects.create(name="Cancha Calendario")
        self.start = timezone.now() + timedelta(days=5)
        self.booking = Booking.objects.create(
            user=self.owner,
            resource=self.resource,
            start_time=self.start,
            end_time=self.start + timedelta(hours=1),
        )
        self.block = Availability.objects.create(
            resource=self.resource,
            start_time=self.start + timedelta(hours=2),
            end_time=self.start + timedelta(hours=3),
        )

    def test_events_endpoint_combines_bookings_and_blocks(self):
        response = self.client.get(reverse("api_reservas", args=[self.resource.id]))

        self.assertEqual(response.status_code, 200)
        events = response.json()
        self.assertEqual(len(events), 2)
        self.assertEqual({event["extendedProps"]["status"] for event in events}, {"booking", "blocked"})
        self.assertEqual({event["color"] for event in events}, {"#2563eb", "#dc2626"})

    def test_event_titles_do_not_expose_other_users(self):
        self.client.login(username="visitante", password="segura-456")

        response = self.client.get(reverse("api_reservas", args=[self.resource.id]))

        content = response.content.decode()
        self.assertNotIn("propietario", content)
        self.assertEqual(response.json()[0]["title"], "Ocupado")

    def test_owner_can_identify_own_booking(self):
        self.client.login(username="propietario", password="segura-123")

        response = self.client.get(reverse("api_reservas", args=[self.resource.id]))

        booking_event = next(event for event in response.json() if event["extendedProps"]["status"] == "booking")
        self.assertEqual(booking_event["title"], "Mi reserva")
        self.assertTrue(booking_event["extendedProps"]["owned"])

    def test_calendar_contains_legend_navigation_and_dynamic_refresh(self):
        response = self.client.get(reverse("calendario_full", args=[self.resource.id]))

        self.assertContains(response, "Estados de disponibilidad")
        self.assertContains(response, "resource-selector")
        self.assertContains(response, "calendar.refetchEvents()")
        self.assertContains(response, reverse("api_reservas", args=[self.resource.id]))


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="carlos", password="segura-123")
        self.other_user = User.objects.create_user(username="otro", password="segura-456")
        self.resource = Resource.objects.create(name="Pista Central")

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_user_can_save_reusable_profile_data(self):
        self.client.login(username="carlos", password="segura-123")

        response = self.client.post(reverse("profile"), {
            "phone": "+507 6000-1234",
            "preferred_resource": self.resource.id,
            "default_repeat_weeks": 3,
        })

        self.assertRedirects(response, reverse("profile"))
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.phone, "+507 6000-1234")
        self.assertEqual(profile.preferred_resource, self.resource)
        self.assertEqual(profile.default_repeat_weeks, 3)

    def test_profile_rejects_excessive_default_repetition(self):
        self.client.login(username="carlos", password="segura-123")

        response = self.client.post(reverse("profile"), {
            "phone": "",
            "preferred_resource": "",
            "default_repeat_weeks": 13,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se pueden preseleccionar más de 12 semanas")

    def test_calendar_uses_authenticated_users_default_repetition(self):
        UserProfile.objects.create(
            user=self.user,
            preferred_resource=self.resource,
            default_repeat_weeks=4,
        )
        self.client.login(username="carlos", password="segura-123")

        response = self.client.get(reverse("calendario_full", args=[self.resource.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-default-repeat-weeks="4"')


class RegistrationTests(TestCase):
    def test_registration_page_uses_shared_responsive_form(self):
        response = self.client.get(reverse("register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Crea tu perfil de cliente")
        self.assertContains(response, 'class="form-grid"')

    def test_user_can_create_account_and_is_logged_in(self):
        response = self.client.post(reverse("register"), {
            "username": "nuevo_cliente",
            "first_name": "María",
            "last_name": "López",
            "email": "CLIENTE@EXAMPLE.COM",
            "password1": "Reserva-Segura-2026!",
            "password2": "Reserva-Segura-2026!",
        })

        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(username="nuevo_cliente")
        self.assertEqual(user.email, "cliente@example.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(username="existente", email="cliente@example.com", password="segura-123")

        response = self.client.post(reverse("register"), {
            "username": "otro_cliente",
            "first_name": "Otro",
            "last_name": "Cliente",
            "email": "Cliente@Example.com",
            "password1": "Reserva-Segura-2026!",
            "password2": "Reserva-Segura-2026!",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe una cuenta con este correo electrónico")
        self.assertFalse(User.objects.filter(username="otro_cliente").exists())

    def test_login_ignores_external_redirect(self):
        User.objects.create_user(username="cliente", password="segura-123")

        response = self.client.post(reverse("login"), {
            "username": "cliente",
            "password": "segura-123",
            "next": "https://example.com/externo",
        })

        self.assertRedirects(response, reverse("home"))


class DemandForecastTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="gabriel",
            password="segura-789",
            is_staff=True,
        )
        self.customer = User.objects.create_user(username="cliente", password="segura-123")
        self.resource = Resource.objects.create(name="Sala Ejecutiva")

    def create_booking(self, weeks_ago, weekday=0):
        current_week = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        booking_day = current_week - timedelta(weeks=weeks_ago) + timedelta(days=weekday)
        start = timezone.make_aware(datetime.combine(booking_day, time(10, 0)))
        return Booking.objects.create(
            user=self.customer,
            resource=self.resource,
            start_time=start,
            end_time=start + timedelta(hours=1),
        )

    def test_forecast_uses_last_four_complete_weeks(self):
        self.create_booking(1)
        self.create_booking(2)
        self.create_booking(2, weekday=1)
        self.create_booking(4)

        report = build_demand_forecast(weeks=8)

        resource = report["resources"][0]
        self.assertEqual(resource["total"], 4)
        self.assertEqual(resource["weekly_counts"][-4:], [1, 0, 2, 1])
        self.assertEqual(resource["forecast"], 1.0)

    def test_forecast_identifies_busiest_weekday(self):
        self.create_booking(1, weekday=2)
        self.create_booking(2, weekday=2)
        self.create_booking(3, weekday=4)

        report = build_demand_forecast(weeks=4)

        self.assertEqual(report["busiest_weekday"], {"name": "Miércoles", "count": 2})

    def test_forecast_page_rejects_non_staff_user(self):
        self.client.login(username="cliente", password="segura-123")

        response = self.client.get(reverse("demand_forecast"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_forecast_page_accepts_staff_and_limits_range(self):
        self.client.login(username="gabriel", password="segura-789")

        response = self.client.get(reverse("demand_forecast"), {"weeks": 100})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["weeks"], 52)
        self.assertContains(response, "promedio de reservas de las últimas cuatro semanas")


class MyBookingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="carlos", password="segura-123")
        self.other_user = User.objects.create_user(username="otro", password="segura-456")
        self.resource = Resource.objects.create(name="Cancha Sur")
        self.client.login(username="carlos", password="segura-123")

    def create_booking(self, user, hours_from_now):
        start = timezone.now() + timedelta(hours=hours_from_now)
        return Booking.objects.create(
            user=user,
            resource=self.resource,
            start_time=start,
            end_time=start + timedelta(hours=1),
        )

    def test_page_only_lists_authenticated_users_bookings(self):
        own = self.create_booking(self.user, 72)
        other = self.create_booking(self.other_user, 96)

        response = self.client.get(reverse("my_bookings"))

        self.assertContains(response, reverse("cancel_booking", args=[own.id]))
        self.assertNotContains(response, reverse("cancel_booking", args=[other.id]))

    def test_user_can_cancel_eligible_booking_and_audit_is_kept(self):
        booking = self.create_booking(self.user, 48)

        response = self.client.post(reverse("cancel_booking", args=[booking.id]))

        self.assertRedirects(response, reverse("my_bookings"))
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())
        cancellation = BookingCancellation.objects.get(user=self.user)
        self.assertEqual(cancellation.resource_name, "Cancha Sur")
        self.assertEqual(cancellation.start_time, booking.start_time)

    def test_user_cannot_cancel_another_users_booking(self):
        booking = self.create_booking(self.other_user, 48)

        response = self.client.post(reverse("cancel_booking", args=[booking.id]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Booking.objects.filter(id=booking.id).exists())

    def test_booking_inside_24_hours_cannot_be_cancelled(self):
        booking = self.create_booking(self.user, 12)

        response = self.client.post(reverse("cancel_booking", args=[booking.id]), follow=True)

        self.assertTrue(Booking.objects.filter(id=booking.id).exists())
        self.assertFalse(BookingCancellation.objects.exists())
        self.assertContains(response, "al menos 24 horas de anticipación")

    def test_past_booking_cannot_be_cancelled(self):
        booking = self.create_booking(self.user, -2)

        response = self.client.post(reverse("cancel_booking", args=[booking.id]))

        self.assertRedirects(response, reverse("my_bookings"))
        self.assertTrue(Booking.objects.filter(id=booking.id).exists())
        self.assertFalse(BookingCancellation.objects.exists())

    def test_cancellation_only_accepts_post(self):
        booking = self.create_booking(self.user, 48)

        response = self.client.get(reverse("cancel_booking", args=[booking.id]))

        self.assertEqual(response.status_code, 405)


class WaitlistTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="titular", password="segura-123")
        self.first = User.objects.create_user(username="primero", password="segura-456")
        self.second = User.objects.create_user(username="segundo", password="segura-789")
        self.resource = Resource.objects.create(name="Cancha Lista")
        self.start = timezone.now() + timedelta(days=5)
        self.end = self.start + timedelta(hours=1)
        self.booking = Booking.objects.create(
            user=self.owner,
            resource=self.resource,
            start_time=self.start,
            end_time=self.end,
        )

    def payload(self):
        return {
            "resource_id": self.resource.id,
            "start_time": self.start.isoformat(),
            "end_time": self.end.isoformat(),
        }

    def join_as(self, username, password):
        self.client.login(username=username, password=password)
        response = self.client.post(
            reverse("join_waitlist"),
            data=self.payload(),
            content_type="application/json",
        )
        self.client.logout()
        return response

    def test_waitlist_requires_authentication(self):
        response = self.client.post(
            reverse("join_waitlist"),
            data=self.payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(WaitlistEntry.objects.exists())

    def test_waitlist_rejects_past_slot(self):
        self.client.force_login(self.first)
        past_start = timezone.now() - timedelta(hours=2)
        past_end = past_start + timedelta(hours=1)

        response = self.client.post(
            reverse("join_waitlist"),
            data={
                "resource_id": self.resource.id,
                "start_time": past_start.isoformat(),
                "end_time": past_end.isoformat(),
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "El horario ya pasó.")
        self.assertFalse(WaitlistEntry.objects.exists())

    def test_user_cannot_join_same_slot_twice(self):
        first_response = self.join_as("primero", "segura-456")
        second_response = self.join_as("primero", "segura-456")

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(WaitlistEntry.objects.count(), 1)

    def test_cancellation_notifies_first_waiting_user(self):
        self.join_as("primero", "segura-456")
        self.join_as("segundo", "segura-789")
        self.client.login(username="titular", password="segura-123")

        response = self.client.post(reverse("cancel_booking", args=[self.booking.id]))

        self.assertRedirects(response, reverse("my_bookings"))
        first_entry = WaitlistEntry.objects.get(user=self.first)
        second_entry = WaitlistEntry.objects.get(user=self.second)
        self.assertEqual(first_entry.status, WaitlistEntry.Status.NOTIFIED)
        self.assertEqual(second_entry.status, WaitlistEntry.Status.WAITING)
        self.assertIsNotNone(first_entry.notified_at)
        self.assertTrue(InAppNotification.objects.filter(user=self.first).exists())
        self.assertFalse(InAppNotification.objects.filter(user=self.second).exists())

    def test_notified_user_has_priority_for_released_slot(self):
        WaitlistEntry.objects.create(
            user=self.first,
            resource=self.resource,
            start_time=self.start,
            end_time=self.end,
            status=WaitlistEntry.Status.NOTIFIED,
            notified_at=timezone.now(),
        )
        self.booking.delete()
        self.client.login(username="segundo", password="segura-789")
        reservation_payload = {**self.payload(), "repeat_weeks": 0}

        response = self.client.post(
            reverse("api_crear_reserva"),
            data=reservation_payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertFalse(Booking.objects.exists())

    def test_notified_user_can_reserve_and_entry_is_completed(self):
        entry = WaitlistEntry.objects.create(
            user=self.first,
            resource=self.resource,
            start_time=self.start,
            end_time=self.end,
            status=WaitlistEntry.Status.NOTIFIED,
            notified_at=timezone.now(),
        )
        self.booking.delete()
        self.client.login(username="primero", password="segura-456")
        reservation_payload = {**self.payload(), "repeat_weeks": 0}

        response = self.client.post(
            reverse("api_crear_reserva"),
            data=reservation_payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        entry.refresh_from_db()
        self.assertEqual(entry.status, WaitlistEntry.Status.BOOKED)
        self.assertTrue(Booking.objects.filter(user=self.first).exists())


@override_settings(DEBUG=True)
class DemoDataCommandTests(TestCase):
    def test_demo_command_is_idempotent(self):
        call_command("crear_reservas_demo", stdout=StringIO())
        first_count = Booking.objects.filter(user__username__in=("demo_user", "ana_demo", "luis_demo")).count()
        call_command("crear_reservas_demo", stdout=StringIO())

        self.assertGreater(first_count, 20)
        self.assertEqual(
            Booking.objects.filter(user__username__in=("demo_user", "ana_demo", "luis_demo")).count(),
            first_count,
        )
        self.assertEqual(Resource.objects.filter(name__in=(
            "Cancha de Pádel Bahía", "Cancha de Tenis Central", "Sala Creativa", "Auditorio Horizonte",
        )).count(), 4)
        admin = User.objects.get(username="admin_user")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("admin1234"))

    def test_demo_reset_preserves_unrelated_bookings(self):
        user = User.objects.create_user(username="real", password="segura-123")
        resource = Resource.objects.create(name="Sala Real")
        start = timezone.now() + timedelta(days=2)
        booking = Booking.objects.create(
            user=user,
            resource=resource,
            start_time=start,
            end_time=start + timedelta(hours=1),
        )

        call_command("crear_reservas_demo", reset_demo=True, stdout=StringIO())

        self.assertTrue(Booking.objects.filter(id=booking.id).exists())
