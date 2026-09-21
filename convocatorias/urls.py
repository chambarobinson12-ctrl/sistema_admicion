from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_carreras, name='lista_carreras'),
]
