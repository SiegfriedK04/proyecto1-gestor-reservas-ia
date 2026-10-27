from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from datetime import timedelta

from reservas.models import Booking, Resource


class Command(BaseCommand):
    help = "Crea recursos y reservas de prueba para el calendario"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-demo",
            action="store_true",
            help="Elimina y regenera únicamente las reservas del usuario y recurso demostrativos.",
        )

    def handle(self, *args, **kwargs):
        user, created = User.objects.get_or_create(username='demo_user')
        if created:
            user.set_password('demo1234')
            user.save()
            self.stdout.write(self.style.SUCCESS("Usuario demo_user creado."))

        recurso, creado = Resource.objects.get_or_create(name='Pista Pádel 1', defaults={'description': 'Pista de pádel exterior'})
        if creado:
            self.stdout.write(self.style.SUCCESS("Recurso Pista Pádel 1 creado."))

        if kwargs["reset_demo"]:
            Booking.objects.filter(user=user, resource=recurso).delete()

        hoy = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        created_count = 0

        for i in range(5):
            for j in range(3):
                inicio = hoy + timedelta(days=i, hours=j * 2)
                fin = inicio + timedelta(hours=1)
                _, booking_created = Booking.objects.get_or_create(
                    user=user,
                    resource=recurso,
                    start_time=inicio,
                    end_time=fin,
                )
                created_count += int(booking_created)
        self.stdout.write(self.style.SUCCESS(f"Datos demo listos. Reservas nuevas: {created_count}."))
