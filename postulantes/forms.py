from django import forms
from .models import Postulante, Documento


class PostulacionForm(forms.ModelForm):
    """Datos personales + carrera a la que postula, usados para registrar
    al estudiante y para que el administrativo pueda ver a qué carrera
    postula cada uno. Después de este registro, el estudiante lleva el
    control de sus propios documentos en "Mis documentos"."""

    telefono = forms.CharField(label='Teléfono', max_length=15, required=False)
    carrera = forms.ModelChoiceField(
        queryset=None,
        label='Carrera',
        empty_label=None,
        widget=forms.RadioSelect,
    )
    acepto_terminos = forms.BooleanField(
        label='Declaro que la información proporcionada es verídica y acepto los términos del proceso de admisión.',
        required=True,
    )

    class Meta:
        model = Postulante
        fields = ['nombres', 'apellidos', 'fecha_nacimiento', 'genero', 'direccion', 'colegio_procedencia', 'foto']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'foto': forms.ClearableFileInput(attrs={'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.jpg,.jpeg,.png'})
        }

    def __init__(self, *args, carreras_disponibles=None, **kwargs):
        super().__init__(*args, **kwargs)
        if carreras_disponibles is not None:
            self.fields['carrera'].queryset = carreras_disponibles
        self.fields['foto'].required = False
        self.fields['genero'].required = False
        # Reordenar para que teléfono aparezca junto a los demás datos de contacto.
        self.order_fields([
            'nombres', 'apellidos', 'fecha_nacimiento', 'genero',
            'telefono', 'direccion', 'colegio_procedencia', 'foto',
            'carrera', 'acepto_terminos',
        ])

    def clean_foto(self):
        archivo = self.cleaned_data.get('foto')
        if archivo and hasattr(archivo, 'content_type'):
            import os
            extension = os.path.splitext(archivo.name)[1].lower()
            permitidas = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.jpg', '.jpeg', '.png']
            if extension not in permitidas:
                raise forms.ValidationError('Formato no permitido. Sube un PDF, Word, Excel, PowerPoint o imagen.')
            if archivo.size > 8 * 1024 * 1024:
                raise forms.ValidationError('El archivo no debe superar los 8 MB.')
        return archivo


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['archivo']

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        limite_mb = 8
        if archivo.size > limite_mb * 1024 * 1024:
            raise forms.ValidationError(f'El archivo no debe superar los {limite_mb} MB.')

        # Solo PDF o imagen, y que el contenido sea de verdad de ese tipo
        # (si no, el panel no lo puede mostrar y el revisor ve un error).
        nombre = archivo.name.lower()
        extension = nombre.rsplit('.', 1)[-1] if '.' in nombre else ''
        firmas = {
            'pdf': [b'%PDF'],
            'jpg': [b'\xff\xd8\xff'],
            'jpeg': [b'\xff\xd8\xff'],
            'png': [b'\x89PNG'],
            'docx': [b'PK\x03\x04'],
        }
        if extension not in firmas:
            raise forms.ValidationError('Sube el documento en PDF, Word (.docx), JPG o PNG.')
        inicio = archivo.read(1024)
        archivo.seek(0)
        if not any(firma in inicio[:1024] if extension == 'pdf' else inicio.startswith(firma) for firma in firmas[extension]):
            raise forms.ValidationError(
                f'El archivo no es un .{extension} válido o está dañado. Vuelve a guardarlo o escanearlo e inténtalo de nuevo.'
            )
        return archivo
    
class DatosPersonalesForm(forms.ModelForm):
    telefono = forms.CharField(label='Teléfono', max_length=15, required=False)
    carrera = forms.ModelChoiceField(queryset=None, label='Carrera', empty_label=None)

    class Meta:
        model = Postulante
        fields = ['nombres', 'apellidos', 'fecha_nacimiento', 'genero', 'direccion', 'colegio_procedencia']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, carreras_disponibles=None, **kwargs):
        super().__init__(*args, **kwargs)
        if carreras_disponibles is not None:
            self.fields['carrera'].queryset = carreras_disponibles
        for campo in ('nombres', 'apellidos', 'fecha_nacimiento'):
            self.fields[campo].required = True
        self.fields['genero'].required = False
        self.order_fields([
            'nombres', 'apellidos', 'fecha_nacimiento', 'genero',
            'telefono', 'colegio_procedencia', 'direccion', 'carrera',
        ])