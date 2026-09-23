import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('convocatorias', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='carrera',
            name='malla_curricular',
            field=models.FileField(
                blank=True,
                help_text='PDF o imagen con la malla curricular de la carrera.',
                null=True,
                upload_to='mallas_curriculares/',
                validators=[django.core.validators.FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
                verbose_name='Malla curricular',
            ),
        ),
    ]
