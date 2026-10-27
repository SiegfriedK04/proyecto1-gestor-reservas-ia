# Auditoría de la línea base

Fecha: 26 de octubre de 2026

## Arquitectura encontrada

- Django 5.2.4 con una aplicación llamada `reservas`.
- SQLite como base de datos local.
- Modelos principales: `Resource`, `Booking` y `Availability`.
- Autenticación mediante usuarios de Django.
- FullCalendar para mostrar reservas y bloqueos.
- Endpoints JSON para consultar y crear reservas.

## Funcionalidades existentes

- Listado de recursos.
- Inicio y cierre de sesión.
- Calendario semanal interactivo.
- Reservas únicas y recurrentes.
- Validación básica de solapamientos.
- Bloqueos administrativos.

## Hallazgos iniciales

1. El README menciona `requirements.txt`, pero el archivo no existía.
2. No había `.gitignore` y la base SQLite estaba versionada.
3. `reservas/tests.py` no contenía pruebas.
4. La clave de Django estaba escrita directamente en `settings.py`.
5. La configuración repetía `INSTALLED_APPS`.
6. El idioma y la zona horaria no correspondían al contexto del equipo.
7. El endpoint de creación usa `csrf_exempt`; se revisará en una historia posterior para no mezclar seguridad con la línea base.
8. La creación recurrente no es atómica: un conflicto tardío puede dejar reservas parciales. Se registrará como deuda técnica.

## Decisión humana

El equipo decidió estabilizar instalación, configuración, pruebas y CI antes de comenzar las historias funcionales. Los puntos 7 y 8 quedan documentados para cambios separados y revisables.

