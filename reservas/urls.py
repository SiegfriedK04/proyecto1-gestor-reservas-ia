from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Página principal
    path('calendario/<int:resource_id>/', views.calendario, name='calendario'),
    path('calendario_full/<int:resource_id>/', views.calendario_full, name='calendario_full'),
    path('api/reservas/<int:resource_id>/', views.api_reservas, name='api_reservas'),
    path('api/reservas/crear/', views.api_crear_reserva, name='api_crear_reserva'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.profile_view, name='profile'),
    path('administracion/prevision-demanda/', views.demand_forecast, name='demand_forecast'),
    path('mis-reservas/', views.my_bookings, name='my_bookings'),
    path('mis-reservas/<int:booking_id>/cancelar/', views.cancel_booking, name='cancel_booking'),
    path('api/lista-espera/', views.join_waitlist, name='join_waitlist'),



]
