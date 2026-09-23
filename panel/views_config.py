"""Pantallas nuevas del panel:

- Revisión de documentos: todos los documentos de todos los postulantes en
  un solo lugar, con un visor emergente para revisarlos sin salir de la página.
- Configuración > Historial de procesos: cuántos pasaron / no pasaron en cada
  proceso de admisión y reintegro de los que no pasaron a un proceso nuevo.
- Configuración > Estado de los postulantes: corrección manual del estado.
- Configuración > Personal de admisión: dar o quitar acceso al panel.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme

from convocatorias.models import Convocatoria, Carrera
from postulantes.models import Inscripcion, Documento
from .decorators import panel_required
from .notificaciones import notificar_decision_inscripcion, notificar_reintegro, notificar_comentario


def _convocatoria_activa():
    return Convocatoria.objects.filter(activa=True).order_by('fecha_fin').first()


def _convocatoria_elegida(request, parametro='proceso'):
    """Proceso elegido en el filtro; si no se eligió ninguno, el activo."""
    valor = request.GET.get(parametro, '')
    if valor == 'todos':
        return None, 'todos'
    if valor.isdigit():
        conv = Convocatoria.objects.filter(id=int(valor)).first()
        if conv:
            return conv, str(conv.id)
    conv = _convocatoria_activa()
    return conv, str(conv.id) if conv else 'todos'


def _resumen_proceso(convocatoria):
    """Postulantes de un proceso según su avance: completo (subió los 4
    documentos), incompleto (le falta alguno o debe volver a subirlo) o
    sin documentos (vacío)."""
    inscripciones = Inscripcion.objects.filter(convocatoria=convocatoria).prefetch_related('documentos')
    conteo = {'completo': 0, 'incompleto': 0, 'vacio': 0}
    for inscripcion in inscripciones:
        conteo[inscripcion.avance] += 1
    return {
        'postulantes': sum(conteo.values()),
        'completos': conteo['completo'],
        'incompletos': conteo['incompleto'],
        'vacios': conteo['vacio'],
    }


def _volver(request, por_defecto):
    destino = request.POST.get('next') or request.GET.get('next')
    if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        return redirect(destino)
    return redirect(por_defecto)


def _puede_gestionar_personal(user):
    return user.is_superuser or user.is_staff


# ============================================================
# Revisión de documentos (todos los postulantes en una sola pantalla)
# ============================================================

@panel_required
def revisar_documentos(request):
    convocatoria, filtro_proceso = _convocatoria_elegida(request)
    filtro_docs = request.GET.get('docs', 'pendientes')
    q = request.GET.get('q', '').strip()

    inscripciones = (
        Inscripcion.objects.select_related('postulante', 'postulante__usuario', 'carrera', 'convocatoria')
        .prefetch_related('documentos')
        .order_by('postulante__apellidos', 'postulante__nombres')
    )
    if convocatoria:
        inscripciones = inscripciones.filter(convocatoria=convocatoria)
    if q:
        inscripciones = inscripciones.filter(
            Q(postulante__nombres__icontains=q)
            | Q(postulante__apellidos__icontains=q)
            | Q(postulante__usuario__cedula__icontains=q)
            | Q(numero_postulacion__icontains=q)
        )
    if filtro_docs == 'pendientes':
        inscripciones = inscripciones.filter(documentos__estado='pendiente_revision').distinct()
    elif filtro_docs == 'rechazados':
        inscripciones = inscripciones.filter(documentos__estado='rechazado').distinct()
    elif filtro_docs == 'completos':
        inscripciones = inscripciones.filter(documentos__estado='validado').annotate(
            n_validados=Count('documentos', filter=Q(documentos__estado='validado'), distinct=True)
        ).filter(n_validados=len(Documento.TIPO_CHOICES))

    paginator = Paginator(inscripciones, 12)
    pagina = paginator.get_page(request.GET.get('pagina'))

    for inscripcion in pagina.object_list:
        por_tipo = {d.tipo: d for d in inscripcion.documentos.all()}
        inscripcion.docs_detalle = [
            {'tipo': tipo, 'etiqueta': etiqueta, 'documento': por_tipo.get(tipo)}
            for tipo, etiqueta in Documento.TIPO_CHOICES
        ]
        inscripcion.docs_validados = sum(1 for d in por_tipo.values() if d.estado == 'validado')

    pendientes_total = Documento.objects.filter(estado='pendiente_revision')
    if convocatoria:
        pendientes_total = pendientes_total.filter(inscripcion__convocatoria=convocatoria)

    return render(request, 'panel/revisar_documentos.html', {
        'pagina': pagina,
        'convocatorias': Convocatoria.objects.order_by('-fecha_inicio'),
        'convocatoria': convocatoria,
        'filtro_proceso': filtro_proceso,
        'filtro_docs': filtro_docs,
        'filtro_q': q,
        'pendientes_total': pendientes_total.count(),
        'total_tipos': len(Documento.TIPO_CHOICES),
    })


# ============================================================
# Configuración (pantalla principal)
# ============================================================

@panel_required
def configuracion(request):
    Usuario = get_user_model()

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'estado_postulante':
            inscripcion = Inscripcion.objects.filter(id=request.POST.get('inscripcion') or 0).first()
            nuevo_estado = request.POST.get('estado')
            if inscripcion and nuevo_estado in dict(Inscripcion.ESTADO_CHOICES):
                if inscripcion.estado != nuevo_estado:
                    inscripcion.estado = nuevo_estado
                    inscripcion.save(update_fields=['estado'])
                    messages.success(request, f'Estado de {inscripcion.postulante.nombre_completo} cambiado a "{inscripcion.get_estado_display()}".')
            else:
                messages.error(request, 'No se pudo cambiar el estado.')
            return redirect(f"{request.path}?{request.POST.get('volver', '')}")

    personal_admision = Usuario.objects.filter(
        Q(rol='admin_admision') | Q(is_staff=True) | Q(is_superuser=True)
    ).distinct().order_by('username')

    procesos = []
    for conv in Convocatoria.objects.order_by('-fecha_inicio'):
        procesos.append({'convocatoria': conv, **_resumen_proceso(conv)})

    convocatoria_activa = _convocatoria_activa()
    convocatorias = Convocatoria.objects.order_by('-activa', '-fecha_inicio')

    # Avance de los postulantes por proceso (por defecto el proceso actual)
    proceso_id = request.GET.get('proceso', '')
    proceso = convocatorias.filter(id=proceso_id).first() if proceso_id.isdigit() else convocatoria_activa
    q = request.GET.get('q', '').strip()
    filtro_avance = request.GET.get('avance', '')
    inscripciones = []
    resumen_avance = {'postulantes': 0, 'completos': 0, 'incompletos': 0, 'vacios': 0}
    if proceso:
        consulta = (
            Inscripcion.objects.filter(convocatoria=proceso)
            .select_related('postulante', 'postulante__usuario', 'carrera')
            .prefetch_related('documentos')
            .order_by('postulante__apellidos', 'postulante__nombres')
        )
        if q:
            consulta = consulta.filter(
                Q(postulante__nombres__icontains=q)
                | Q(postulante__apellidos__icontains=q)
                | Q(postulante__usuario__cedula__icontains=q)
                | Q(numero_postulacion__icontains=q)
            )
        resumen_avance = _resumen_proceso(proceso)
        inscripciones = [i for i in consulta if not filtro_avance or i.avance == filtro_avance]
    pagina = Paginator(inscripciones, 15).get_page(request.GET.get('pagina'))

    destinos_abiertos = convocatorias.filter(activa=True)
    if proceso:
        destinos_abiertos = destinos_abiertos.exclude(id=proceso.id)

    return render(request, 'panel/configuracion.html', {
        'convocatoria_activa': convocatoria_activa,
        'convocatorias': convocatorias,
        'procesos_activos': convocatorias.filter(activa=True).count(),
        'procesos': procesos,
        'personal_admision': personal_admision,
        'puede_gestionar_personal': _puede_gestionar_personal(request.user),
        'proceso': proceso,
        'pagina': pagina,
        'resumen_avance': resumen_avance,
        'destinos_abiertos': destinos_abiertos,
        'filtro_q': q,
        'filtro_avance': filtro_avance,
    })


# ============================================================
# Historial de un proceso + reintegro de quienes no pasaron
# ============================================================

@panel_required
def proceso_historial(request, convocatoria_id):
    convocatoria = get_object_or_404(Convocatoria, id=convocatoria_id)
    resumen = _resumen_proceso(convocatoria)

    por_carrera = []
    filas = (
        Inscripcion.objects.filter(convocatoria=convocatoria)
        .values('carrera__nombre', 'estado').annotate(total=Count('id'))
    )
    tabla = {}
    for fila in filas:
        nombre = fila['carrera__nombre'] or 'Sin carrera'
        datos = tabla.setdefault(nombre, {'carrera': nombre, 'inscritos': 0, 'aprobados': 0, 'no_aprobados': 0, 'en_tramite': 0})
        datos['inscritos'] += fila['total']
        if fila['estado'] == 'aprobada':
            datos['aprobados'] += fila['total']
        elif fila['estado'] == 'rechazada':
            datos['no_aprobados'] += fila['total']
        else:
            datos['en_tramite'] += fila['total']
    por_carrera = sorted(tabla.values(), key=lambda d: d['carrera'])

    otros_procesos = Convocatoria.objects.exclude(id=convocatoria.id).order_by('-activa', '-fecha_inicio')
    destino_id = request.GET.get('destino', '')
    destino = otros_procesos.filter(id=destino_id).first() if destino_id.isdigit() else None
    if destino is None:
        destino = otros_procesos.filter(activa=True).first() or otros_procesos.first()

    ver = request.GET.get('ver', 'no_aprobados')
    candidatos = (
        Inscripcion.objects.filter(convocatoria=convocatoria)
        .select_related('postulante', 'postulante__usuario', 'carrera')
        .prefetch_related('documentos')
        .order_by('postulante__apellidos', 'postulante__nombres')
    )
    if ver == 'no_aprobados':
        candidatos = candidatos.filter(estado='rechazada')
    elif ver == 'en_tramite':
        candidatos = candidatos.filter(estado__in=['docs_pendientes', 'en_revision'])
    elif ver == 'aprobados':
        candidatos = candidatos.filter(estado='aprobada')

    ya_en_destino = set()
    carreras_destino = set()
    if destino:
        ya_en_destino = set(
            Inscripcion.objects.filter(convocatoria=destino).values_list('postulante_id', flat=True)
        )
        carreras_destino = set(destino.cupocarrera_set.values_list('carrera_id', flat=True))

    for inscripcion in candidatos:
        inscripcion.ya_reintegrado = inscripcion.postulante_id in ya_en_destino
        inscripcion.carrera_en_destino = inscripcion.carrera_id in carreras_destino
        inscripcion.docs_validados = sum(1 for d in inscripcion.documentos.all() if d.estado == 'validado')

    return render(request, 'panel/proceso_historial.html', {
        'convocatoria': convocatoria,
        'resumen': resumen,
        'por_carrera': por_carrera,
        'candidatos': candidatos,
        'ver': ver,
        'otros_procesos': otros_procesos,
        'destino': destino,
        'total_tipos': len(Documento.TIPO_CHOICES),
    })


@panel_required
def reintegrar_postulantes(request, convocatoria_id):
    origen = get_object_or_404(Convocatoria, id=convocatoria_id)
    if request.method != 'POST':
        return redirect('panel:proceso_historial', convocatoria_id=origen.id)

    destino = Convocatoria.objects.exclude(id=origen.id).filter(id=request.POST.get('destino') or 0).first()
    if not destino:
        messages.error(request, 'Elige el proceso de admisión al que quieres reintegrar a los postulantes.')
        return redirect('panel:proceso_historial', convocatoria_id=origen.id)

    ids = [i for i in request.POST.getlist('inscripciones') if i.isdigit()]
    if not ids:
        messages.warning(request, 'No seleccionaste ningún postulante.')
        return redirect(f"{request.path.rsplit('reintegrar/', 1)[0]}?destino={destino.id}")

    copiar_docs = request.POST.get('copiar_documentos') == '1'
    avisar = request.POST.get('avisar') == '1'

    creadas, omitidas = 0, 0
    with transaction.atomic():
        for anterior in Inscripcion.objects.filter(id__in=ids, convocatoria=origen).select_related('postulante', 'carrera'):
            if Inscripcion.objects.filter(postulante=anterior.postulante, convocatoria=destino).exists():
                omitidas += 1
                continue
            nueva = Inscripcion.objects.create(
                postulante=anterior.postulante,
                convocatoria=destino,
                carrera=anterior.carrera,
            )
            if copiar_docs:
                for doc in anterior.documentos.filter(estado='validado'):
                    Documento.objects.create(
                        inscripcion=nueva,
                        tipo=doc.tipo,
                        archivo=doc.archivo.name,
                        estado='validado',
                        observaciones=f'Validado anteriormente en el proceso {origen.nombre}.',
                        fecha_revision=doc.fecha_revision,
                        revisado_por=doc.revisado_por,
                    )
            nueva.actualizar_estado_por_documentos()
            if avisar:
                notificar_reintegro(nueva, origen)
            creadas += 1

    if creadas:
        messages.success(request, f'{creadas} postulante(s) reintegrado(s) al proceso "{destino.nombre}".')
    if omitidas:
        messages.info(request, f'{omitidas} postulante(s) ya estaban inscritos en "{destino.nombre}" y se omitieron.')
    url = redirect('panel:proceso_historial', convocatoria_id=origen.id).url
    return redirect(f'{url}?destino={destino.id}')


# ============================================================
# Corregir el estado de los postulantes
# ============================================================

@panel_required
def estados_postulantes(request):
    """Revisar y comentar: qué pasos completó cada postulante (✓) y cuáles
    dejó en blanco, con un comentario para avisarle qué le falta."""
    convocatoria, filtro_proceso = _convocatoria_elegida(request)
    q = request.GET.get('q', '').strip()
    filtro_avance = request.GET.get('avance', '')

    inscripciones = (
        Inscripcion.objects.select_related('postulante', 'postulante__usuario', 'carrera', 'convocatoria')
        .prefetch_related('documentos')
        .order_by('postulante__apellidos', 'postulante__nombres')
    )
    if convocatoria:
        inscripciones = inscripciones.filter(convocatoria=convocatoria)
    if q:
        inscripciones = inscripciones.filter(
            Q(postulante__nombres__icontains=q)
            | Q(postulante__apellidos__icontains=q)
            | Q(postulante__usuario__cedula__icontains=q)
            | Q(numero_postulacion__icontains=q)
        )
    inscripciones = list(inscripciones)
    if filtro_avance == 'completo':
        inscripciones = [i for i in inscripciones if i.proceso_completo]
    elif filtro_avance == 'incompleto':
        inscripciones = [i for i in inscripciones if not i.proceso_completo]

    paginator = Paginator(inscripciones, 15)
    pagina = paginator.get_page(request.GET.get('pagina'))
    for inscripcion in pagina.object_list:
        faltan = inscripcion.documentos_faltantes
        if faltan:
            no_subidos = [d['etiqueta'] for d in faltan if d['situacion'] == 'falta']
            rechazados = [d['etiqueta'] for d in faltan if d['situacion'] == 'rechazado']
            texto = 'Tu proceso está incompleto.'
            if no_subidos:
                texto += ' No has subido: ' + ', '.join(no_subidos) + '.'
            if rechazados:
                texto += ' Debes volver a subir: ' + ', '.join(rechazados) + '.'
            inscripcion.comentario_sugerido = texto + ' Ingresa a "Mis documentos" y complétalo.'
        else:
            inscripcion.comentario_sugerido = ''

    return render(request, 'panel/estados_postulantes.html', {
        'pagina': pagina,
        'convocatorias': Convocatoria.objects.order_by('-fecha_inicio'),
        'filtro_proceso': filtro_proceso,
        'filtro_q': q,
        'filtro_avance': filtro_avance,
    })


@panel_required
def enviar_comentario(request, inscripcion_id):
    """Guarda el comentario para el postulante (lo ve en "Mis documentos")
    y se lo envía por correo."""
    inscripcion = get_object_or_404(Inscripcion.objects.select_related('postulante', 'postulante__usuario', 'carrera'), id=inscripcion_id)
    if request.method != 'POST':
        return redirect('panel:estados_postulantes')
    comentario = request.POST.get('comentario', '').strip()
    if not comentario:
        messages.error(request, 'Escribe el comentario que quieres enviar.')
        return _volver(request, 'panel:estados_postulantes')

    from django.utils import timezone
    inscripcion.comentario_revision = comentario
    inscripcion.fecha_comentario = timezone.now()
    inscripcion.save(update_fields=['comentario_revision', 'fecha_comentario'])
    notificar_comentario(inscripcion)
    messages.success(request, f'Comentario enviado a {inscripcion.postulante.nombre_completo}. Lo verá en "Mis documentos" y en su correo.')
    return _volver(request, 'panel:estados_postulantes')


@panel_required
def cambiar_estado(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    if request.method != 'POST':
        return redirect('panel:estados_postulantes')

    nuevo = request.POST.get('estado')
    if nuevo not in dict(Inscripcion.ESTADO_CHOICES):
        messages.error(request, 'Estado no válido.')
        return _volver(request, 'panel:estados_postulantes')

    anterior = inscripcion.get_estado_display()
    if nuevo == inscripcion.estado:
        messages.info(request, f'{inscripcion.postulante.nombre_completo} ya estaba en "{anterior}".')
        return _volver(request, 'panel:estados_postulantes')

    inscripcion.estado = nuevo
    inscripcion.save(update_fields=['estado'])
    if request.POST.get('avisar') == '1':
        notificar_decision_inscripcion(inscripcion)

    messages.success(
        request,
        f'Estado de {inscripcion.postulante.nombre_completo} cambiado de "{anterior}" a "{inscripcion.get_estado_display()}".',
    )
    return _volver(request, 'panel:estados_postulantes')


# ============================================================
# Personal de admisión (dar / quitar acceso al panel)
# ============================================================

@panel_required
def personal_agregar(request):
    if request.method != 'POST' or not _puede_gestionar_personal(request.user):
        messages.error(request, 'Solo un administrador principal puede gestionar el personal de admisión.')
        return redirect('panel:configuracion')

    dato = request.POST.get('usuario', '').strip()
    Usuario = get_user_model()
    usuario = (
        Usuario.objects.filter(username__iexact=dato).first()
        or Usuario.objects.filter(email__iexact=dato).first()
        or Usuario.objects.filter(cedula=dato).first()
    ) if dato else None

    if not usuario:
        messages.error(request, f'No se encontró ninguna cuenta con "{dato}". La persona primero debe registrarse en el sistema.')
    elif usuario.rol == 'admin_admision':
        messages.info(request, f'{usuario.username} ya es parte del personal de admisión.')
    else:
        usuario.rol = 'admin_admision'
        usuario.save(update_fields=['rol'])
        messages.success(request, f'{usuario.username} ahora es personal de admisión y puede entrar al panel.')
    return redirect('panel:configuracion')


@panel_required
def personal_quitar(request, usuario_id):
    Usuario = get_user_model()
    usuario = get_object_or_404(Usuario, id=usuario_id)
    if request.method != 'POST' or not _puede_gestionar_personal(request.user):
        messages.error(request, 'Solo un administrador principal puede gestionar el personal de admisión.')
    elif usuario == request.user:
        messages.error(request, 'No puedes quitarte el acceso a ti mismo.')
    elif usuario.is_superuser or usuario.is_staff:
        messages.error(request, f'{usuario.username} es administrador principal; su acceso se cambia desde el administrador de Django.')
    else:
        usuario.rol = 'postulante'
        usuario.save(update_fields=['rol'])
        messages.success(request, f'Se quitó el acceso al panel a {usuario.username}.')
    return redirect('panel:configuracion')