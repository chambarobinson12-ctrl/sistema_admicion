from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .forms import RecuperarContrasenaForm, NuevaContrasenaForm, CambiarContrasenaForm

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('registro/', views.registro, name='registro'),
    path('ayuda/', views.ayuda, name='ayuda'),
    path('login/', views.IngresoView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # ---- Recuperar contraseña (olvidé mi contraseña) ----
    path('recuperar-contrasena/', auth_views.PasswordResetView.as_view(
        template_name='usuarios/recuperar_contrasena.html',
        email_template_name='usuarios/correo_recuperar.txt',
        html_email_template_name='usuarios/correo_recuperar.html',
        subject_template_name='usuarios/correo_recuperar_asunto.txt',
        form_class=RecuperarContrasenaForm,
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('recuperar-contrasena/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='usuarios/recuperar_enviado.html',
    ), name='password_reset_done'),
    path('recuperar-contrasena/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='usuarios/recuperar_nueva.html',
        form_class=NuevaContrasenaForm,
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('recuperar-contrasena/listo/', auth_views.PasswordResetCompleteView.as_view(
        template_name='usuarios/recuperar_listo.html',
    ), name='password_reset_complete'),

    # ---- Cambiar contraseña (usuario con sesión iniciada) ----
    path('cambiar-contrasena/', views.CambiarContrasenaView.as_view(), name='password_change'),
]
