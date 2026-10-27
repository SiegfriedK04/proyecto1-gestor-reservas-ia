from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, Resource, UserProfile
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
        self.assertEqual(response.json()[0]["title"], "Reservado por cliente")


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
