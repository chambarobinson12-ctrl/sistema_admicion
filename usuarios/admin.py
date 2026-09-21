from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

admin.site.site_header = "Instituto Superior Tecnológico Amazónico · Panel administrativo"
admin.site.site_title = "ISTAM Admisión"
admin.site.index_title = "Gestión del proceso de admisión"

admin.site.register(Usuario, UserAdmin)