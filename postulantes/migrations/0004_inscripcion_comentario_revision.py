from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('postulantes', '0003_documento_tipos_por_pasos'),
    ]

    operations = [
        migrations.AddField(
            model_name='inscripcion',
            name='comentario_revision',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='inscripcion',
            name='fecha_comentario',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
