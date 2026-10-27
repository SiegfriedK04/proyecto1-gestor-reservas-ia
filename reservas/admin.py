from django.contrib import admin
from .models import Availability, Booking, Resource, UserProfile

# --- CONFIGURACIÓN DEL PANEL ADMIN ---

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')  # Columnas que veremos en el admin
    search_fields = ('name',)                     # Buscar recursos por nombre


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'resource', 'start_time', 'end_time')
    list_filter = ('resource',)                   # Filtro por recurso
    search_fields = ('resource__name',)
    verbose_name = 'Bloqueo'
    verbose_name_plural = 'Bloqueos'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'resource', 'start_time', 'end_time', 'created_at')
    list_filter = ('resource', 'user')
    search_fields = ('user__username', 'resource__name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "preferred_resource", "default_repeat_weeks")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone")
    list_filter = ("preferred_resource",)
