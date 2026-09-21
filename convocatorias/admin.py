from django.contrib import admin
from .models import Carrera, Convocatoria, CupoCarrera

admin.site.register(Carrera)
admin.site.register(Convocatoria)
admin.site.register(CupoCarrera)