# Actualizar el sistema en el servidor

Guía para actualizar un servidor donde el sistema **ya está instalado y funcionando**.
No se crea nada desde cero: se descargan los cambios y se reinicia.

## Qué trae esta actualización (27/09/2026)

- Panel → Procesos de admisión: reintegro de estudiantes con **correo automático** (motivo + mensaje).
- Paginación de 10 en 10 en todas las listas del panel.
- Detalle del postulante: botones **Validar proceso / Rechazar proceso / Permitir corregir**.
- Solo los 5 pasos actuales (Registro, Inscripción, Evaluación, Postulación, Aceptación);
  se quitaron los textos y documentos del sistema anterior (cédula, votación, acta, foto).
- **No hay migraciones nuevas** ni paquetes nuevos: la base de datos no cambia de estructura.
- **No cambiaron las rutas (URLs).**

## Pasos

Dentro de la carpeta del proyecto en el servidor (donde está `manage.py`), con el entorno virtual activado:

```bash
# 1. Descargar los cambios
git pull origin main

# 2. Dependencias (no hay nuevas, pero por si acaso)
pip install -r requirements.txt

# 3. Migraciones (debe decir "No migrations to apply")
python manage.py migrate

# 4. Revisión rápida (debe decir "System check identified no issues")
python manage.py check
```

### 5. Agregar el correo al `.env` del servidor

Los avisos por correo necesitan estas variables en el `.env` **del servidor** (ver `.env.example`).
Sin ellas el sistema funciona igual, pero los correos no se envían (solo se imprimen en consola):

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=correo@gmail.com
EMAIL_HOST_PASSWORD=contraseñadeaplicacion
DEFAULT_FROM_EMAIL=Admisiones ISTAM <correo@gmail.com>
```

Probar el envío:

```bash
python manage.py shell -c "from django.core.mail import send_mail; print(send_mail('Prueba ISTAM', 'El correo funciona', None, ['correo@gmail.com']))"
```

Debe imprimir `1`.

### 6. Archivos estáticos

Se modificaron `static/css/estilos.css` y `static/js/avisos.js`. Si el servidor usa `collectstatic`
(con `STATIC_ROOT` definido en su configuración), ejecutarlo:

```bash
python manage.py collectstatic --noinput
```

### 7. (Opcional) Limpiar documentos del sistema anterior

Si la base de datos del servidor todavía tiene documentos de tipos antiguos
(cédula, certificado de votación, acta de grado, foto carnet):

```bash
python manage.py limpiar_documentos_antiguos             # solo muestra cuántos hay
python manage.py limpiar_documentos_antiguos --confirmar # los borra con sus archivos (no se puede deshacer)
```

### 8. Reiniciar la aplicación

Según cómo esté instalado, por ejemplo:

```bash
sudo systemctl restart gunicorn      # o el nombre del servicio que use
sudo systemctl reload nginx
```

## Importante

- **No reemplazar** el `.env` ni la carpeta `media/` del servidor: no están en GitHub a propósito
  (contraseñas y documentos de los postulantes).
- Si `git pull` dice que hay cambios locales en el servidor, revisarlos con `git status`
  antes de continuar.
