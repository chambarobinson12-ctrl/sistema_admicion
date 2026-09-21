from django import template

from postulantes.models import ConfiguracionProceso
from panel.forms import ConfiguracionProcesoForm

register = template.Library()


@register.inclusion_tag('panel/_tarjeta_pasos.html', takes_context=True)
def tarjeta_pasos(context):
    form = ConfiguracionProcesoForm(instance=ConfiguracionProceso.obtener())
    pasos = [
        {
            'n': n,
            'nombre': form[f'paso{n}_nombre'],
            'documento': form[f'paso{n}_documento'],
            'ayuda': form[f'paso{n}_ayuda'],
        }
        for n in range(1, 6)
    ]
    return {'form_pasos': form, 'pasos': pasos, 'csrf_token': context.get('csrf_token')}