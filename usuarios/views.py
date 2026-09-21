from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import RegistroForm, CambiarContrasenaForm


class IngresoView(LoginView):
    """Login que envía a cada quien a su propia sección según su rol."""

    template_name = 'usuarios/login.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['username'].label = 'Usuario, correo o cédula'
        form.fields['username'].widget.attrs.update({'placeholder': 'Ej. jperez o jperez@correo.com'})
        form.fields['password'].widget.attrs.update({'placeholder': 'Tu contraseña'})
        form.error_messages['invalid_login'] = (
            'Los datos no coinciden. Revisa tu usuario/correo y contraseña '
            '(las mayúsculas cuentan).'
        )
        return form

    def get_success_url(self):
        usuario = self.request.user
        if usuario.is_superuser or usuario.is_staff or usuario.rol == 'admin_admision':
            return '/'
        return '/'


def inicio(request):
    return render(request, 'usuarios/inicio.html')


def ayuda(request):
    # La página estática de ayuda fue reemplazada por el chat flotante
    # disponible en todas las páginas del sitio. Cualquier enlace o marcador
    # antiguo hacia /ayuda/ ahora abre el chat directamente.
    return redirect('/?abrir_chat=1')


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cuenta creada. Ahora inicia sesión con tu correo y contraseña.')
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


class CambiarContrasenaView(LoginRequiredMixin, PasswordChangeView):
    """Permite a cualquier usuario con sesión iniciada cambiar su contraseña."""

    template_name = 'usuarios/cambiar_contrasena.html'
    form_class = CambiarContrasenaForm

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, 'Tu contraseña se cambió correctamente.')
        return respuesta

    def get_success_url(self):
        usuario = self.request.user
        if usuario.is_superuser or usuario.is_staff or usuario.rol == 'admin_admision':
            return '/panel/'
        return '/postulantes/mis-inscripciones/'
