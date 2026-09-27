# Reemplaza Meta.unique_together por Meta.constraints (models.UniqueConstraint),
# que es la forma recomendada en la documentación de Django 5.2.
# Primero se crea la nueva restricción y después se elimina la anterior, para que
# la tabla nunca quede sin la regla de unicidad (y para que MySQL/MariaDB conserve
# siempre un índice sobre la columna de la clave foránea).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("convocatorias", "0002_carrera_malla_curricular"),
        ("postulantes", "0008_configuracionproceso"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="inscripcion",
            constraint=models.UniqueConstraint(
                fields=("postulante", "convocatoria"),
                name="uniq_inscripcion_postulante_convocatoria",
            ),
        ),
        migrations.AddConstraint(
            model_name="documento",
            constraint=models.UniqueConstraint(
                fields=("inscripcion", "tipo"),
                name="uniq_documento_inscripcion_tipo",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="inscripcion",
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name="documento",
            unique_together=set(),
        ),
    ]
