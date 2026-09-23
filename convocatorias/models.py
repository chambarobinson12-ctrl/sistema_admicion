from django.core.validators import FileExtensionValidator
from django.db import models


class Carrera(models.Model):
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=20, unique=True)
    activa = models.BooleanField(default=True)
    malla_curricular = models.FileField(
        'Malla curricular',
        upload_to='mallas_curriculares/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='PDF o imagen con la malla curricular de la carrera.',
    )

    def __str__(self):
        return self.nombre


class Convocatoria(models.Model):
    nombre = models.CharField(max_length=150)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    carreras = models.ManyToManyField(Carrera, through='CupoCarrera')
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class CupoCarrera(models.Model):
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE)
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE)
    cupos = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.carrera} - {self.convocatoria} ({self.cupos} cupos)"