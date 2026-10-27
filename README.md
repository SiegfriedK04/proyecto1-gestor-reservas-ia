# Gestor de reservas

Aplicación web desarrollada con **Django** para gestionar reservas de pistas, salas y otros recursos. Incluye calendario interactivo, preferencias de clientes, cancelaciones, previsión de demanda y lista de espera.

---

## **Características principales**

### **Modelos implementados**
- **Resource** – Representa cada recurso o pista disponible (pádel, fútbol, etc.).
- **Booking** – Registra las reservas de usuarios para un recurso.
- **Availability (Bloqueos)** – Define franjas horarias en las que una pista no está disponible (bloqueos administrativos).
- **UserProfile** – Conserva preferencias reutilizables del cliente.
- **WaitlistEntry** – Mantiene el orden y estado de la lista de espera.
- **InAppNotification** – Registra avisos internos para los usuarios.
- **BookingCancellation** – Conserva la auditoría de cancelaciones.
- **User (Autenticación)** – Gestión de usuarios con login/logout.

### **Funcionalidades clave**
- 📅 **Calendario de disponibilidad** con **FullCalendar**.
- ⛔ **Evita solapamientos y bloqueos** tanto en la interfaz como en el servidor.
- 🔁 **Reservas recurrentes atómicas** de hasta 12 semanas.
- 🔒 **Bloqueos de recursos** gestionados desde el panel de administración.
- 👤 **Datos y preferencias reutilizables** por cliente.
- 🧾 **Consulta y cancelación de reservas propias** con política de 24 horas.
- 🔔 **Lista de espera y notificaciones internas** por horarios liberados.
- 📈 **Previsión de demanda administrativa** basada en semanas completas.
- 👨💼 **Panel Django Admin** para gestionar los datos operativos.

---

## **Tecnologías utilizadas**

- **Backend:** Django 5 (Python 3.12)
- **Frontend:** HTML5, CSS3, JavaScript (con integración de FullCalendar)
- **Base de datos:** SQLite (por defecto, fácil de cambiar a MySQL o PostgreSQL)
- **Autenticación:** Sistema de usuarios de Django
- **UI:** Diseño minimalista con **navbar**, cards y calendario interactivo

---

## Calidad y seguridad

El proyecto incluye protección CSRF, aislamiento de datos por usuario, validaciones de servidor, transacciones para recurrencias, auditoría de cancelaciones, pruebas automatizadas y verificación continua mediante GitHub Actions.



## Instalación

### Inicio rápido en Windows

Haz doble clic en `iniciar_app.cmd`. El archivo crea el entorno si hace falta, instala dependencias, aplica migraciones, prepara datos variados y abre el navegador.

Credenciales locales preparadas automáticamente:

- Administración: `admin_user` / `admin1234`
- Cliente de demostración: `demo_user` / `demo1234`

### Inicio manual

1. Clonar y abrir el repositorio:

   ```text
   git clone https://github.com/SiegfriedK04/proyecto1-gestor-reservas-ia.git
   cd proyecto1-gestor-reservas-ia
   ```

2. Crear el entorno virtual:

   ```text
   python -m venv .venv
   ```

3. Activarlo en Windows:

   ```text
   .venv\Scripts\activate
   ```

   En Linux o macOS:

   ```text
   source .venv/bin/activate
   ```

4. Instalar y preparar la aplicación:

   ```text
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Ejecutar las pruebas y el servidor:

   ```text
   python manage.py test
   python manage.py runserver
   ```

La aplicación queda disponible en `http://127.0.0.1:8000/` y el panel administrativo en `http://127.0.0.1:8000/admin/`.

Las variables admitidas para otros entornos se documentan en `.env.example`.

## Datos demostrativos opcionales

```text
python manage.py crear_reservas_demo
```

El comando crea cuatro recursos, tres clientes de ejemplo, reservas futuras visibles, actividad histórica para la previsión y un bloqueo de muestra. Puede ejecutarse varias veces sin duplicar datos. Para regenerar únicamente las reservas demostrativas:

```text
python manage.py crear_reservas_demo --reset-demo
```

Estas credenciales y datos deben usarse solo en desarrollo local.

## Uso de la aplicación

- Desde administración se crean recursos y bloqueos de horario.
- En el inicio se selecciona un recurso para abrir su calendario.
- Un bloque disponible permite crear una reserva única o recurrente.
- Un horario ocupado permite solicitar ingreso a la lista de espera.
- “Mis datos” guarda preferencias no sensibles.
- “Mis reservas” muestra reservas, historial, lista de espera y notificaciones.
- Las cuentas administrativas pueden abrir “Previsión” para analizar demanda por semana, recurso y día.
