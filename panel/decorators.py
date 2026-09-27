from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def _es_personal_admision(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, 'rol', None) == 'admin_admision')


def es_admin_principal(user):
    """Administrador principal: puede ver y cambiar todo en el panel."""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


# Páginas que solo sirven para crear algo nuevo: el administrador
# secundario no las puede abrir (las de "editar" sí, pero solo para ver).
VISTAS_SOLO_PRINCIPAL = {'carrera_crear', 'convocatoria_crear', 'examen_crear'}


def _solo_lectura_para_secundario(view_func):
    """El administrador secundario (rol 'admin_admision') puede VER todo el
    panel, pero no guardar, editar, eliminar ni aprobar nada: cualquier
    envío de formulario (POST) se bloquea aquí, antes de llegar a la vista."""
    @wraps(view_func)
    def envoltura(request, *args, **kwargs):
        if not es_admin_principal(request.user):
            nombre_vista = getattr(request.resolver_match, 'url_name', '')
            if request.method not in ('GET', 'HEAD', 'OPTIONS') or nombre_vista in VISTAS_SOLO_PRINCIPAL:
                messages.warning(
                    request,
                    'Tu cuenta es de administrador secundario: solo puedes ver la información, no hacer cambios.'
                )
                anterior = request.META.get('HTTP_REFERER', '')
                if anterior and url_has_allowed_host_and_scheme(anterior, allowed_hosts={request.get_host()}):
                    return redirect(anterior)
                return redirect('panel:dashboard')
        return view_func(request, *args, **kwargs)
    return envoltura


def panel_required(view_func):
    """Solo deja pasar a administradores del proceso de admisión (o los manda al login).
    El administrador secundario entra en modo solo lectura."""
    return user_passes_test(_es_personal_admision, login_url='login')(
        _solo_lectura_para_secundario(view_func)
    )