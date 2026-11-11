# Acceso del MVP — SPEC-007

## Comportamiento

POST /auth/login recibe email y password; responde identidad, rol y empresa.
El identificador de sesión solo se entrega mediante cookie HttpOnly. GET /auth/me
recupera la identidad y POST /auth/logout revoca la sesión persistida. No hay JWT
ni contraseñas en localStorage. Sesión absoluta de 8 horas.

Las claves X-API-Key demo ya no autorizan peticiones. Servicios y reservas requieren
una cuenta business_admin. Un super_admin no puede usar esa cuenta para operar
como un cliente. La dependencia require_super_admin protege el panel administrativo de SPEC-008.
El panel de cliente está disponible en SPEC-009. Registro público, recuperación de contraseña y MFA todavía no existen.

## Preparar desarrollo habitual (pasos explícitos, no automáticos)

Desde la raíz, con el entorno virtual activo y una base de desarrollo configurada:

```powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
```

La revisión e713a007c001 añade users y auth_sessions. No altera registros de
servicios, empresas, reservas ni leads. En una base nueva, ejecutar seed.py para
crear Alfa/Beta antes de crear sus usuarios. En una existente no es necesario.

Crear cuentas separadas; la contraseña se solicita sin eco y no se pasa en argumentos:

```powershell
python scripts/create_user.py --email admin@example.com --role super_admin
python scripts/create_user.py --email alfa@example.com --role business_admin --business-id alfa
python scripts/create_user.py --email beta@example.com --role business_admin --business-id beta
```

Usar contraseñas distintas de 12–128 caracteres. Estos correos son ejemplos de
demostración, no credenciales preconfiguradas. El comando no sobrescribe usuarios.
No existe ninguna contraseña por defecto en el código de aplicación.

Configurar las variables de proceso antes de ejecutar Uvicorn local:

```powershell
$env:AUTH_COOKIE_SECURE = "false"
$env:AUTH_ALLOWED_ORIGINS = "http://127.0.0.1:5178,http://localhost:5178"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

En otra terminal, desde frontend:

```powershell
npm run dev -- --host 127.0.0.1 --port 5178 --strictPort
```

Abrir http://127.0.0.1:5178/#access. Vite redirige /auth y /leads a la API.
Si cambia el puerto, configurar el origen exacto. La lista vacía rechaza login
y escrituras protegidas. No se infiere confianza del encabezado Host.

Para HTTPS, conservar AUTH_COOKIE_SECURE=true (valor predeterminado), limitar
AUTH_ALLOWED_ORIGINS al origen público exacto y configurar el proxy del mismo origen.
No utilizar HTTP ni Secure=false en una publicación pública.

## Controles y límites

- Hash de contraseña Argon2id; identificador aleatorio de 256 bits y hash SHA-256 en DB.
- Cookie HttpOnly, SameSite=Strict y Secure por defecto; respuestas privadas no-store.
- Verificación de Origin en login/logout y escrituras autenticadas. POST /leads es público.
- 5 intentos de login/IP/minuto por proceso, memoria acotada. En varias instancias
  se requiere contador compartido; configurar proxies de confianza antes de publicar.
- Cambiar o desactivar un usuario en la base se refleja en la siguiente petición.
- Logout solo informa éxito después de revocar; ante fallo de red mantiene aviso.
- Caducidad y revocación se validan en servidor. La pantalla recupera sesión al
  recargar y ofrece comprobación manual; no es todavía un panel con sondeo continuo.
- No ejecutar downgrade sobre datos reales: elimina cuentas y sesiones.

## Verificación

pytest usa SQLite temporal y cuentas ficticias. scripts/verify_postgres.py verifica
migración desde SPEC-005, preservación de servicios, sesiones, roles, aislamiento,
reservas concurrentes y logout en PostgreSQL temporal; nunca carga .env.
Los resultados finales se registran en specs/007-authentication/verification.md.


## Arranque local simplificado

El puerto 8000 está ocupado por otro proyecto; ORQENTIVA utiliza 8001.
Desde la raíz, ejecutar en dos terminales:

```powershell
.\scripts\start_development.ps1 -Component api
.\scripts\start_development.ps1 -Component web
```

La migración de desarrollo ya se aplicó el 2026-11-04 con respaldo y comprobación
de datos existentes. La creación de cuentas continúa siendo explícita.

SPEC-008: desactivar un negocio revoca las sesiones de sus usuarios y bloquea nuevos logins. Reactivarlo requiere iniciar sesión de nuevo.

## Demo aislada del TFM

La demo usa los puertos web 5179 y API 8002, con tfm-demo.sqlite3. Ejecutar
scripts/start_tfm_demo.ps1 con -Component api y -Component web en terminales distintas.
Se admiten http://127.0.0.1:5179 y http://localhost:5179; conservar el mismo hostname
al navegar para mantener la cookie. Las tres cuentas ficticias del README tienen
la contraseña Orqentiva-Demo-2026!, exclusivamente en esta base de demostración.
El entorno PostgreSQL habitual (5178/8001) no recibe esas cuentas automáticamente.
Un 403 puede indicar un Origin no autorizado; un 401 indica credenciales o cuenta
no válidas; un 429 requiere esperar al límite de intentos. No borrar la base para resolverlo.
