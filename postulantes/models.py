from django.db import models
from django.conf import settings
from django.utils import timezone
from convocatorias.models import Convocatoria, Carrera


class Postulante(models.Model):
    GENERO_CHOICES = (
        ('femenino', 'Femenino'),
        ('masculino', 'Masculino'),
        ('otro', 'Otro'),
    )

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombres = models.CharField(max_length=100, blank=True)
    apellidos = models.CharField(max_length=100, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=15, choices=GENERO_CHOICES, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    colegio_procedencia = models.CharField(max_length=150, blank=True)
    foto = models.FileField(upload_to='fotos_postulantes/%Y/%m/', blank=True, null=True)

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"

    @property
    def datos_completos(self):
        return bool(self.nombres and self.apellidos and self.fecha_nacimiento)
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def iniciales(self):
        partes = f"{self.nombres} {self.apellidos}".split()
        letras = ''.join(p[0].upper() for p in partes[:2] if p)
        return letras or '??'


class Inscripcion(models.Model):
    ESTADO_CHOICES = (
        ('docs_pendientes', 'Documentos pendientes'),
        ('en_revision', 'En revisión'),
        ('aprobada', 'Revisada'),
        ('rechazada', 'Rechazada'),
    )

    postulante = models.ForeignKey(Postulante, on_delete=models.CASCADE, related_name='inscripciones')
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE)
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE)
    numero_postulacion = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='docs_pendientes')
    # Comentario que el personal de admisión le envía al postulante desde
    # "Revisar y comentar" (por ejemplo: qué paso dejó en blanco).
    comentario_revision = models.TextField(blank=True)
    fecha_comentario = models.DateTimeField(null=True, blank=True)
    pasos_marcados = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('postulante', 'convocatoria')
        ordering = ['-fecha_inscripcion']

    def __str__(self):
        return f"{self.postulante} - {self.carrera} ({self.estado})"

    def paso_marcado(self, tipo):
        return tipo in self.pasos_marcados.split(',')

    def marcar_paso(self, tipo, valor):
        actuales = [p for p in self.pasos_marcados.split(',') if p]
        if valor and tipo not in actuales:
            actuales.append(tipo)
        if not valor and tipo in actuales:
            actuales.remove(tipo)
        self.pasos_marcados = ','.join(actuales)
        self.save(update_fields=['pasos_marcados'])

    def save(self, *args, **kwargs):
        if not self.numero_postulacion:
            self.numero_postulacion = self._generar_numero_postulacion()
        super().save(*args, **kwargs)

    @staticmethod
    def _generar_numero_postulacion():
        anio = timezone.now().year
        prefijo = f"POST-{anio}-"
        ultima = (
            Inscripcion.objects.filter(numero_postulacion__startswith=prefijo)
            .order_by('-numero_postulacion')
            .first()
        )
        siguiente = 1
        if ultima:
            try:
                siguiente = int(ultima.numero_postulacion.replace(prefijo, '')) + 1
            except ValueError:
                siguiente = ultima.id + 1
        return f"{prefijo}{siguiente:05d}"

    @property
    def documentos_completos(self):
        tipos_requeridos = {t[0] for t in Documento.TIPO_CHOICES}
        tipos_subidos = set(self.documentos.values_list('tipo', flat=True))
        return tipos_requeridos.issubset(tipos_subidos)

    @property
    def avance_documentos(self):
        """Los 4 documentos requeridos con su situación, en orden:
        'subido' (✓), 'rechazado' (hay que volver a subirlo) o 'falta'."""
        cortos = {
            'certificado_registro': 'Registro', 'certificado_inscripcion': 'Inscripción',
            'evaluacion': 'Evaluación', 'certificado_postulacion': 'Postulación',
            'certificado_aceptacion': 'Aceptación',
        }
        por_tipo = {d.tipo: d for d in self.documentos.all()}
        avance = []
        for tipo, etiqueta in Documento.TIPO_CHOICES:
            doc = por_tipo.get(tipo)
            if not doc:
                situacion = 'falta'
            elif doc.estado == 'rechazado':
                situacion = 'rechazado'
            else:
                situacion = 'subido'
            avance.append({
                'tipo': tipo, 'etiqueta': etiqueta, 'corto': cortos.get(tipo, etiqueta),
                'situacion': situacion, 'documento': doc,
                     'marcado': self.paso_marcado(tipo),
            })
        return avance

    @property
    def documentos_faltantes(self):
        """Documentos que le faltan subir o que debe volver a subir."""
        return [d for d in self.avance_documentos if d['situacion'] != 'subido']

    @property
    def documentos_subidos_total(self):
        return sum(1 for d in self.avance_documentos if d['situacion'] == 'subido')

    @property
    def proceso_completo(self):
        return not self.documentos_faltantes

    @property
    def avance(self):
        """'completo', 'incompleto' o 'vacio' (todavía no sube nada)."""
        subidos = self.documentos_subidos_total
        if subidos == len(Documento.TIPO_CHOICES):
            return 'completo'
        if all(d['situacion'] == 'falta' for d in self.avance_documentos):
            return 'vacio'
        return 'incompleto'

    @property
    def documentos_validados_total(self):
        return self.documentos.filter(estado='validado').count()

    @property
    def total_documentos_requeridos(self):
        return len(Documento.TIPO_CHOICES)

    def actualizar_estado_por_documentos(self):
        """Recalcula el estado de la inscripción según cómo van sus documentos.

        No pisa una decisión final (aprobada/rechazada) ya tomada por el
        administrador: esa solo cambia cuando él aprueba o rechaza la
        postulación completa desde el panel.
        """
        if self.estado in ('aprobada', 'rechazada'):
            return

        if not self.documentos_completos:
            nuevo_estado = 'docs_pendientes'
        elif self.documentos.filter(estado='rechazado').exists():
            nuevo_estado = 'docs_pendientes'
        else:
            nuevo_estado = 'en_revision'

        if nuevo_estado != self.estado:
            self.estado = nuevo_estado
            self.save(update_fields=['estado'])


class Documento(models.Model):
    # Pasos del proceso de admisión: en cada uno el postulante sube el
    # certificado que obtuvo (registro, inscripción, evaluación con su nota,
    # postulación a la carrera y aceptación del cupo).
    TIPO_CHOICES = (
        ('certificado_registro', 'Certificado de registro'),
        ('certificado_inscripcion', 'Certificado de inscripción'),
        ('evaluacion', 'Evaluación (nota obtenida)'),
        ('certificado_postulacion', 'Registro de postulación a la carrera'),
        ('certificado_aceptacion', 'Certificado de aceptación del cupo'),
    )
    # Tipos que se pedían antes; se siguen mostrando con su nombre en los
    # documentos que ya se habían subido.
    TIPOS_ANTERIORES = {
        'cedula': 'Cédula de identidad',
        'certificado_votacion': 'Certificado de votación',
        'acta_grado': 'Acta de grado / Título de bachiller',
        'foto': 'Foto tamaño carnet',
    }
    ESTADO_CHOICES = (
        ('pendiente_revision', 'Pendiente de revisión'),
        ('validado', 'Validado'),
        ('rechazado', 'Rechazado'),
    )

    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, related_name='documentos')
    tipo = models.CharField(max_length=25, choices=TIPO_CHOICES)
    archivo = models.FileField(upload_to='documentos/%Y/%m/')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente_revision')
    observaciones = models.TextField(blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    fecha_revision = models.DateTimeField(null=True, blank=True)
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_revisados',
    )

    class Meta:
        unique_together = ('inscripcion', 'tipo')
        ordering = ['tipo']

    def get_tipo_display(self):
        return dict(self.TIPO_CHOICES).get(self.tipo) or self.TIPOS_ANTERIORES.get(self.tipo, self.tipo)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.inscripcion}"

class ConfiguracionProceso(models.Model):
    """Textos del recorrido del postulante ("Mi proceso") que el administrador
    puede cambiar desde Configuración, sin tocar el código."""
    descripcion = models.TextField(
        'Texto de introducción',
        default='Sigue los pasos de tu proceso de admisión. En cada paso marca que ya lo realizaste y sube tu documento; verás un ✓ cuando esté listo. Si admisión rechaza un documento, verás el motivo y podrás subirlo de nuevo.',
    )
    paso1_nombre = models.CharField('Nombre del paso 1', max_length=40, default='Registro')
    paso1_documento = models.CharField('Documento del paso 1', max_length=80, default='Certificado de registro')
    paso1_ayuda = models.TextField('Indicaciones del paso 1', blank=True)
    paso2_nombre = models.CharField('Nombre del paso 2', max_length=40, default='Inscripción')
    paso2_documento = models.CharField('Documento del paso 2', max_length=80, default='Certificado de inscripción')
    paso2_ayuda = models.TextField('Indicaciones del paso 2', blank=True)
    paso3_nombre = models.CharField('Nombre del paso 3', max_length=40, default='Evaluación')
    paso3_documento = models.CharField('Documento del paso 3', max_length=80, default='Evaluación (nota obtenida)')
    paso3_ayuda = models.TextField('Indicaciones del paso 3', blank=True)
    paso4_nombre = models.CharField('Nombre del paso 4', max_length=40, default='Postulación')
    paso4_documento = models.CharField('Documento del paso 4', max_length=80, default='Registro de postulación a la carrera')
    paso4_ayuda = models.TextField('Indicaciones del paso 4', blank=True)
    paso5_nombre = models.CharField('Nombre del paso 5', max_length=40, default='Aceptación')
    paso5_documento = models.CharField('Documento del paso 5', max_length=80, default='Certificado de aceptación del cupo')
    paso5_ayuda = models.TextField('Indicaciones del paso 5', blank=True)

    class Meta:
        verbose_name = 'configuración del proceso'
        verbose_name_plural = 'configuración del proceso'

    def __str__(self):
        return 'Configuración del proceso'

    @classmethod
    def obtener(cls):
        objeto, _ = cls.objects.get_or_create(pk=1)
        return objeto

    def pasos(self):
        return [
            {
                'numero': n,
                'nombre': getattr(self, f'paso{n}_nombre'),
                'documento': getattr(self, f'paso{n}_documento'),
                'ayuda': getattr(self, f'paso{n}_ayuda'),
            }
            for n in range(1, 6)
        ]
