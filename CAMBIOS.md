# Cambios en el sistema de admisión ISTAM

Resumen de lo que se agregó/cambió a partir de las indicaciones del ingeniero
y las maquetas de referencia (panel de postulantes, validación de documentos,
inicio y formulario de postulación).

## 1. El postulante ahora puede subir sus documentos en la plataforma

- Nueva pantalla **"Postularme"** (`/postulantes/postular/`): datos personales,
  selección de carrera dentro del proceso activo y confirmación. Al enviarla
  se genera un **número de postulación** único (ej. `POST-2026-00001`).
- En **"Mi proceso de admisión"** cada postulación muestra los 4 documentos
  requeridos (cédula, certificado de votación, acta de grado/título de
  bachiller y foto tamaño carnet) con un botón para subir o volver a subir
  cada uno, y el estado de cada archivo: *no cargado*, *pendiente de
  revisión*, *validado* o *rechazado* (con el motivo).
- El seguimiento visual de etapas ahora es: Inscripción → Documentos →
  Evaluación → Aceptación, alineado con el lenguaje de SENECYT (Registro,
  Inscripción, Evaluación, Postulación, Aceptación, Matriculación).

## 2. Panel administrativo nuevo (antes solo existía el admin de Django)

- `/panel/`: pantalla para el evaluador con tarjetas de resumen (total de
  postulantes, pendientes de validación, documentos por revisar, cupos
  disponibles), tabla de postulantes con búsqueda y filtros por carrera y
  estado, y paginación.
- `/panel/postulante/<id>/`: detalle de cada postulante — sus datos, el
  resultado de examen si ya rindió, y cada documento con botones para
  **aprobar** o **rechazar** (con observación). Al final, un botón para
  **aprobar o rechazar la postulación completa**, que solo se habilita
  cuando los 4 documentos están validados. Así el administrativo puede ver
  de un vistazo en qué paso va cada persona y dónde se está quedando.
- Solo pueden entrar usuarios con rol "Administrativo" (o superusuario). Al
  iniciar sesión, cada quien cae automáticamente en su sección: el
  postulante en "Mi proceso de admisión" y el administrativo en el panel.

## 3. Notificaciones por correo

- Se corrigió la configuración de correo (antes tenía una clave que Django
  no reconocía y nunca se habría podido activar). Ahora en `.env` se puede
  configurar un correo institucional real (ver los comentarios en ese
  archivo); mientras tanto, los correos se imprimen en la consola.
- Se avisa por correo al postulante cuando: un documento es validado o
  rechazado, y cuando su postulación completa es aprobada o rechazada.
- La integración con WhatsApp que mencionaste que el ingeniero usa hoy queda
  pendiente: no hay una API oficial y gratuita de WhatsApp para esto (la de
  Meta requiere aprobación de negocio y cuesta por mensaje). Si quieren
  avanzar en eso, dime y lo cotizamos/planificamos aparte.

## 4. Rediseño visual

- Nueva paleta e interfaz (tipografía Public Sans, tarjetas, tabla y
  distintivos de estado) inspirada en las maquetas que enviaste, aplicada a
  todo el sitio: inicio, carreras, login, registro, ayuda, "Mi proceso de
  admisión", el nuevo formulario de postulación y el panel administrativo.

## 5. Otros cambios técnicos

- Se agregaron migraciones de base de datos (`postulantes/migrations/0002_...`).
  Incluyen un paso que genera automáticamente un número de postulación para
  inscripciones que ya existan en la base de datos real, así que es seguro
  correr `python manage.py migrate` aunque ya haya postulantes cargados.
- Se agregó `Pillow` a `requirements.txt` (es necesaria para la foto del
  postulante). Antes de correr el proyecto: `pip install -r requirements.txt`.
- Documento ahora tiene tipos más específicos (cédula, certificado de
  votación, acta de grado/título de bachiller, foto) en vez del genérico
  "certificado de estudios" que tenía antes. Si en la base de datos real ya
  hay documentos con el tipo anterior, van a quedar con esa etiqueta antigua;
  avísame si quieres que migre esos datos a los tipos nuevos.

## 6. Nombre oficial del instituto

- Se corrigió el nombre en los lugares más visibles del sistema (barra de
  navegación, inicio, pie de página, panel administrativo y admin de
  Django): ahora dice **Instituto Superior Tecnológico Amazónico**, usando
  "ISTAM" solo como marca/sigla secundaria, no como nombre principal.

## 7. Nueva paleta de colores (verde institucional #8BC34A)

- Se reemplazó la paleta morada/índigo por una paleta verde basada en el
  color real del EVA (`#8BC34A`), aplicada en todo el sitio público, el
  panel administrativo y el admin de Django (`estilos.css` y
  `admin_istam.css`). Se ajustaron los tonos exactos usados en botones y
  encabezados para mantener buen contraste de texto blanco sobre verde.
- Se agregaron degradados y sombras suaves en botones, tarjetas del inicio,
  logo, avatares y encabezado del panel para un look más elegante y
  llamativo, sin cambiar la estructura de las pantallas.

## 8. Chat de ayuda interactivo (reemplaza la página de Ayuda)

- Se quitó el enlace "Ayuda" del menú y la antigua página estática de
  contacto. Todo pasa ahora por el botón flotante 💬, que abre un panel de
  chat más grande con dos pestañas:
  - **Chat**: el postulante puede escribir preguntas libres o usar botones
    rápidos ("¿Qué documentos debo subir?", "¿Cómo veo el estado de mi
    postulación?", "¿Qué es el proceso de SENECYT?", "Quiero hablar con una
    persona"). Las respuestas son reglas simples por palabra clave (no es
    un modelo de lenguaje conectado), pensadas para las dudas más comunes
    del proceso y de SENECYT.
  - **Ubicación y contacto**: muestra un mapa embebido de Google Maps con la
    ubicación real del instituto y los datos oficiales de contacto
    (dirección, horario de atención, WhatsApp, teléfono fijo, Instagram y
    Facebook).
  - Un enlace viejo a `/ayuda/` sigue funcionando: ahora redirige a la
    página de inicio y abre el chat automáticamente.
- Si más adelante quieren que el chat responda con inteligencia artificial
  real (en vez de reglas fijas) o que las conversaciones lleguen a un
  correo/WhatsApp del instituto, eso es una fase aparte — avísame y lo
  planificamos.

## 9. El panel ya no manda a los operadores al admin de Django

- Antes, "Procesos de admisión", "Carreras", "Exámenes", "Reportes" y
  "Configuración" del panel eran solo enlaces directos a las pantallas
  crudas de `/admin/...`. Ahora cada uno tiene su propia pantalla dentro
  de `/panel/`, con el mismo diseño verde del resto del sistema:
  - **Carreras**: lista, crear y editar carreras.
  - **Procesos de admisión**: lista, crear y editar convocatorias, y desde
    ahí mismo se definen los cupos por carrera de ese proceso (ya no hace
    falta entrar a otra pantalla para eso).
  - **Exámenes**: lista, crear y editar exámenes, con selector de fecha y
    hora normal (esto también corrige el error "Introduzca una hora
    válida" que salía en el admin de Django).
  - **Reportes**: una pantalla de solo lectura con totales por estado,
    por carrera y por estado de documento.
  - **Configuración**: muestra el proceso de admisión activo y el
    personal de admisión registrado.
  Toda esta información sigue siendo la misma de siempre (los mismos
  modelos/tablas), así que lo que se carga aquí aparece automáticamente
  en el sitio público para los postulantes (carreras visibles, cupos,
  etc.) — es la misma base de datos, solo con una pantalla propia para
  cargarla, sin pasar por `/admin/`.
- El administrador de Django (`/admin/`) volvió a su color y diseño
  **automático/original** de Django (se quitó el CSS y la plantilla que lo
  pintaban de verde). Sigue existiendo como herramienta técnica aparte,
  solo para tareas de superusuario (crear grupos, permisos, etc.), y ya no
  es el camino normal para el día a día del panel.

## Pendiente de confirmar con el ingeniero

- Alcance real de "conectar con SENECYT": por ahora solo se alineó la
  terminología y las etapas visibles del proceso. Si él tiene acceso a algún
  sistema o archivo oficial de SENECYT con el que de verdad haya que
  intercambiar datos, cuéntame los detalles (qué plataforma, qué datos, en
  qué formato) para evaluar esa integración.

## 10. Recuperar y cambiar contraseña

- En la pantalla de **Iniciar sesión** ahora aparece **"¿Olvidaste tu
  contraseña?"**. El postulante escribe su correo, le llega un mensaje con un
  botón para crear una contraseña nueva (el enlace dura 24 horas y solo se
  puede usar una vez). El correo también le recuerda cuál es su usuario.
- Nueva opción **"Cambiar contraseña"** para quien ya inició sesión (en la
  barra superior, en el pie de página y en el menú lateral del panel).
- Ahora se puede iniciar sesión con el **usuario, el correo o la cédula**.
- En el registro ya no se permite crear dos cuentas con el mismo correo o la
  misma cédula (así la recuperación por correo siempre encuentra a la
  persona correcta).

**IMPORTANTE para que el correo llegue de verdad:** mientras no se configure
un correo en `.env`, los mensajes solo se imprimen en la consola donde corre
`python manage.py runserver` (ahí puedes copiar el enlace para probar). Para
enviarlos de verdad, agrega al `.env` (ejemplo con Gmail, usando una
"contraseña de aplicación" de Google, no la contraseña normal):

    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_USE_TLS=True
    EMAIL_HOST_USER=correo.del.instituto@gmail.com
    EMAIL_HOST_PASSWORD=la_contraseña_de_aplicacion
    DEFAULT_FROM_EMAIL=Admisión ISTAM <correo.del.instituto@gmail.com>

## 11. Mejoras de diseño

- Login, registro y todas las pantallas de contraseña tienen un diseño
  nuevo de dos columnas (panel verde institucional con el logo + formulario).
- Botón **"Ver / Ocultar"** en todos los campos de contraseña.
- Los avisos ahora tienen color según el tipo (verde = éxito, rojo = error,
  amarillo = advertencia), se pueden cerrar y los de éxito desaparecen solos.
  Antes todos los avisos salían en verde, incluso los errores.
- Pie de página nuevo con dirección, horario, WhatsApp y accesos rápidos.
- La barra superior se queda fija al hacer scroll y se adapta mejor al celular.
- La zona horaria del sistema pasó de UTC a **Ecuador (America/Guayaquil)**,
  así las fechas y horas que se muestran coinciden con la hora local.
- No se tocó ningún modelo: **no hace falta `migrate`**.

## 12. Revisión de documentos en un solo lugar (panel)

- Nueva opción en el menú del panel: **"Revisión de documentos"**. Muestra a
  todos los postulantes con sus 4 documentos en una sola pantalla, con
  colores: amarillo = por revisar, verde = validado, rojo = rechazado,
  punteado = todavía no lo sube.
- Al hacer clic en cualquier documento se abre una **ventana emergente**
  (visor) dentro de la misma página: se ve el PDF o la imagen, y ahí mismo
  se puede **aprobar o rechazar** con una observación. Con las flechas
  ‹ › (o las del teclado) se pasa al siguiente documento sin cerrar la
  ventana, y el botón ⤢ la agranda a pantalla completa.
- Filtros por proceso de admisión, por búsqueda y por "con documentos por
  revisar / rechazados / todo validado / todos".
- En la ficha de cada postulante, "Ver documento" también abre el visor.
- Los archivos Word (.docx) no se pueden mostrar en el navegador; para esos
  el visor muestra un botón para descargarlos.

## 13. Configuración: historial de procesos, reintegro y corrección de estados

- **Historial de procesos de admisión**: tabla con cada proceso (activo o
  cerrado) y cuántos se inscribieron, cuántos **pasaron** (aprobados),
  cuántos **no pasaron** (rechazados) y cuántos quedaron en trámite.
- **Ver y reintegrar**: dentro de cada proceso se ven los resultados por
  carrera y la lista de quienes no pasaron. Se marcan los que se quieren
  **reintegrar al proceso nuevo** y con un clic se les crea una nueva
  postulación (misma carrera, nuevo número de postulación) sin borrar su
  historial anterior. Opciones: conservar los documentos que ya estaban
  validados (para que no los vuelvan a subir) y avisar a cada postulante
  por correo.
- **Estado de los postulantes**: pantalla para **corregir manualmente** el
  estado de cualquier postulación (por ejemplo, si se rechazó por error),
  con opción de avisar al postulante por correo. También se llega desde la
  ficha del postulante con el botón "Corregir estado".
- **Personal de admisión**: el rol ahora se muestra bien (antes un
  administrador salía como "Postulante"). Un administrador principal puede
  **dar acceso al panel** a otra persona escribiendo su usuario, correo o
  cédula, y **quitarle el acceso**, sin entrar al admin de Django.
- Se corrigió el botón "Editar este proceso" que salía encimado sobre las
  fechas, y los filtros del panel ahora quedan en una sola fila.
- No se tocó ningún modelo: **no hace falta `migrate`**.
