# AI Development Log

Solo se registran interacciones que influyen de forma material en el desarrollo. No se presentan simulaciones como evidencia real.

| Fecha | Actividad | Herramienta | Solicitud | Resultado | Decisión humana | Referencia |
|---|---|---|---|---|---|---|
| 2026-10-26 | Auditoría | Codex Desktop | Analizar arquitectura y riesgos antes de modificar | Detectó ausencia de dependencias, pruebas y configuración segura; también señaló CSRF y atomicidad | Aceptar la estabilización; separar seguridad y atomicidad en cambios posteriores | PR de fundación |
| 2026-10-26 | Línea base | Codex Desktop | Ejecutar comprobaciones iniciales | La ejecución falló porque Django no estaba instalado y no existía `requirements.txt` | Crear dependencia fijada, entorno virtual y CI | PR de fundación |
| 2026-10-26 | Datos guardados | Codex Desktop | Diseñar datos reutilizables sin almacenar información de pago sensible | Propuso un perfil uno a uno con teléfono, recurso preferido y repetición predeterminada | Aceptar el perfil; excluir tarjeta y CVV; exigir permisos y límites mediante pruebas | HU1 / PR pendiente |
| 2026-10-26 | Previsión de demanda | Codex Desktop | Diseñar una previsión comprensible usando únicamente las reservas disponibles | Propuso una media móvil sobre semanas completas con desglose semanal y por día | Aceptar una ventana de cuatro semanas; añadir rangos configurables, control de administrador y explicación de limitaciones | HU3 / PR pendiente |
| 2026-10-26 | Pruebas de previsión | Codex Desktop | Ejecutar la suite tras incorporar los casos de demanda | Dos casos fallaron por omitir `datetime` y `time` en las importaciones de las pruebas | Corregir las importaciones y repetir la suite completa antes de publicar | HU3 / PR pendiente |

