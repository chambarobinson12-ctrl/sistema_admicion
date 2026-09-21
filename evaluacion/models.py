from django.db import models
from postulantes.models import Inscripcion


class Examen(models.Model):
    nombre = models.CharField(max_length=100)
    fecha = models.DateField()
    hora = models.TimeField()
    lugar = models.CharField(max_length=150)
    class Meta:
        verbose_name = 'Examen'
        verbose_name_plural = 'Exámenes'
        
    def __str__(self):
        return f"{self.nombre} - {self.fecha}"


class Resultado(models.Model):
    inscripcion = models.OneToOneField(Inscripcion, on_delete=models.CASCADE)
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    puntaje = models.DecimalField(max_digits=5, decimal_places=2)
    aprobado = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.inscripcion} - {self.puntaje}"