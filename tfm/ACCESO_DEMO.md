# Acceso de demostración para el TFM

Estos accesos funcionan únicamente en la base aislada creada por scripts/prepare_tfm_demo.py. No son credenciales de las cuentas habituales del autor.

| Rol | Usuario | Contraseña de demostración |
| --- | --- | --- |
| Administrador | admin@example.com | Orqentiva-Demo-2026! |
| Barbería Alfa | alfa@example.com | Orqentiva-Demo-2026! |
| Barbería Beta | beta@example.com | Orqentiva-Demo-2026! |

URL de acceso: http://127.0.0.1:5179/#access

Reservas Alfa: http://127.0.0.1:5179/#reservar/alfa

Reservas Beta: http://127.0.0.1:5179/#reservar/beta

## Preparar y abrir

Instalar dependencias según README, ejecutar python scripts/prepare_tfm_demo.py y abrir dos terminales. En una ejecutar .\scripts\start_tfm_demo.ps1 -Component api y en la otra .\scripts\start_tfm_demo.ps1 -Component web. La demo queda limitada a 127.0.0.1. Detener ambos procesos con Ctrl+C al terminar.

El preparador usa migraciones hasta head. Si tfm-demo.sqlite3 ya existe, lo conserva y no vuelve a crear datos ni cuentas. Para repetir la demo basta arrancar los dos servicios; no es necesario prepararla otra vez.

## Recorrido sugerido

1. Entrar como administrador y mostrar Alfa/Beta.
2. Cerrar sesión y entrar como Alfa. Mostrar Corte demo, Ana y los horarios.
3. Abrir el enlace de reservas de Alfa y desplegar «Reservar por chat».
4. Escribir «Quiero Corte demo con Ana el AAAA-MM-DD a las 10», usando una fecha futura libre.
5. Escribir «Soy Pedro». Mostrar la propuesta antes de confirmar.
6. Preguntar «¿Con cuánta anticipación puedo cancelar?». Alfa debe citar 24 horas.
7. Volver al modo de reservas y pulsar «Confirmar cita».
8. Volver al panel de Alfa y comprobar la reserva.
9. En Beta, la misma consulta debe citar 48 horas y su panel no debe mostrar la reserva de Alfa.

No publicar este entorno con su contraseña conocida ni reutilizarla en cuentas reales. Para una publicación compartida, usar datos ficticios, cuentas de acceso limitado y una configuración específica. SQLite aquí sirve para revisar la aplicación localmente, no como recomendación de despliegue multiusuario.
