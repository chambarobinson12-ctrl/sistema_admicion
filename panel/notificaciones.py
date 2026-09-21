"""Notificaciones por correo en los puntos clave del proceso de admisión.

Se envían en segundo plano de forma silenciosa: si el correo falla (por
ejemplo, si todavía no se ha configurado un servidor SMTP real), el proceso
de admisión sigue funcionando con normalidad y el detalle queda disponible
igual dentro del sistema.
"""

from django.conf import settings
from django.core.mail import send_mail


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
            'Puedes ver el detalle en "Mis documentos".'
        )
    elif documento.estado == 'rechazado':
        asunto = f'Debes volver a subir: {documento.get_tipo_display()}'
        mensaje = (
            f'Hola {nombre},\n\n'
            f'Tu documento "{documento.get_tipo_display()}" de la postulación '
            f'{documento.inscripcion.numero_postulacion} fue rechazado.\n'
            f'Motivo: {documento.observaciones or "No especificado"}\n\n'
            'Ingresa a "Mis documentos" para volver a subirlo.'
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
            'Si tienes dudas sobre este resultado, contáctanos usando el chat de ayuda del sitio (ícono 💬).'
        )
    else:
        return

    _enviar(asunto, mensaje, usuario.email)


def notificar_reintegro(inscripcion, proceso_anterior):
    usuario = inscripcion.postulante.usuario
    nombre = usuario.first_name or usuario.username
    asunto = f'Fuiste reintegrado al proceso {inscripcion.convocatoria.nombre} - ISTAM'
    mensaje = (
        f'Hola {nombre},\n\n'
        f'Te informamos que fuiste inscrito nuevamente en el proceso de admisión '
        f'"{inscripcion.convocatoria.nombre}" para la carrera {inscripcion.carrera.nombre} '
        f'(antes participaste en "{proceso_anterior.nombre}").\n\n'
        f'Tu nuevo número de postulación es {inscripcion.numero_postulacion}.\n'
        'Ingresa a "Mis documentos" para revisar qué documentos debes completar.'
    )
    _enviar(asunto, mensaje, usuario.email)


def notificar_comentario(inscripcion):
    usuario = inscripcion.postulante.usuario
    nombre = usuario.first_name or usuario.username
    asunto = f'Revisa tu proceso de admisión {inscripcion.numero_postulacion} - ISTAM'
    mensaje = (
        f'Hola {nombre},\n\n'
        f'El personal de admisión revisó tu postulación a {inscripcion.carrera.nombre} '
        f'y te dejó este comentario:\n\n'
        f'"{inscripcion.comentario_revision}"\n\n'
        'Ingresa a "Mis documentos" para completar lo que falta.'
    )
    _enviar(asunto, mensaje, usuario.email)
