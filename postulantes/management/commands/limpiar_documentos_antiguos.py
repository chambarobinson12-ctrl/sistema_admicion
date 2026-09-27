"""Borra los documentos del sistema anterior (cédula, certificado de
votación, acta de grado y foto tamaño carnet), que ya no forman parte
de los 5 pasos del proceso de admisión.

Uso:
    python manage.py limpiar_documentos_antiguos             (solo muestra cuántos hay)
    python manage.py limpiar_documentos_antiguos --confirmar (los borra, con sus archivos)
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from postulantes.models import Documento, Inscripcion


class Command(BaseCommand):
    help = 'Borra los documentos de tipos antiguos (cédula, votación, acta de grado, foto).'

    def add_arguments(self, parser):
        parser.add_argument('--confirmar', action='store_true', help='Borrar de verdad (sin esto solo muestra el resumen).')

    def handle(self, *args, **opciones):
        tipos_actuales = [t for t, _ in Documento.TIPO_CHOICES]
        antiguos = Documento.objects.exclude(tipo__in=tipos_actuales).select_related('inscripcion__postulante')
        total = antiguos.count()

        if not total:
            self.stdout.write(self.style.SUCCESS('No hay documentos antiguos. Todo está limpio.'))
            return

        self.stdout.write(f'Documentos antiguos encontrados: {total}')
        for tipo, nombre in Documento.TIPOS_ANTERIORES.items():
            n = antiguos.filter(tipo=tipo).count()
            if n:
                self.stdout.write(f'  - {nombre}: {n}')

        if not opciones['confirmar']:
            self.stdout.write(self.style.WARNING(
                '\nNo se borró nada. Para borrarlos (con sus archivos) ejecuta:\n'
                '  python manage.py limpiar_documentos_antiguos --confirmar'
            ))
            return

        afectadas = set(antiguos.values_list('inscripcion_id', flat=True))
        archivos = [d.archivo for d in antiguos if d.archivo]
        with transaction.atomic():
            antiguos.delete()
            # El estado de cada postulación se recalcula solo con los 5 pasos actuales
            for inscripcion in Inscripcion.objects.filter(id__in=afectadas).prefetch_related('documentos'):
                inscripcion.actualizar_estado_por_documentos()
        for archivo in archivos:
            try:
                archivo.delete(save=False)
            except Exception:
                pass
        self.stdout.write(self.style.SUCCESS(f'Listo: se borraron {total} documentos antiguos y sus archivos.'))
