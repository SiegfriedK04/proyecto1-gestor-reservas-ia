from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, Resource, UserProfile


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
