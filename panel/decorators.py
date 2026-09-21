from django.contrib.auth.decorators import user_passes_test


def _es_personal_admision(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, 'rol', None) == 'admin_admision')


def panel_required(view_func):
    """Solo deja pasar a administradores del proceso de admisión (o los manda al login)."""
    return user_passes_test(_es_personal_admision, login_url='login')(view_func)
