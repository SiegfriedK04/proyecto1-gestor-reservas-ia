from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from reservas.models import Availability, Booking, Resource


class Command(BaseCommand):
    help = "Crea recursos y reservas de prueba para el calendario"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-demo",
            action="store_true",
            help="Elimina y regenera únicamente las reservas del usuario y recurso demostrativos.",
        )

    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            raise CommandError("Los datos demostrativos solo pueden prepararse con DEBUG habilitado.")

        admin, _ = User.objects.get_or_create(username="admin_user")
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("admin1234")
        admin.save()

        demo_users = []
        for username, first_name in (("demo_user", "Sofía"), ("ana_demo", "Ana"), ("luis_demo", "Luis")):
            user, created = User.objects.get_or_create(username=username, defaults={"first_name": first_name})
            if created:
                user.set_password("demo1234")
                user.save()
            demo_users.append(user)

        legacy_resource = Resource.objects.filter(name="Pista Pádel 1").first()
        if legacy_resource and not Resource.objects.filter(name="Cancha de Pádel Bahía").exists():
            legacy_resource.name = "Cancha de Pádel Bahía"
            legacy_resource.description = "Cancha exterior para partidos y entrenamientos de pádel."
            legacy_resource.save(update_fields=("name", "description"))

        resource_specs = (
            ("Cancha de Pádel Bahía", "Cancha exterior para partidos y entrenamientos de pádel."),
            ("Cancha de Tenis Central", "Superficie rápida con iluminación para horarios vespertinos."),
            ("Sala Creativa", "Sala equipada para talleres, reuniones y sesiones colaborativas."),
            ("Auditorio Horizonte", "Espacio para presentaciones, charlas y actividades académicas."),
        )
        resources = [
            Resource.objects.get_or_create(name=name, defaults={"description": description})[0]
            for name, description in resource_specs
        ]

        if kwargs["reset_demo"]:
            Booking.objects.filter(user__in=demo_users).delete()

        today = timezone.localdate()

        def at(day, hour, minute=0):
            return timezone.make_aware(datetime.combine(day, time(hour, minute)))

        future_specs = (
            (0, 0, 1, 10), (1, 1, 1, 14), (2, 2, 1, 16),
            (0, 3, 2, 18), (1, 0, 3, 9), (2, 1, 3, 12),
            (0, 2, 4, 11), (1, 3, 5, 15), (2, 0, 6, 17),
            (0, 1, 7, 10), (1, 2, 8, 13), (2, 3, 9, 18),
        )
        historical_specs = []
        for weeks_ago in range(1, 9):
            week_start = today - timedelta(days=today.weekday(), weeks=weeks_ago)
            for resource_index in range(4):
                for offset in range(1 + ((weeks_ago + resource_index) % 3)):
                    historical_specs.append((
                        (weeks_ago + resource_index + offset) % len(demo_users),
                        resource_index,
                        week_start + timedelta(days=(resource_index + offset) % 5),
                        9 + resource_index + offset,
                    ))

        created_count = 0
        for user_index, resource_index, days_ahead, hour in future_specs:
            start = at(today + timedelta(days=days_ahead), hour)
            _, was_created = Booking.objects.get_or_create(
                user=demo_users[user_index], resource=resources[resource_index],
                start_time=start, end_time=start + timedelta(hours=1),
            )
            created_count += int(was_created)

        for user_index, resource_index, booking_day, hour in historical_specs:
            start = at(booking_day, hour)
            _, was_created = Booking.objects.get_or_create(
                user=demo_users[user_index], resource=resources[resource_index],
                start_time=start, end_time=start + timedelta(hours=1),
            )
            created_count += int(was_created)

        block_start = at(today + timedelta(days=2), 15)
        Availability.objects.get_or_create(
            resource=resources[2],
            start_time=block_start,
            end_time=block_start + timedelta(hours=2),
        )
        self.stdout.write(self.style.SUCCESS(
            f"Datos demo listos. Recursos: {len(resources)}. Reservas nuevas: {created_count}. "
            "Administrador: admin_user / admin1234."
        ))
