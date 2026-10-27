from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Resource(models.Model):
    """Recurso que puede reservarse (pistas, salas, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Datos reutilizables y preferencias no sensibles del cliente."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="reservation_profile")
    phone = models.CharField(max_length=30, blank=True)
    preferred_resource = models.ForeignKey(
        Resource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_by_profiles",
    )
    default_repeat_weeks = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Availability(models.Model):
    """Horarios disponibles para cada recurso."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='availabilities')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.resource.name} - {self.start_time} a {self.end_time}"
    
    class Meta:
        verbose_name = 'Bloqueo'
        verbose_name_plural = 'Bloqueos'


class Booking(models.Model):
    """Reserva de un recurso por un usuario."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva de {self.resource.name} por {self.user.username}"

    def clean(self):
        """
        Validación para evitar que haya reservas solapadas con la misma franja horaria.
        """
        overlapping = Booking.objects.filter(
            resource=self.resource,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)  # Excluimos la propia reserva al editar

        if overlapping.exists():
            raise ValidationError("Ya existe una reserva en esta franja horaria.")

    class Meta:
        unique_together = ('resource', 'start_time', 'end_time')


class BookingCancellation(models.Model):
    """Registro de auditoría conservado después de eliminar una reserva."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booking_cancellations")
    resource_name = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    cancelled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-cancelled_at",)

    def __str__(self):
        return f"Cancelación de {self.resource_name} por {self.user.username}"


class WaitlistEntry(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "En espera"
        NOTIFIED = "notified", "Notificado"
        BOOKED = "booked", "Reserva completada"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="waitlist_entries")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="waitlist_entries")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.WAITING)
    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "resource", "start_time", "end_time"),
                name="unique_waitlist_slot_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user.username} en espera para {self.resource.name}"


class InAppNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Notificación para {self.user.username}"
