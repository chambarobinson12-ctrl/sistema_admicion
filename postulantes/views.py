from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q
from django.urls import reverse

from convocatorias.models import Convocatoria, Carrera
from .models import Postulante, Inscripcion, Documento, ConfiguracionProceso
from .forms import PostulacionForm, DocumentoForm, DatosPersonalesForm


def _convocatoria_activa():
    """El proceso de admisión vigente. Si hay varias activas, toma la que cierra antes."""
    return Convocatoria.objects.filter(activa=True).order_by('fecha_fin').first()


def _carreras_de(convocatoria):
    if not convocatoria:
        return Carrera.objects.none()
    return Carrera.objects.filter(cupocarrera__convocatoria=convocatoria).distinct()


def _volver_al_paso(tipo):
    """Vuelve a Mi proceso dejando abierto el paso de ese documento."""
    tipos = [t for t, _ in Documento.TIPO_CHOICES]
    if tipo in tipos:
        return f"{reverse('mis_inscripciones')}?paso={tipos.index(tipo) + 1}"
    return reverse('mis_inscripciones')


def _reabrir_si_estaba_revisada(inscripcion):
    """Si la postulación ya estaba marcada como revisada y el postulante cambia
    algo, vuelve a quedar abierta para que admisión la revise otra vez."""
    if inscripcion.estado == 'aprobada':
        inscripcion.estado = 'docs_pendientes'
        inscripcion.save(update_fields=['estado'])


@login_required
def postular(request):
    convocatoria = _convocatoria_activa()

    if not convocatoria:
        messages.info(request, 'No hay ningún proceso de admisión activo por el momento.')
        return redirect('inicio')

    postulante = Postulante.objects.filter(usuario=request.user).first()

    if postulante and Inscripcion.objects.filter(postulante=postulante, convocatoria=convocatoria).exists():
        messages.info(request, 'Ya tienes una postulación registrada en este proceso de admisión.')
        return redirect('mis_inscripciones')

    carreras_disponibles = _carreras_de(convocatoria)

    if request.method == 'POST':
        form = PostulacionForm(request.POST, request.FILES, instance=postulante, carreras_disponibles=carreras_disponibles)
        if form.is_valid():
            nuevo_postulante = form.save(commit=False)
            nuevo_postulante.usuario = request.user
            nuevo_postulante.save()

            if form.cleaned_data.get('telefono'):
                request.user.telefono = form.cleaned_data['telefono']
                request.user.save(update_fields=['telefono'])

            try:
                inscripcion = Inscripcion.objects.create(
                    postulante=nuevo_postulante,
                    convocatoria=convocatoria,
                    carrera=form.cleaned_data['carrera'],
                )
            except IntegrityError:
                messages.warning(request, 'Ya tienes una postulación registrada en este proceso de admisión.')
                return redirect('mis_inscripciones')

            messages.success(
                request,
                f'¡Registro completado! Tu número de postulación es {inscripcion.numero_postulacion}. '
                'Ahora sube tus documentos para continuar el proceso.',
            )
            return redirect('mis_inscripciones')
    else:
        initial = {'telefono': request.user.telefono}
        form = PostulacionForm(instance=postulante, initial=initial, carreras_disponibles=carreras_disponibles)

    cupos_por_carrera = []
    for cupo in convocatoria.cupocarrera_set.select_related('carrera'):
        cupos_por_carrera.append({
            'carrera_id': cupo.carrera_id,
            'nombre': cupo.carrera.nombre,
            'cupos': cupo.cupos,
        })

    return render(request, 'postulantes/postular.html', {
        'form': form,
        'convocatoria': convocatoria,
        'cupos_por_carrera': cupos_por_carrera,
    })


@login_required
def iniciar_postulacion(request):
    if request.method != 'POST':
        return redirect('lista_carreras')

    convocatoria = _convocatoria_activa()
    if not convocatoria:
        messages.info(request, 'No hay ningún proceso de admisión activo por el momento.')
        return redirect('inicio')

    try:
        carrera = _carreras_de(convocatoria).get(id=request.POST.get('carrera'))
    except (Carrera.DoesNotExist, ValueError, TypeError):
        messages.error(request, 'Esa carrera no está disponible en este proceso.')
        return redirect('lista_carreras')

    postulante, _creado = Postulante.objects.get_or_create(usuario=request.user)

    if Inscripcion.objects.filter(postulante=postulante, convocatoria=convocatoria).exists():
        messages.info(request, 'Ya tienes una postulación en este proceso. Puedes cambiar tu carrera en el paso 1.')
    else:
        Inscripcion.objects.create(postulante=postulante, convocatoria=convocatoria, carrera=carrera)
        messages.success(request, f'Elegiste {carrera.nombre}. Completa el paso 1 con tus datos personales.')

    return redirect('mis_inscripciones')


@login_required
def mis_inscripciones(request):
    todas = list(
        Inscripcion.objects.filter(postulante__usuario=request.user)
        .select_related('carrera', 'convocatoria')
        .prefetch_related('documentos')
        .order_by('-fecha_inscripcion')
    )

    if not todas:
        messages.info(request, 'Elige la carrera a la que quieres postular para empezar tu proceso.')
        return redirect('lista_carreras')

    # Una sola tarjeta: la inscripción más reciente (la del proceso vigente).
    # Las anteriores se conservan como historial para el administrador.
    inscripciones = todas[:1]

    # Textos de los pasos que el administrador puede cambiar desde Configuración
    config = ConfiguracionProceso.obtener()
    pasos_cfg = config.pasos()

    for inscripcion in inscripciones:
        docs_por_tipo = {d.tipo: d for d in inscripcion.documentos.all()}
        inscripcion.form_datos = DatosPersonalesForm(
            instance=inscripcion.postulante,
            initial={'telefono': request.user.telefono, 'carrera': inscripcion.carrera_id},
            carreras_disponibles=_carreras_de(inscripcion.convocatoria),
            auto_id=f'dp{inscripcion.id}_%s',
        )
        inscripcion.docs_detalle = [
            {
                'tipo': tipo,
                'etiqueta': etiqueta,
                'documento': docs_por_tipo.get(tipo),
            }
            for tipo, etiqueta in Documento.TIPO_CHOICES
        ]

        # Los pasos con los textos configurados (nombre, documento e indicaciones)
        avance = inscripcion.avance_documentos
        for item, cfg in zip(avance, pasos_cfg):
            item['corto'] = cfg['nombre']
            item['etiqueta'] = cfg['documento']
            item['ayuda'] = cfg['ayuda']
        inscripcion.avance_config = avance

    return render(request, 'postulantes/mis_inscripciones.html', {
        'inscripciones': inscripciones,
        'proceso_config': config,
    })


@login_required
def subir_documento(request, inscripcion_id, tipo):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id, postulante__usuario=request.user)
    tipos_validos = dict(Documento.TIPO_CHOICES)

    if tipo not in tipos_validos:
        messages.error(request, 'Tipo de documento no reconocido.')
        return redirect('mis_inscripciones')

    if request.method != 'POST':
        return redirect('mis_inscripciones')

    # Solo se protege un documento que admisión ya validó. Los rechazados y los
    # pendientes se pueden cambiar aunque la postulación ya esté revisada.
    documento_actual = Documento.objects.filter(inscripcion=inscripcion, tipo=tipo).first()
    if documento_actual and documento_actual.estado == 'validado':
        messages.warning(request, 'Este documento ya fue validado por admisión; no se puede cambiar.')
        return redirect(_volver_al_paso(tipo))

    documento, _creado = Documento.objects.get_or_create(inscripcion=inscripcion, tipo=tipo)
    form = DocumentoForm(request.POST, request.FILES, instance=documento)

    if form.is_valid():
        documento = form.save(commit=False)
        documento.estado = 'pendiente_revision'
        documento.observaciones = ''
        documento.fecha_revision = None
        documento.revisado_por = None
        documento.save()
        _reabrir_si_estaba_revisada(inscripcion)
        inscripcion.actualizar_estado_por_documentos()
        messages.success(request, f'{tipos_validos[tipo]} subido correctamente. Quedó pendiente de revisión.')
    else:
        if _creado:
            documento.delete()
        errores = ' '.join(str(e) for e in form.errors.values())
        messages.error(request, f'No se pudo subir el documento: {errores}')

    return redirect(_volver_al_paso(tipo))


@login_required
def editar_datos(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id, postulante__usuario=request.user)

    if request.method != 'POST':
        return redirect('mis_inscripciones')

    form = DatosPersonalesForm(
        request.POST,
        instance=inscripcion.postulante,
        carreras_disponibles=_carreras_de(inscripcion.convocatoria),
    )
    if form.is_valid():
        form.save()
        request.user.telefono = form.cleaned_data.get('telefono') or ''
        request.user.save(update_fields=['telefono'])
        inscripcion.carrera = form.cleaned_data['carrera']
        inscripcion.save(update_fields=['carrera'])
        inscripcion.marcar_paso('certificado_registro', True)
        messages.success(request, 'Tus datos se guardaron. Paso 1 completado.')
    else:
        errores = ' '.join(str(e) for lista in form.errors.values() for e in lista)
        messages.error(request, f'No se pudieron guardar los datos: {errores}')

    return redirect('mis_inscripciones')


@login_required
def marcar_paso(request, inscripcion_id, tipo):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id, postulante__usuario=request.user)
    tipos = [t for t, _ in Documento.TIPO_CHOICES]

    if request.method != 'POST' or tipo not in tipos or tipo == 'certificado_registro':
        return redirect('mis_inscripciones')

    inscripcion.marcar_paso(tipo, request.POST.get('realizado') == 'on')
    return redirect(_volver_al_paso(tipo))


@login_required
def eliminar_documento(request, inscripcion_id, tipo):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id, postulante__usuario=request.user)
    tipos = [t for t, _ in Documento.TIPO_CHOICES]

    if request.method != 'POST' or tipo not in tipos:
        return redirect('mis_inscripciones')

    volver = _volver_al_paso(tipo)

    documento = Documento.objects.filter(inscripcion=inscripcion, tipo=tipo).first()
    if not documento:
        messages.info(request, 'Ese paso no tiene ningún documento subido.')
        return redirect(volver)

    if documento.estado == 'validado':
        messages.warning(request, 'Este documento ya fue validado por admisión; no se puede eliminar.')
        return redirect(volver)

    documento.archivo.delete(save=False)
    documento.delete()
    inscripcion.marcar_paso(tipo, False)
    _reabrir_si_estaba_revisada(inscripcion)
    inscripcion.actualizar_estado_por_documentos()
    messages.success(request, 'Documento eliminado. Puedes subir otro cuando quieras.')
    return redirect(volver)


@login_required
def finalizar_proceso(request):
    messages.success(request, 'Tu proceso quedó guardado. Admisión lo revisará y te avisará si necesita algo más.')
    return redirect('inicio')