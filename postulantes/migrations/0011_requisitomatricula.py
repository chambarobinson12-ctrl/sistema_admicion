from django.db import migrations, models


REQUISITOS_INICIALES = [
    'Copia de la cédula de identidad a color',
    'Copia del certificado de votación',
    'Copia del título de bachiller o acta de grado',
    'Dos fotografías tamaño carné',
    'Certificado de aceptación del cupo',
]


def crear_requisitos(apps, schema_editor):
    Requisito = apps.get_model('postulantes', 'RequisitoMatricula')
    if not Requisito.objects.exists():
        Requisito.objects.bulk_create(
            Requisito(orden=i, nombre=nombre) for i, nombre in enumerate(REQUISITOS_INICIALES, start=1)
        )


class Migration(migrations.Migration):

    dependencies = [
        ('postulantes', '0010_tutorialinscripcion'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequisitoMatricula',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveSmallIntegerField(default=0, verbose_name='Orden')),
                ('nombre', models.CharField(max_length=200, verbose_name='Requisito')),
            ],
            options={
                'verbose_name': 'requisito de matriculación',
                'verbose_name_plural': 'requisitos de matriculación',
                'ordering': ['orden', 'id'],
            },
        ),
        migrations.RunPython(crear_requisitos, migrations.RunPython.noop),
    ]
