from django.contrib import admin
from .models import Examen, Resultado


class ResultadoAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'examen', 'puntaje', 'aprobado')
    list_filter = ('examen', 'aprobado')


admin.site.register(Examen)
admin.site.register(Resultado, ResultadoAdmin)