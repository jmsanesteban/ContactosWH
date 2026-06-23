# ContactosWH — Gestión de Contactos

Aplicación web para la gestión de contactos con importación/exportación Excel, control de visibilidad y gestión de usuarios.

---

## Índice

1. [Arquitectura](#1-arquitectura)
2. [Componentes y versiones](#2-componentes-y-versiones)
3. [Estructura del proyecto](#3-estructura-del-proyecto)
4. [Despliegue rápido (Docker)](#4-despliegue-rápido-docker)
5. [Despliegue en producción (Debian/Ubuntu)](#5-despliegue-en-producción-debianubuntu)
6. [Configuración (variables de entorno)](#6-configuración-variables-de-entorno)
7. [Funcionalidades y cómo probarlas](#7-funcionalidades-y-cómo-probarlas)
8. [Gestión de usuarios](#8-gestión-de-usuarios)
9. [Formato del Excel de importación](#9-formato-del-excel-de-importación)
10. [Seguridad](#10-seguridad)
11. [Solución de problemas](#11-solución-de-problemas)

---

## 1. Arquitectura

```
Internet → Nginx (80) → Gunicorn (8000) → Flask App → MariaDB (3306)
```

| Capa | Tecnología | Rol |
|---|---|---|
| Proxy inverso | Nginx 1.27 | SSL termination, ficheros estáticos, cabeceras de seguridad |
| Servidor WSGI | Gunicorn 22 | Workers Python (4 por defecto) |
| Aplicación | Flask 3.0 (Python 3.12) | Lógica de negocio, plantillas Jinja2 |
| Base de datos | MariaDB 11 | Almacenamiento persistente |
| Contenedores | Docker + Docker Compose 3.9 | Orquestación |

---

## 2. Componentes y versiones

### Python / Flask

| Paquete | Versión | Propósito |
|---|---|---|
| Python | 3.12 | Intérprete |
| Flask | 3.0.3 | Framework web |
| Flask-SQLAlchemy | 3.1.1 | ORM para MariaDB |
| Flask-Login | 0.6.3 | Gestión de sesiones y autenticación |
| Flask-WTF | 1.2.1 | Formularios con protección CSRF |
| WTForms | 3.1.2 | Validación de formularios |
| Werkzeug | 3.0.3 | Hashing de contraseñas (pbkdf2:sha256) |
| PyMySQL | 1.1.1 | Driver MySQL puro Python |
| cryptography | 42.0.8 | Criptografía requerida por PyMySQL |
| openpyxl | 3.1.5 | Lectura/escritura de archivos Excel (.xlsx) |
| pandas | 2.2.2 | Parseo robusto de Excel |
| gunicorn | 22.0.0 | Servidor WSGI de producción |
| python-dotenv | 1.0.1 | Carga de variables de entorno desde .env |
| email-validator | 2.2.0 | Validación de emails en formularios |

### Infraestructura

| Componente | Versión | Notas |
|---|---|---|
| MariaDB | 11 | Compatible con MySQL 8 |
| Nginx | 1.27-alpine | Ligero, Alpine Linux |
| Docker Engine | 24+ | Recomendado |
| Docker Compose | v2.x | Sintaxis `version: '3.9'` |

---

## 3. Estructura del proyecto

```
contactos_wh/
├── app/
│   ├── __init__.py               # Factory de la aplicación Flask
│   ├── config.py                 # Configuración por entorno
│   ├── extensions.py             # SQLAlchemy, LoginManager
│   ├── models/
│   │   ├── user.py               # Modelo User (admin/user, hash contraseña)
│   │   ├── field.py              # FieldDefinition (campos dinámicos)
│   │   └── contact.py            # Contact + ContactValue (valores EAV)
│   ├── blueprints/
│   │   ├── auth/                 # Login, logout, cambio de contraseña
│   │   ├── contacts/             # Vista de contactos (usuarios)
│   │   └── admin/                # Panel admin completo
│   ├── utils/
│   │   ├── excel.py              # parse_excel(), export_to_excel()
│   │   └── security.py           # generate_secure_password()
│   ├── templates/                # Jinja2 HTML
│   └── static/
│       ├── css/style.css         # Diseño moderno minimalista
│       └── js/app.js             # Sidebar, CSRF, alerts
├── nginx/nginx.conf              # Configuración Nginx
├── Dockerfile                    # Imagen Python 3.12-slim
├── docker-compose.yml            # Servicios: db, app, nginx
├── manage.py                     # CLI: init_db, create_admin, reset_password
├── wsgi.py                       # Entrypoint Gunicorn
├── requirements.txt
├── .env.example                  # Plantilla de variables de entorno
└── README.md
```

### Modelo de datos (EAV)

```
users                field_definitions
─────────────        ─────────────────────
id (PK)              id (PK)
username             name          ← nombre interno (slug del header Excel)
email                display_name  ← nombre visible en UI
password_hash        is_visible
role                 field_order
is_active            created_at
must_change_password
created_at

contacts             contact_values
─────────────        ─────────────────────────────
id (PK)              id (PK)
is_visible           contact_id (FK → contacts)
created_at           field_id   (FK → field_definitions)
updated_at           value (TEXT)
created_by_id
```

---

## 4. Despliegue rápido (Docker)

### Requisitos previos

- Docker Engine 24+
- Docker Compose v2+
- Puerto 80 libre

### Pasos

```bash
# 1. Clonar / copiar el proyecto
cd /opt
git clone <repo> contactos_wh
cd contactos_wh

# 2. Crear el archivo de entorno
cp .env.example .env
nano .env   # Edita las contraseñas

# 3. Construir y arrancar
docker compose up -d --build

# 4. Ver logs del primer arranque (se muestran las credenciales del admin)
docker compose logs app
```

En el primer arranque verás en los logs:

```
[ADMIN CREADO]
  Usuario   : admin
  Contraseña: Xk7#mP2qL!vN9wRt
  (Cambia la contraseña en el primer inicio de sesión)
```

Accede a `http://IP_DEL_SERVIDOR` e inicia sesión con `admin` y la contraseña mostrada.

### Comandos útiles

```bash
# Ver estado
docker compose ps

# Ver logs en tiempo real
docker compose logs -f app

# Detener
docker compose down

# Detener y borrar datos (CUIDADO: elimina la BD)
docker compose down -v

# Restablecer contraseña de un usuario
docker compose exec app python manage.py reset_password <username>

# Crear nuevo admin
docker compose exec app python manage.py create_admin
```

---

## 5. Despliegue en producción (Debian/Ubuntu)

Si prefieres instalación directa sin Docker:

```bash
# Dependencias del sistema
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip \
                   mariadb-server nginx

# Crear base de datos
sudo mariadb -e "
  CREATE DATABASE IF NOT EXISTS contactos_wh CHARACTER SET utf8mb4;
  CREATE USER IF NOT EXISTS 'contactos_user'@'localhost' IDENTIFIED BY 'TU_CONTRASEÑA';
  GRANT ALL PRIVILEGES ON contactos_wh.* TO 'contactos_user'@'localhost';
  FLUSH PRIVILEGES;
"

# Entorno virtual
cd /opt/contactos_wh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configurar .env (cambia DB_HOST a localhost)
cp .env.example .env
nano .env

# Inicializar BD
python manage.py init_db

# Servicio systemd
sudo tee /etc/systemd/system/contactos.service <<EOF
[Unit]
Description=ContactosWH Gunicorn
After=network.target mariadb.service

[Service]
User=www-data
WorkingDirectory=/opt/contactos_wh
EnvironmentFile=/opt/contactos_wh/.env
ExecStart=/opt/contactos_wh/.venv/bin/gunicorn wsgi:application \
          --bind 127.0.0.1:8000 --workers 4 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now contactos

# Nginx
sudo cp nginx/nginx.conf /etc/nginx/sites-available/contactos
sudo ln -s /etc/nginx/sites-available/contactos /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 6. Configuración (variables de entorno)

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave secreta Flask (mín. 32 chars aleatorios) | `openssl rand -hex 32` |
| `FLASK_ENV` | `production` o `development` | `production` |
| `DB_HOST` | Host de MariaDB | `db` (Docker) / `localhost` |
| `DB_PORT` | Puerto MariaDB | `3306` |
| `DB_NAME` | Nombre de la base de datos | `contactos_wh` |
| `DB_USER` | Usuario de la BD | `contactos_user` |
| `DB_PASSWORD` | Contraseña del usuario de la BD | cadena segura |
| `MYSQL_ROOT_PASSWORD` | Contraseña root (solo Docker) | cadena segura |

---

## 7. Funcionalidades y cómo probarlas

### 7.1 Inicio de sesión

1. Ve a `http://localhost/auth/login`
2. Introduce `admin` y la contraseña generada
3. Al ser el primer acceso, se te pedirá cambiar la contraseña

### 7.2 Importar contactos desde Excel

**Formato del Excel:** Primera fila = cabeceras de columna.

Ejemplo:

| nombre | apellidos | profesion | ciudad | lugar_de_trabajo |
|---|---|---|---|---|
| Juan | García | Médico | Madrid | Hospital La Paz |

**Pasos:**
1. Panel Admin → **Importar Excel**
2. Selecciona o arrastra el archivo `.xlsx`
3. Opcionalmente activa "Actualizar contactos existentes"
4. Haz clic en **Importar**

Los campos se crean automáticamente si no existen.

### 7.3 Visibilidad de contactos y campos

- **Admin → Campos**: activa/desactiva la visibilidad de cada campo con el toggle. Arrastra filas para reordenar.
- **Admin → Gestionar contactos**: activa/desactiva la visibilidad de contactos individuales.
- Los usuarios normales solo ven contactos y campos marcados como visibles.

### 7.4 Exportar contactos

1. Admin → **Exportar Excel**
2. Selecciona los contactos (por defecto todos)
3. Elige si exportar solo campos visibles o todos
4. Clic en **Exportar a Excel** → descarga `contactos_export.xlsx`

### 7.5 Gestión de usuarios

1. Admin → **Usuarios** → **Nuevo usuario**
2. Rellena usuario, email y rol (Usuario / Administrador)
3. Se genera automáticamente una contraseña segura mostrada en pantalla
4. El usuario deberá cambiarla en su primer acceso

Acciones disponibles sobre usuarios:
- **Editar**: cambiar nombre, email, rol, estado
- **⏸ / ▶**: activar/desactivar cuenta
- **🔑**: restablecer contraseña (genera una nueva)
- **✕**: eliminar usuario (no se puede eliminar a uno mismo)

---

## 8. Gestión de usuarios

### Roles

| Rol | Acceso |
|---|---|
| `admin` | Todo: contactos, campos, usuarios, importar, exportar |
| `user` | Solo ver contactos y campos marcados como visibles |

### Contraseñas

- Generadas con `secrets.choice` (CSPRNG) sobre alfabeto de 64 chars
- Longitud mínima: 16 caracteres
- Requieren: mayúscula + minúscula + dígito + símbolo especial
- Almacenadas como hash `pbkdf2:sha256` via Werkzeug
- El flag `must_change_password=True` fuerza cambio en el primer login

---

## 9. Formato del Excel de importación

### Requisitos

- Extensión: `.xlsx` o `.xls`
- Primera fila: nombres de columnas (cabeceras)
- Las cabeceras se normalizan automáticamente: minúsculas, espacios → `_`
- No hay límite de columnas
- Tamaño máximo: 32 MB

### Ejemplo de columnas soportadas

```
nombre, apellidos, lugar_de_trabajo, lugar_de_descanso, lugar_de_residencia,
ciudad, profesion, raza, untersuchung, telefono, email, notas, ...
```

### Actualización de contactos existentes

Si activas "Actualizar contactos existentes", el sistema busca coincidencias por los campos `nombre` + `apellidos` (o `name` + `apellido`). Si encuentra una coincidencia, actualiza los valores; si no, crea un nuevo contacto.

---

## 10. Seguridad

| Medida | Implementación |
|---|---|
| CSRF | Flask-WTF en todos los formularios + header `X-CSRFToken` en AJAX |
| Hashing de contraseñas | PBKDF2-SHA256 (Werkzeug) |
| SQL injection | Prevenido por SQLAlchemy ORM (queries parametrizadas) |
| XSS | Auto-escape en Jinja2 |
| Autenticación | Flask-Login con sesión segura firmada |
| Autorización | Decorator `@admin_required` en todas las rutas de admin |
| Cabeceras HTTP | `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` via Nginx |
| Subida de ficheros | Validación de extensión + límite 32 MB |
| Contraseñas seguras | `secrets` module (CSPRNG), política de complejidad |
| Usuario mínimo privilegios | Imagen Docker corre con usuario `appuser` (no root) |

---

## 11. Solución de problemas

### La app no arranca — "Can't connect to MySQL"

La base de datos tarda en arrancar. El `healthcheck` espera hasta 30s. Si persiste:

```bash
docker compose logs db
docker compose restart app
```

### Contraseña del admin perdida

```bash
docker compose exec app python manage.py reset_password admin
```

### Error 500 al importar Excel

- Verifica que la primera fila tenga cabeceras y no esté vacía
- El archivo debe ser `.xlsx` (no `.csv`)
- Consulta los logs: `docker compose logs app`

### Cambiar número de workers Gunicorn

Edita el `CMD` del `Dockerfile` y cambia `--workers 4`. Para alto tráfico: `2 * CPU_CORES + 1`.
