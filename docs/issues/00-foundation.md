## Objetivo

Estabilizar la instalación, configuración y validación automatizada antes de implementar historias funcionales.

## Alcance

- Dependencias reproducibles y entorno documentado.
- Configuración mediante variables de entorno.
- Exclusión de SQLite, secretos y archivos compilados.
- Pruebas de línea base.
- GitHub Actions.
- Plan del equipo, QA de David y registro de IA.

## Criterios de aceptación

- [ ] `python manage.py check` termina sin errores.
- [ ] No existen migraciones pendientes.
- [ ] Las pruebas automatizadas pasan localmente y en GitHub Actions.
- [ ] Carlos revisa el PR.
- [ ] David cuenta con un plan de QA ejecutable sin GitHub.

## Roles

- Developer: Gabriel Rodriguez.
- Reviewer: Carlos Jaen.
- QA: David Ortega.

