from django.db import migrations, models


class Migration(migrations.Migration):
    """Los documentos que se piden ahora son los certificados de cada paso del
    proceso (registro, inscripción, evaluación, postulación y aceptación).
    Solo cambian las opciones: los documentos ya subidos no se borran."""

    dependencies = [
        ('postulantes', '0002_alter_documento_options_alter_inscripcion_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documento',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('certificado_registro', 'Certificado de registro'),
                    ('certificado_inscripcion', 'Certificado de inscripción'),
                    ('evaluacion', 'Evaluación (nota obtenida)'),
                    ('certificado_postulacion', 'Registro de postulación a la carrera'),
                    ('certificado_aceptacion', 'Certificado de aceptación del cupo'),
                ],
                max_length=25,
            ),
        ),
    ]
