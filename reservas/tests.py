from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, Resource


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
