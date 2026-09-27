"""Notificaciones por correo en los puntos clave del proceso de admisión.

Se envían en segundo plano de forma silenciosa: si el correo falla (por
ejemplo, si todavía no se ha configurado un servidor SMTP real), el proceso
de admisión sigue funcionando con normalidad y el detalle queda disponible
igual dentro del sistema.
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string


def _enviar(asunto, mensaje, destinatario):
    if not destinatario:
        return
    send_mail(
        asunto,
        mensaje,
        settings.DEFAULT_FROM_EMAIL,
        [destinatario],
        fail_silently=True,
    )


def notificar_documento(documento):
    usuario = documento.inscripcion.postulante.usuario
    nombre = usuario.first_name or usuario.username

    if documento.estado == 'validado':
        asunto = f'Documento validado: {documento.get_tipo_display()}'
        mensaje = (
            f'Hola {nombre},\n\n'
            f'Tu documento "{documento.get_tipo_display()}" de la postulación '
            f'{documento.inscripcion.numero_postulacion} fue revisado y quedó validado.\n\n'
            'Puedes ver el detalle en "Mi proceso".'
        )
    elif documento.estado == 'rechazado':
        asunto = f'Debes volver a subir: {documento.get_tipo_display()}'
        mensaje = (
            f'Hola {nombre},\n\n'
            f'Tu documento "{documento.get_tipo_display()}" de la postulación '
            f'{documento.inscripcion.numero_postulacion} fue rechazado.\n'
            f'Motivo: {documento.observaciones or "No especificado"}\n\n'
            'Ingresa a "Mi proceso" para volver a subirlo.'
        )
    else:
        return

    _enviar(asunto, mensaje, usuario.email)


def notificar_decision_inscripcion(inscripcion):
    usuario = inscripcion.postulante.usuario
    nombre = usuario.first_name or usuario.username

    if inscripcion.estado == 'aprobada':
        asunto = 'Tu postulación a ISTAM fue aprobada'
        mensaje = (
            f'Hola {nombre},\n\n'
            f'Felicitaciones. Tu postulación {inscripcion.numero_postulacion} a la carrera '
            f'{inscripcion.carrera.nombre} fue aprobada.\n\n'
            'Pronto recibirás información sobre el siguiente paso: la matriculación.'
        )
    elif inscripcion.estado == 'rechazada':
        asunto = 'Resultado de tu postulación a ISTAM'
        mensaje = (
            f'Hola {nombre},\n\n'
            f'Tu postulación {inscripcion.numero_postulacion} a la carrera '
            f'{inscripcion.carrera.nombre} no fue aprobada.\n\n'
            f'{inscripcion.comentario_revision}\n\n'
            'Si tienes dudas sobre este resultado, contáctanos usando el chat de ayuda del sitio (ícono 💬).'
        )
    else:
        return

    _enviar(asunto, mensaje, usuario.email)


def notificar_reintegro(inscripcion, proceso_anterior, concepto='', mensaje='', enlace=''):
    """Correo al postulante cuando el personal lo reintegra a un proceso nuevo.
    Lleva el motivo (concepto), un mensaje opcional del personal y los pasos a
    seguir. Devuelve False si el postulante no tiene correo registrado."""
    usuario = inscripcion.postulante.usuario
    if not usuario.email:
        return False
    nombre = inscripcion.postulante.nombres or usuario.first_name or usuario.username
    proceso = inscripcion.convocatoria
    asunto = f'Fuiste reintegrado al proceso de admisión {proceso.nombre} - ISTAM'
    contexto = {
        'nombre': nombre,
        'inscripcion': inscripcion,
        'proceso': proceso,
        'proceso_anterior': proceso_anterior,
        'concepto': concepto,
        'mensaje': mensaje,
        'enlace': enlace,
    }
    texto = render_to_string('panel/correo_reintegro.txt', contexto)
    html = render_to_string('panel/correo_reintegro.html', contexto)
    correo = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [usuario.email])
    correo.attach_alternative(html, 'text/html')
    correo.send(fail_silently=True)
    return True


def notificar_comentario(inscripcion):
    usuario = inscripcion.postulante.usuario
    nombre = usuario.first_name or usuario.username
    asunto = f'Revisa tu proceso de admisión {inscripcion.numero_postulacion} - ISTAM'
    mensaje = (
        f'Hola {nombre},\n\n'
        f'El personal de admisión revisó tu postulación a {inscripcion.carrera.nombre} '
        f'y te dejó este comentario:\n\n'
        f'"{inscripcion.comentario_revision}"\n\n'
        'Ingresa a "Mi proceso" para completar lo que falta.'
    )
    _enviar(asunto, mensaje, usuario.email)
