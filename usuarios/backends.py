from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsuarioOCorreoBackend(ModelBackend):
    """Permite iniciar sesión con el nombre de usuario, el correo o la cédula."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        Usuario = get_user_model()
        dato = username.strip()
        usuario = Usuario.objects.filter(username__iexact=dato).first()
        if usuario is None and '@' in dato:
            usuario = Usuario.objects.filter(email__iexact=dato).order_by('id').first()
        if usuario is None:
            usuario = Usuario.objects.filter(cedula=dato).first()
        if usuario is None:
            # Mismo costo de tiempo que un usuario real (evita adivinar cuentas).
            Usuario().set_password(password)
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
