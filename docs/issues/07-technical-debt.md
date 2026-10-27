## Problemas detectados

1. `api_crear_reserva` usa `csrf_exempt`.
2. Una reserva recurrente puede crear semanas iniciales antes de encontrar un conflicto posterior.
3. La validación de bloqueos administrativos ocurre en JavaScript, pero no está garantizada por el backend.

## Resultado esperado

- Restaurar protección CSRF.
- Crear reservas recurrentes dentro de una transacción atómica.
- Validar reservas y bloqueos en el backend.
- Agregar pruebas que fallen antes del cambio y pasen después.

Este trabajo debe ir en un PR separado de las historias funcionales.

