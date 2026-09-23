from django.urls import path
from . import views, views_config

app_name = 'panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('postulantes/exportar/', views.exportar_postulantes_excel, name='exportar_postulantes_excel'),
    path('postulante/<int:inscripcion_id>/', views.detalle_postulante, name='detalle_postulante'),
    path('postulante/<int:inscripcion_id>/documentos.zip', views.descargar_documentos, name='descargar_documentos'),
    path('documento/<int:documento_id>/descargar/', views.descargar_documento, name='descargar_documento'),
    path('documento/<int:documento_id>/vista/', views.vista_documento, name='vista_documento'),
    path('documento/<int:documento_id>/validar/', views.validar_documento, name='validar_documento'),
    path('postulante/<int:inscripcion_id>/decidir/', views.decidir_inscripcion, name='decidir_inscripcion'),
    path('carreras/<int:carrera_id>/estado/', views.carrera_cambiar_estado, name='carrera_cambiar_estado'),
    path('carreras/eliminar/', views.carreras_eliminar, name='carreras_eliminar'),

    path('carreras/', views.carreras_lista, name='carreras_lista'),
    path('carreras/nueva/', views.carrera_crear, name='carrera_crear'),
    path('carreras/<int:carrera_id>/editar/', views.carrera_editar, name='carrera_editar'),

    path('procesos/', views.convocatorias_lista, name='convocatorias_lista'),
    path('procesos/nuevo/', views.convocatoria_crear, name='convocatoria_crear'),
    path('procesos/<int:convocatoria_id>/', views.convocatoria_detalle, name='convocatoria_detalle'),
    path('procesos/<int:convocatoria_id>/editar/', views.convocatoria_editar, name='convocatoria_editar'),
    path('procesos/<int:convocatoria_id>/estado/', views.convocatoria_cambiar_estado, name='convocatoria_cambiar_estado'),
    path('procesos/eliminar/', views.convocatorias_eliminar, name='convocatorias_eliminar'),

    path('examenes/', views.examenes_lista, name='examenes_lista'),
    path('examenes/nuevo/', views.examen_crear, name='examen_crear'),
    path('examenes/<int:examen_id>/editar/', views.examen_editar, name='examen_editar'),

    path('reportes/', views.reportes, name='reportes'),
    path('documentos/', views_config.revisar_documentos, name='revisar_documentos'),

    path('configuracion/', views_config.configuracion, name='configuracion'),
    path('configuracion/proceso/<int:convocatoria_id>/', views.convocatoria_detalle, name='proceso_historial'),
    path('configuracion/proceso/<int:convocatoria_id>/reintegrar/', views.reintegrar_postulantes, name='reintegrar_postulantes'),
    path('configuracion/proceso/<int:convocatoria_id>/eliminar-postulantes/', views.eliminar_postulantes, name='eliminar_postulantes'),
    path('configuracion/estados/', views_config.estados_postulantes, name='estados_postulantes'),
    path('configuracion/estados/<int:inscripcion_id>/comentario/', views_config.enviar_comentario, name='enviar_comentario'),
    path('configuracion/estados/<int:inscripcion_id>/cambiar/', views_config.cambiar_estado, name='cambiar_estado'),
    path('configuracion/personal/agregar/', views_config.personal_agregar, name='personal_agregar'),
    path('configuracion/personal/<int:usuario_id>/quitar/', views_config.personal_quitar, name='personal_quitar'),
    path('configuracion/pasos/', views.config_pasos_guardar, name='config_pasos_guardar'),
]