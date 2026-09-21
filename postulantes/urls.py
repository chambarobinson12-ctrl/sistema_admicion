from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('postular/', RedirectView.as_view(pattern_name='mis_inscripciones'), name='postular'),
    path('mis-inscripciones/', views.mis_inscripciones, name='mis_inscripciones'),
    path('iniciar/', views.iniciar_postulacion, name='iniciar_postulacion'),
    path('inscripcion/<int:inscripcion_id>/documento/<str:tipo>/subir/', views.subir_documento, name='subir_documento'),
    path('inscripcion/<int:inscripcion_id>/datos/', views.editar_datos, name='editar_datos'),
    path('inscripcion/<int:inscripcion_id>/paso/<str:tipo>/marcar/', views.marcar_paso, name='marcar_paso'),
    path('inscripcion/<int:inscripcion_id>/documento/<str:tipo>/eliminar/', views.eliminar_documento, name='eliminar_documento'),
    path('finalizar/', views.finalizar_proceso, name='finalizar_proceso'),
]