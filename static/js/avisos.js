/* =====================================================================
   AVISOS DEL SISTEMA (SweetAlert2)
   Reemplaza los cuadros del navegador (alert / confirm) por avisos
   propios con el diseño del sistema: https://sweetalert2.github.io/

   CÓMO USARLO EN UNA PLANTILLA (sin escribir JavaScript):

   1) Pedir confirmación antes de enviar un formulario:
      <form method="post" action="..."
            data-confirmar-titulo="¿Eliminar procesos?"
            data-confirmar-texto="Esta acción no se puede deshacer."
            data-confirmar-boton="Sí, eliminar"
            data-confirmar-peligro="1">          (botón rojo)

   2) Exigir que haya casillas marcadas (cuenta también las que están
      fuera del <form> pero unidas con form="id"):
            data-confirmar-validar-grupo="convocatorias"
            data-confirmar-validar-mensaje="Marca al menos un proceso."
            data-confirmar-texto-plantilla="¿Eliminar {n} proceso(s)?"

   3) Exigir que un campo tenga valor (p. ej. un <select>):
            data-confirmar-requerido="destino"
            data-confirmar-requerido-mensaje="Elige un proceso."
      y en el texto se puede usar {destino} para mostrar la opción elegida.

   4) Confirmar antes de seguir un enlace:
      <a href="..." data-confirmar-texto="¿Salir sin guardar?">Cancelar</a>
   ===================================================================== */
(function () {
    if (typeof Swal === 'undefined') {
        console.warn('SweetAlert2 no está cargado. Revisa el <script> en base.html / base_panel.html.');
        return;
    }

    // Colores tomados de estilos.css (:root)
    var COLOR_CONFIRMAR = '#558B2F';   // --primario
    var COLOR_CANCELAR = '#8A9880';    // gris verdoso, neutro
    var COLOR_PELIGRO = '#C6402F';     // --peligro

    /**
     * Cuadro de confirmación. Devuelve una Promise<boolean>.
     * options: { titulo, texto, icono, textoConfirmar, textoCancelar, peligro }
     */
    window.confirmarAviso = function (options) {
        options = options || {};
        return Swal.fire({
            title: options.titulo || '¿Estás seguro?',
            html: options.texto || '',
            icon: options.icono || (options.peligro ? 'warning' : 'question'),
            showCancelButton: true,
            confirmButtonText: options.textoConfirmar || 'Sí, continuar',
            cancelButtonText: options.textoCancelar || 'Cancelar',
            confirmButtonColor: options.peligro ? COLOR_PELIGRO : COLOR_CONFIRMAR,
            cancelButtonColor: COLOR_CANCELAR,
            reverseButtons: true,
            focusCancel: !!options.peligro,
        }).then(function (r) { return r.isConfirmed; });
    };

    /** Aviso simple (reemplaza a alert()). */
    window.avisar = function (texto, icono) {
        return Swal.fire({
            title: texto,
            icon: icono || 'info',
            confirmButtonText: 'Entendido',
            confirmButtonColor: COLOR_CONFIRMAR,
        });
    };

    /** Mensaje corto que desaparece solo (arriba a la derecha). */
    window.avisoRapido = function (texto, icono) {
        return Swal.fire({
            toast: true,
            position: 'top-end',
            icon: icono || 'success',
            title: texto,
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
        });
    };

    // Cualquier alert() que quede suelto en el sistema también usa SweetAlert
    window.alert = function (texto) { window.avisar(String(texto), 'warning'); };

    function escaparHTML(texto) {
        var div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }

    // Cuenta las casillas marcadas de un grupo, incluidas las que están
    // fuera del <form> pero unidas con form="id-del-form".
    function contarMarcados(form, nombreGrupo) {
        var campos = Array.prototype.filter.call(form.elements, function (el) {
            return el.name === nombreGrupo;
        });
        if (campos.length === 0) {
            campos = Array.prototype.slice.call(document.querySelectorAll('[name="' + nombreGrupo + '"]'));
        }
        return campos.filter(function (el) { return el.checked; }).length;
    }

    // ---------------------------------------------------------------
    // Formularios con data-confirmar-*  (delegado: sirve también para
    // formularios que se agregan después de cargar la página)
    // ---------------------------------------------------------------
    document.addEventListener('submit', function (e) {
        var form = e.target;
        if (!(form instanceof HTMLFormElement)) return;
        var d = form.dataset;
        if (!d.confirmarTexto && !d.confirmarTextoPlantilla && !d.confirmarTitulo) return;

        if (d.avisoConfirmado === '1') {       // ya se confirmó: dejar pasar
            d.avisoConfirmado = '';
            return;
        }
        e.preventDefault();
        var boton = e.submitter || null;

        // 1) Casillas obligatorias
        var n = '';
        if (d.confirmarValidarGrupo) {
            n = contarMarcados(form, d.confirmarValidarGrupo);
            if (n === 0) {
                avisar(d.confirmarValidarMensaje || 'Marca al menos una opción.', 'warning');
                return;
            }
        }

        // 2) Campo obligatorio (p. ej. el proceso destino)
        var textoCampo = '';
        if (d.confirmarRequerido) {
            var campo = form.elements[d.confirmarRequerido];
            if (!campo || !campo.value) {
                avisar(d.confirmarRequeridoMensaje || 'Completa la información requerida.', 'warning');
                return;
            }
            textoCampo = campo.options ? campo.options[campo.selectedIndex].text : campo.value;
        }

        // 3) Texto del aviso
        var texto = d.confirmarTextoPlantilla || d.confirmarTexto || '';
        texto = escaparHTML(texto).replace('{n}', n).replace('{destino}', '<b>' + escaparHTML(textoCampo) + '</b>');

        confirmarAviso({
            titulo: d.confirmarTitulo || '¿Estás seguro?',
            texto: texto,
            icono: d.confirmarIcono,
            textoConfirmar: d.confirmarBoton || 'Sí, continuar',
            peligro: d.confirmarPeligro === '1',
        }).then(function (ok) {
            if (!ok) return;
            d.avisoConfirmado = '1';
            if (form.requestSubmit) {
                // se reenvía con el mismo botón (conserva name/value del botón)
                boton && boton.form === form ? form.requestSubmit(boton) : form.requestSubmit();
            } else {
                form.submit();
            }
        });
    }, true);

    // ---------------------------------------------------------------
    // Enlaces con data-confirmar-texto (p. ej. "Cancelar", "Eliminar")
    // ---------------------------------------------------------------
    document.addEventListener('click', function (e) {
        var enlace = e.target.closest('a[data-confirmar-texto]');
        if (!enlace) return;
        e.preventDefault();
        var d = enlace.dataset;
        confirmarAviso({
            titulo: d.confirmarTitulo || '¿Estás seguro?',
            texto: escaparHTML(d.confirmarTexto),
            icono: d.confirmarIcono,
            textoConfirmar: d.confirmarBoton || 'Sí, continuar',
            peligro: d.confirmarPeligro === '1',
        }).then(function (ok) {
            if (ok) window.location.href = enlace.href;
        });
    });
})();
