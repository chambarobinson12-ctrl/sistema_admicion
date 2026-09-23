from datetime import date
from django.shortcuts import render
from .models import Convocatoria, Carrera


CARRERAS_INFO = {
    'software': {
        'imagen': 'img/carreras/software.png',
        'resumen': 'Diseña, programa y despliega aplicaciones web y móviles desde el primer semestre.',
        'aprenderas': [
            'Programación con Python, JavaScript y bases de datos SQL',
            'Desarrollo de aplicaciones web y móviles completas, de la idea al despliegue',
            'Control de versiones, trabajo en equipo y metodologías ágiles',
        ],
        'salidas': 'Te preparamos para trabajar como desarrollador de software, analista de sistemas o soporte técnico especializado, y también para emprender tu propio negocio digital.',
        'duracion': '6 semestres',
        'modalidad': 'Presencial',
    },
    'contabilidad': {
        'imagen': 'img/carreras/contabilidad.png',
        'resumen': 'Lleva las finanzas de empresas reales: tributación, costos y estados financieros.',
        'aprenderas': [
            'Registro contable, estados financieros y análisis de costos',
            'Declaración de impuestos según la normativa vigente del SRI',
            'Manejo de software contable usado en empresas de la región',
        ],
        'salidas': 'Puedes trabajar en el área contable de empresas públicas o privadas, llevar la contabilidad de un negocio propio, o continuar estudios en auditoría.',
        'duracion': '6 semestres',
        'modalidad': 'Presencial',
    },
    'agropecuaria': {
        'imagen': 'img/carreras/agropecuaria.png',
        'resumen': 'Trabaja el suelo, los cultivos y la producción agrícola con técnicas actuales.',
        'aprenderas': [
            'Manejo de suelos, sistemas de riego y control de plagas',
            'Producción de cultivos propios de la Amazonía, como cacao y café',
            'Buenas prácticas agrícolas y comercialización de la cosecha',
        ],
        'salidas': 'Puedes administrar fincas propias o de terceros, asesorar a productores locales, o integrarte a proyectos agrícolas públicos y privados.',
        'duracion': '6 semestres',
        'modalidad': 'Presencial, con prácticas de campo',
    },
    'pecuaria': {
        'imagen': 'img/carreras/pecuaria.png',
        'resumen': 'Cría y maneja ganado y especies menores con enfoque en sanidad y productividad.',
        'aprenderas': [
            'Manejo y sanidad de ganado bovino y especies menores',
            'Nutrición animal y mejoramiento genético',
            'Producción de leche, carne y derivados con buenas prácticas',
        ],
        'salidas': 'Puedes administrar granjas ganaderas, integrarte a proyectos de producción pecuaria, o asesorar técnicamente a productores de la zona.',
        'duracion': '6 semestres',
        'modalidad': 'Presencial, con prácticas de campo',
    },
}


def clave_carrera(nombre):
    """Detecta a cuál de las 4 carreras insignia corresponde un nombre dado."""
    nombre = nombre.lower()
    if 'software' in nombre:
        return 'software'
    if 'contab' in nombre:
        return 'contabilidad'
    if 'agropecuar' in nombre:
        return 'agropecuaria'
    if 'pecuar' in nombre:
        return 'pecuaria'
    return None


def lista_carreras(request):
    """Procesos de admisión con su etiqueta (actual, nuevo o finalizado) y, dentro
    de cada uno, sus carreras. Si una carrera está pausada se muestra como
    "Cupo cerrado" y no se puede elegir para postular."""
    convocatorias = Convocatoria.objects.filter(activa=True).prefetch_related('cupocarrera_set__carrera')
    hoy = date.today()

    for conv in convocatorias:
        conv.tarjetas = []
        for cupo in conv.cupocarrera_set.all():
            clave = clave_carrera(cupo.carrera.nombre)
            conv.tarjetas.append({
                'carrera': cupo.carrera,
                'cupos': cupo.cupos,
                'clave': clave,
                'info': CARRERAS_INFO.get(clave),
                'pausada': not cupo.carrera.activa,
                'malla_url': cupo.carrera.malla_curricular.url if cupo.carrera.malla_curricular else '',
            })

        if conv.fecha_fin < hoy:
            conv.etiqueta, conv.etiqueta_clase = 'Proceso finalizado', 'etiqueta-cerrado'
        elif conv.fecha_inicio > hoy:
            conv.etiqueta, conv.etiqueta_clase = 'Nuevo proceso', 'etiqueta-nuevo'
        else:
            conv.etiqueta, conv.etiqueta_clase = 'Proceso actual', 'etiqueta-actual'

    # Carreras que sí se pueden elegir al postular (proceso vigente y carrera activa)
    activa = Convocatoria.objects.filter(activa=True).order_by('fecha_fin').first()
    ids_carrera = {}
    if activa:
        for cupo in activa.cupocarrera_set.select_related('carrera'):
            if not cupo.carrera.activa:
                continue
            clave = clave_carrera(cupo.carrera.nombre)
            if clave:
                ids_carrera[clave] = cupo.carrera_id

    # Malla curricular de cada carrera (la que el administrador subió en Carreras)
    mallas = {}
    for carrera in Carrera.objects.exclude(malla_curricular='').exclude(malla_curricular__isnull=True):
        clave = clave_carrera(carrera.nombre)
        if clave and clave not in mallas:
            mallas[clave] = carrera.malla_curricular.url

    modales = {
        clave: dict(info, carrera_id=ids_carrera.get(clave), malla_url=mallas.get(clave, ''))
        for clave, info in CARRERAS_INFO.items()
    }

    return render(request, 'convocatorias/lista_carreras.html', {
        'convocatorias': convocatorias,
        'carreras_info': modales,
    })