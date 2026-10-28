# 📅 Gestor de Reservas

<p align="center">
  Aplicación web para consultar disponibilidad, reservar recursos y administrar horarios desde un calendario interactivo.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/Django-5.2.4-092E20?logo=django&logoColor=white" alt="Django 5.2.4" />
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Tests-47%20passing-success" alt="47 pruebas aprobadas" />
  <a href="https://github.com/SiegfriedK04/proyecto1-gestor-reservas-ia/actions/workflows/tests.yml">
    <img src="https://github.com/SiegfriedK04/proyecto1-gestor-reservas-ia/actions/workflows/tests.yml/badge.svg" alt="Pruebas Django" />
  </a>
</p>

---

## 🚀 Descripción

**Gestor de Reservas** centraliza la disponibilidad de pistas, salas, auditorios y otros recursos compartidos. Los clientes pueden crear una cuenta, buscar recursos, consultar su calendario, realizar reservas únicas o recurrentes y administrar sus horarios desde una interfaz adaptable.

La aplicación también incorpora bloqueos administrativos, cancelaciones auditadas, lista de espera, notificaciones internas y una previsión de demanda para el personal autorizado.

Repositorio: [github.com/SiegfriedK04/proyecto1-gestor-reservas-ia](https://github.com/SiegfriedK04/proyecto1-gestor-reservas-ia)

---

## ✨ Funcionalidades principales

### Experiencia del cliente

- 🔎 **Búsqueda de recursos** por coincidencia parcial del nombre.
- 📅 **Calendario interactivo** con vistas de semana y día mediante FullCalendar.
- 🟢 **Disponibilidad centralizada** para reservas, bloqueos y horarios ocupados.
- 🔁 **Reservas recurrentes atómicas** de hasta 12 semanas.
- ⛔ **Prevención de solapamientos** y validación de bloqueos desde el servidor.
- 👤 **Registro, autenticación y preferencias** reutilizables por cliente.
- 🧾 **Consulta y cancelación de reservas propias** con una política de 24 horas.
- 🔔 **Confirmaciones y notificaciones internas**, con control de estado leído.
- ⏳ **Lista de espera priorizada** para horarios ocupados.
- 📈 **Previsión administrativa de demanda** basada en semanas completas.
- 📱 **Diseño adaptable** para computadoras, tabletas y dispositivos móviles.
- 👨💼 **Panel Django Admin** para gestionar los datos operativos.

---

## 🧰 Tecnologías utilizadas

| Área | Tecnología |
|---|---|
| Backend | Python 3.12 y Django 5.2.4 |
| Frontend | HTML5, CSS3 y JavaScript |
| Calendario | FullCalendar |
| Iconografía | Lucide |
| Base de datos | SQLite |
| Autenticación | Sistema de usuarios y sesiones de Django |
| Pruebas | Django TestCase |
| Integración continua | GitHub Actions |

---

## 📦 Requisitos previos

Antes de ejecutar el proyecto, asegúrate de tener instalado:

- [Python 3.12](https://www.python.org/downloads/) o una versión compatible con Django 5.2.
- `pip`, incluido normalmente con Python.
- Git, si deseas clonar el repositorio desde GitHub.

SQLite no requiere una instalación adicional.

---

## ⚡ Inicio rápido en Windows

1. Clona o descarga el repositorio.
2. Abre la carpeta del proyecto.
3. Haz doble clic en `iniciar_app.cmd`.

El iniciador crea el entorno virtual si hace falta, instala las dependencias, aplica las migraciones, regenera los datos de demostración y abre el navegador.

La aplicación queda disponible en [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## ⚙️ Instalación manual

### 1. Clonar el repositorio

```bash
git clone https://github.com/SiegfriedK04/proyecto1-gestor-reservas-ia.git
cd proyecto1-gestor-reservas-ia
```

### 2. Crear el entorno virtual

```bash
python -m venv .venv
```

### 3. Activar el entorno

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

En Windows CMD:

```bat
.venv\Scripts\activate.bat
```

En Linux o macOS:

```bash
source .venv/bin/activate
```

### 4. Instalar dependencias y preparar la base de datos

```bash
pip install -r requirements.txt
python manage.py migrate
```

### 5. Preparar datos demostrativos

```bash
python manage.py crear_reservas_demo
```

### 6. Iniciar el servidor

```bash
python manage.py runserver
```

---

## 🔐 Configuración del entorno

El proyecto incluye `.env.example` como referencia:

```env
DJANGO_SECRET_KEY=replace-this-in-non-local-environments
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

| Variable | Descripción |
|---|---|
| `DJANGO_SECRET_KEY` | Clave criptográfica de Django. Debe cambiarse fuera del entorno local. |
| `DJANGO_DEBUG` | Activa o desactiva el modo de depuración. |
| `DJANGO_ALLOWED_HOSTS` | Lista de dominios o direcciones permitidas, separadas por comas. |

> Los datos demostrativos solo pueden generarse cuando `DJANGO_DEBUG=True`.

---

## 🧪 Datos de demostración

El comando crea cuatro recursos, tres clientes, reservas futuras, historial para la previsión de demanda y un bloqueo administrativo:

```bash
python manage.py crear_reservas_demo
```

Puede ejecutarse varias veces sin duplicar la información. Para regenerar exclusivamente las reservas de demostración:

```bash
python manage.py crear_reservas_demo --reset-demo
```

### Credenciales locales

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin_user` | `admin1234` |
| Cliente de demostración | `demo_user` | `demo1234` |

Las cuentas `ana_demo` y `luis_demo` también utilizan `demo1234` cuando son creadas por primera vez.

> Estas credenciales son exclusivamente para desarrollo local y no deben utilizarse en producción.

---

## 🌍 Rutas principales

| Ruta | Acceso | Descripción |
|---|---|---|
| `/` | Público | Catálogo y búsqueda de recursos. |
| `/registro/` | Público | Creación de una cuenta de cliente. |
| `/login/` | Público | Inicio de sesión. |
| `/calendario_full/<id>/` | Público / autenticado | Consulta del calendario; reservar requiere una sesión. |
| `/perfil/` | Cliente | Datos y preferencias reutilizables. |
| `/mis-reservas/` | Cliente | Reservas, cancelaciones, lista de espera y notificaciones. |
| `/administracion/prevision-demanda/` | Administrador | Análisis de demanda por semanas, recursos y días. |
| `/admin/` | Administrador | Panel administrativo de Django. |

---

## 🔌 API interna

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/reservas/<resource_id>/` | Devuelve reservas y bloqueos del recurso. |
| `POST` | `/api/reservas/crear/` | Crea una reserva única o recurrente. |
| `POST` | `/api/lista-espera/` | Solicita ingreso a la lista de espera. |
| `POST` | `/mis-reservas/<booking_id>/cancelar/` | Cancela una reserva elegible del usuario. |
| `POST` | `/mis-reservas/notificaciones/<notification_id>/leer/` | Marca una notificación propia como leída. |

Las operaciones de escritura requieren autenticación y protección CSRF cuando corresponde.

---

## 📁 Estructura del proyecto

```text
proyecto1-gestor-reservas-ia/
├── gestor_reservas/             # Configuración principal de Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── reservas/                   # Aplicación de reservas
│   ├── management/commands/   # Generación de datos demo
│   ├── migrations/            # Migraciones de base de datos
│   ├── static/                # CSS y JavaScript
│   ├── templates/             # Plantillas de la interfaz
│   ├── admin.py
│   ├── demand.py              # Previsión de demanda
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── docs/                       # Plan, auditoría, QA y registro de desarrollo
├── .github/workflows/tests.yml # Integración continua
├── .env.example
├── iniciar_app.cmd             # Inicio automatizado en Windows
├── manage.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Comandos disponibles

| Comando | Descripción |
|---|---|
| `python manage.py runserver` | Inicia el servidor de desarrollo. |
| `python manage.py migrate` | Aplica las migraciones pendientes. |
| `python manage.py createsuperuser` | Crea una cuenta administrativa manualmente. |
| `python manage.py crear_reservas_demo` | Crea los recursos y datos demostrativos. |
| `python manage.py crear_reservas_demo --reset-demo` | Regenera las reservas de demostración. |
| `python manage.py check` | Comprueba la configuración de Django. |
| `python manage.py makemigrations --check --dry-run` | Verifica que no falten migraciones. |
| `python manage.py test` | Ejecuta toda la suite automatizada. |

---

## 🧪 Pruebas automatizadas

La suite contiene **47 pruebas** que validan los flujos principales, las restricciones de seguridad y los casos de error.

```bash
python manage.py test
```

Para ejecutar un grupo específico:

```bash
python manage.py test reservas.tests.WaitlistTests
```

### Cobertura funcional

| Grupo | Casos principales |
|---|---|
| Reservas | Creación, recurrencia, conflictos, intervalos y confirmaciones. |
| Calendario | Eventos, bloqueos, privacidad y navegación dinámica. |
| Usuarios | Registro, autenticación, redirecciones y preferencias. |
| Cancelaciones | Propiedad, plazo de 24 horas, método HTTP y auditoría. |
| Lista de espera | Autenticación, prioridad, duplicados y horarios pasados. |
| Notificaciones | Propiedad, estado leído y protección del método. |
| Previsión | Semanas completas, día de mayor demanda y permisos. |
| Datos demo | Idempotencia y preservación de reservas ajenas. |

GitHub Actions ejecuta las comprobaciones, migraciones y pruebas en cada Pull Request y actualización de `main`.

---

## 🛡️ Seguridad e integridad

- Protección CSRF en las operaciones de escritura.
- Validación de permisos y propiedad de reservas y notificaciones.
- Transacciones para evitar recurrencias creadas parcialmente.
- Bloqueo y validación de recursos ante solicitudes simultáneas.
- Títulos neutros en eventos ajenos para no exponer datos personales.
- Redirecciones de autenticación limitadas a destinos seguros.
- Auditoría persistente de cancelaciones.
- Restricción administrativa para la previsión de demanda.

---

## 🔄 Flujo de trabajo

El desarrollo se organiza mediante issues, ramas independientes, Pull Requests, revisiones técnicas y pruebas automáticas. Las decisiones relevantes se conservan en [`docs/AI_DEVELOPMENT_LOG.md`](docs/AI_DEVELOPMENT_LOG.md).

---

## ⚠️ Consideraciones

- El servidor incluido es de desarrollo y no debe utilizarse directamente en producción.
- `DJANGO_SECRET_KEY` y las credenciales demostrativas deben reemplazarse en cualquier entorno compartido.
- El comando de datos demo está deshabilitado cuando `DJANGO_DEBUG=False`.
- SQLite es adecuado para la ejecución local; un despliegue con concurrencia real debe evaluar PostgreSQL u otro motor administrado.
- FullCalendar, Lucide y las fuentes de la interfaz se cargan desde servicios externos y requieren conexión a Internet para mostrarse completamente.

---

## 👥 Equipo

- **Gabriel Rodriguez**
- **Carlos Jaen**
- **David Ortega**

Proyecto académico de **Tópicos Especiales II**.
