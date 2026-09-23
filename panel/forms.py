from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet

from convocatorias.models import Carrera, Convocatoria, CupoCarrera
from evaluacion.models import Examen
from postulantes.models import ConfiguracionProceso


# ============================================================
# FORMULARIO DE CARRERA
# ============================================================

class CarreraForm(forms.ModelForm):

    class Meta:
        model = Carrera

        fields = [
            'nombre',
            'codigo',
            'activa',
            'malla_curricular',
        ]

        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'placeholder':
                        'Ej. Tec. Sup. en Desarrollo de Software'
                }
            ),

            'codigo': forms.TextInput(
                attrs={
                    'placeholder':
                        'Ej. SOFT'
                }
            ),

            'malla_curricular': forms.ClearableFileInput(
                attrs={
                    'accept': '.pdf,.jpg,.jpeg,.png'
                }
            ),
        }

    def clean_malla_curricular(self):
        archivo = self.cleaned_data.get('malla_curricular')
        # Límite de 10 MB para que la descarga sea rápida
        if archivo and hasattr(archivo, 'size') and archivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError('El archivo es muy grande. El máximo es 10 MB.')
        return archivo


# ============================================================
# FORMULARIO DE CONVOCATORIA
# ============================================================

class ConvocatoriaForm(forms.ModelForm):

    class Meta:
        model = Convocatoria

        fields = [
            'nombre',
            'fecha_inicio',
            'fecha_fin',
            'activa',
        ]

        widgets = {

            'nombre': forms.TextInput(
                attrs={
                    'placeholder':
                        'Ej. Admisión 2026-II'
                }
            ),

            'fecha_inicio': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),

            'fecha_fin': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),
        }


# ============================================================
# FORMULARIO DE CUPOS POR CARRERA
# ============================================================

class CupoCarreraForm(forms.ModelForm):

    class Meta:
        model = CupoCarrera

        fields = [
            'carrera',
            'cupos',
        ]

        widgets = {

            'carrera': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'cupos': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 1,
                    'placeholder': 'Ej. 30'
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs
        )

        # Las carreras disponibles inicialmente
        # son las activas.
        self.fields['carrera'].queryset = (
            Carrera.objects
            .filter(activa=True)
            .order_by('nombre')
        )


# ============================================================
# FORMSET PERSONALIZADO DE CARRERAS Y CUPOS
# ============================================================

class CupoCarreraBaseFormSet(BaseInlineFormSet):

    def __init__(
        self,
        *args,
        **kwargs
    ):

        instance = kwargs.get(
            'instance'
        )

        # ----------------------------------------------------
        # NUEVO PROCESO
        # ----------------------------------------------------
        #
        # Cuando todavía no existe una convocatoria,
        # creamos automáticamente una fila por cada
        # carrera activa.
        #
        if not instance or not instance.pk:

            cantidad_carreras = (
                Carrera.objects
                .filter(activa=True)
                .count()
            )

            self.extra = cantidad_carreras

        else:

            # Al editar un proceso:
            # - se mantienen las carreras existentes
            # - dejamos una fila adicional para poder agregar otra
            self.extra = 1

        super().__init__(
            *args,
            **kwargs
        )

        # ----------------------------------------------------
        # NUEVO PROCESO: PRECARGAR LAS CARRERAS ACTIVAS
        # ----------------------------------------------------

        if not self.is_bound and (
            not instance or not instance.pk
        ):

            carreras_activas = list(
                Carrera.objects
                .filter(activa=True)
                .order_by('nombre')
            )

            for formulario, carrera in zip(
                self.forms,
                carreras_activas
            ):

                formulario.initial['carrera'] = (
                    carrera.id
                )


    def clean(self):

        cleaned_data = super().clean()

        carreras = set()

        for formulario in self.forms:

            if (
                not formulario.cleaned_data
                or formulario.cleaned_data.get('DELETE')
            ):
                continue

            carrera = formulario.cleaned_data.get(
                'carrera'
            )

            if not carrera:
                continue

            if carrera.id in carreras:

                raise forms.ValidationError(
                    'No puedes agregar la misma carrera '
                    'más de una vez en el mismo proceso.'
                )

            carreras.add(
                carrera.id
            )

        return cleaned_data


# ============================================================
# FORMSET
# ============================================================

CupoCarreraFormSet = inlineformset_factory(
    Convocatoria,
    CupoCarrera,
    form=CupoCarreraForm,
    formset=CupoCarreraBaseFormSet,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)


# ============================================================
# FORMULARIO DE EXAMEN
# ============================================================

class ExamenForm(forms.ModelForm):

    class Meta:
        model = Examen

        fields = [
            'nombre',
            'fecha',
            'hora',
            'lugar',
        ]

        widgets = {

            'nombre': forms.TextInput(
                attrs={
                    'placeholder':
                        'Ej. Examen de admisión - Sede Yantzaza'
                }
            ),

            'fecha': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),

            'hora': forms.TimeInput(
                attrs={
                    'type': 'time'
                }
            ),

            'lugar': forms.TextInput(
                attrs={
                    'placeholder':
                        'Ej. Yantzaza - Centro comercial de la ciudad'
                }
            ),
        }


# ============================================================
# CONFIGURACIÓN DEL PROCESO
# ============================================================

class ConfiguracionProcesoForm(forms.ModelForm):

    class Meta:

        model = ConfiguracionProceso

        fields = (
            ['descripcion']
            +
            [
                f'paso{n}_{campo}'
                for n in range(1, 6)
                for campo in (
                    'nombre',
                    'documento',
                    'ayuda'
                )
            ]
        )

        widgets = {

            'descripcion': forms.Textarea(
                attrs={
                    'rows': 3
                }
            ),

            **{
                f'paso{n}_ayuda':
                forms.Textarea(
                    attrs={
                        'rows': 2
                    }
                )

                for n in range(1, 6)
            },
        }