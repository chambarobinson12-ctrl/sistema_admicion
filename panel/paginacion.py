"""Paginación de las tablas del panel: de 10 en 10, con números (1 2 3 … 8)."""
from django.core.paginator import Paginator

POR_PAGINA = 10


def paginar(request, lista, por_pagina=POR_PAGINA, parametro='pagina'):
    """Devuelve la página pedida en ?pagina=N. A la página se le agregan:
    - rango: los números a mostrar (con '…' cuando son muchos)
    - qs: el resto de filtros de la URL, para no perderlos al cambiar de página
    """
    paginator = Paginator(lista, por_pagina)
    pagina = paginator.get_page(request.GET.get(parametro))
    pagina.rango = list(paginator.get_elided_page_range(pagina.number, on_each_side=2, on_ends=1))
    pagina.puntos = Paginator.ELLIPSIS
    parametros = request.GET.copy()
    parametros.pop(parametro, None)
    pagina.qs = parametros.urlencode()
    pagina.parametro = parametro
    return pagina
