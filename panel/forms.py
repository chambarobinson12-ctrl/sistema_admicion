from django import forms
from django.forms import inlineformset_factory

from convocatorias.models import Carrera, Convocatoria, CupoCarrera
from evaluacion.models import Examen
from postulantes.models import ConfiguracionProceso


class CarreraForm(forms.ModelForm):
    class Meta:
        model = Carrera
        fields = ['nombre', 'codigo', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Tec. Sup. en Desarrollo de Software'}),
            'codigo': forms.TextInput(attrs={'placeholder': 'Ej. SOFT'}),
        }


class ConvocatoriaForm(forms.ModelForm):
    class Meta:
        model = Convocatoria
        fields = ['nombre', 'fecha_inicio', 'fecha_fin', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Admisión 2026-II'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }


class CupoCarreraForm(forms.ModelForm):
    class Meta:
        model = CupoCarrera
        fields = ['carrera', 'cupos']


CupoCarreraFormSet = inlineformset_factory(
    Convocatoria,
    CupoCarrera,
    form=CupoCarreraForm,
    extra=1,
    can_delete=True,
)


class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = ['nombre', 'fecha', 'hora', 'lugar']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Examen de admisión - Sede Yantzaza'}),
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'lugar': forms.TextInput(attrs={'placeholder': 'Ej. Yantzaza - Centro comercial de la ciudad'}),
        }
class ConfiguracionProcesoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionProceso
        fields = ['descripcion'] + [f'paso{n}_{campo}' for n in range(1, 6) for campo in ('nombre', 'documento', 'ayuda')]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            **{f'paso{n}_ayuda': forms.Textarea(attrs={'rows': 2}) for n in range(1, 6)},
        }