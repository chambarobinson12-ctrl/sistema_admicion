from django.contrib import admin
from .models import Postulante, Inscripcion, Documento


class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0
    readonly_fields = ('fecha_subida', 'fecha_revision', 'revisado_por')
    fields = ('tipo', 'archivo', 'estado', 'observaciones', 'fecha_subida', 'fecha_revision', 'revisado_por')


class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('numero_postulacion', 'postulante', 'carrera', 'convocatoria', 'estado', 'fecha_inscripcion')
    list_filter = ('estado', 'convocatoria', 'carrera')
    search_fields = ('numero_postulacion', 'postulante__nombres', 'postulante__apellidos', 'postulante__usuario__cedula')
    readonly_fields = ('numero_postulacion', 'fecha_inscripcion')
    inlines = [DocumentoInline]


class PostulanteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'usuario', 'colegio_procedencia')
    search_fields = ('nombres', 'apellidos', 'usuario__cedula', 'usuario__username')


admin.site.register(Postulante, PostulanteAdmin)
admin.site.register(Inscripcion, InscripcionAdmin)
