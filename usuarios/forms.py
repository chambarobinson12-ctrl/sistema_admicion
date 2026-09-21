from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario


class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True, label='Correo electrónico',
        help_text='Úsalo con cuidado: aquí te llegarán los avisos y el enlace para recuperar tu contraseña.',
    )
    cedula = forms.CharField(required=True, label='Cédula', max_length=15)
    telefono = forms.CharField(required=False, label='Teléfono', max_length=15)

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'cedula', 'telefono', 'password1', 'password2')

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.cedula = self.cleaned_data['cedula']
        usuario.telefono = self.cleaned_data.get('telefono', '')
        usuario.rol = 'postulante'
        if commit:
            usuario.save()
        return usuario

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta registrada con este correo. Si olvidaste tu contraseña, usa "¿Olvidaste tu contraseña?" en la pantalla de inicio de sesión.')
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data['cedula'].strip()
        if Usuario.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError('Ya existe una cuenta registrada con esta cédula.')
        return cedula

# ---------------- Recuperación y cambio de contraseña ----------------

from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, PasswordChangeForm


class RecuperarContrasenaForm(PasswordResetForm):
    email = forms.EmailField(
        label='Correo electrónico',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'tucorreo@ejemplo.com',
            'autofocus': True,
        }),
    )


class NuevaContrasenaForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password2'].label = 'Confirma la nueva contraseña'


class CambiarContrasenaForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Contraseña actual'
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password2'].label = 'Confirma la nueva contraseña'
