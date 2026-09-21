from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    ROL_CHOICES = (
        ('postulante', 'Postulante'),
        ('admin_admision', 'Administrativo'),
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='postulante')
    cedula = models.CharField(max_length=15, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.username} ({self.rol})"

    @property
    def rol_visible(self):
        """Rol que se muestra en pantalla. Un superusuario o staff creado con
        createsuperuser queda con rol 'postulante' por defecto; en el panel
        debe verse como Administrador, no como Postulante."""
        if self.rol == 'admin_admision':
            return 'Administrativo'
        if self.is_superuser or self.is_staff:
            return 'Administrador'
        return self.get_rol_display()
