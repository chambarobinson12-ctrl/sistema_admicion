import datetime

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from convocatorias.models import Carrera, Convocatoria, CupoCarrera
from postulantes.models import Postulante, Inscripcion, Documento



def _pdf_de_ejemplo(texto):
    """PDF mínimo pero válido (una página con un texto), para que los
    documentos de prueba se puedan abrir en el visor del panel."""
    texto = texto.replace('\\', '').replace('(', '').replace(')', '')
    contenido = f"BT /F1 20 Tf 60 740 Td ({texto}) Tj ET".encode('latin-1', 'replace')
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(contenido)).encode() + b" >>\nstream\n" + contenido + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    salida = b"%PDF-1.4\n"
    posiciones = []
    for i, obj in enumerate(objetos, start=1):
        posiciones.append(len(salida))
        salida += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    inicio_xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for pos in posiciones:
        salida += f"{pos:010d} 00000 n \n".encode()
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n".encode()
    return salida

class Command(BaseCommand):
    help = "Crea carreras, una convocatoria activa y postulantes de ejemplo para ver el panel con datos reales."

    def handle(self, *args, **options):
        Usuario = get_user_model()
        hoy = timezone.now().date()

        # 1) Carreras -------------------------------------------------------
        datos_carreras = [
            ("Tec. Sup. en Desarrollo de Software", "SOFT"),
            ("Tec. Sup. en Contabilidad", "CONT"),
            ("Tec. Sup. en Agropecuaria", "AGRO"),
            ("Tec. Sup. en Pecuaria", "PEC"),
        ]
        carreras = {}
        for nombre, codigo in datos_carreras:
            carrera, creada = Carrera.objects.get_or_create(
                codigo=codigo, defaults={"nombre": nombre, "activa": True}
            )
            carreras[codigo] = carrera
            self.stdout.write(f"{'Creada' if creada else 'Ya existía'}: carrera {nombre}")

        # 2) Convocatoria activa ---------------------------------------------
        convocatoria, creada = Convocatoria.objects.get_or_create(
            nombre="Admisión 2026-I",
            defaults={
                "fecha_inicio": hoy - datetime.timedelta(days=20),
                "fecha_fin": hoy + datetime.timedelta(days=20),
                "activa": True,
            },
        )
        self.stdout.write(f"{'Creada' if creada else 'Ya existía'}: convocatoria {convocatoria.nombre}")

        # 3) Cupos por carrera ------------------------------------------------
        cupos_por_codigo = {"SOFT": 90, "CONT": 60, "AGRO": 70, "PEC": 60}
        for codigo, cupos in cupos_por_codigo.items():
            CupoCarrera.objects.get_or_create(
                convocatoria=convocatoria, carrera=carreras[codigo], defaults={"cupos": cupos}
            )

        # 4) Usuario administrador de ejemplo --------------------------------
        if not Usuario.objects.filter(username="admin_demo").exists():
            Usuario.objects.create_user(
                username="admin_demo",
                email="admin_demo@istam.edu.ec",
                password="Demo12345",
                rol="admin_admision",
                cedula="9999999999",
            )
            self.stdout.write(self.style.SUCCESS(
                "Creado usuario administrador: admin_demo / Demo12345"
            ))
        else:
            self.stdout.write("Ya existía el usuario admin_demo")

        # 5) Postulantes de ejemplo, cada uno en una etapa distinta ----------
        archivo_falso = lambda nombre: ContentFile(
            _pdf_de_ejemplo(f"Documento de ejemplo: {nombre}"), name=nombre
        )

        postulantes_demo = [
            {
                "username": "maria_demo", "cedula": "1350246789",
                "nombres": "María Fernanda", "apellidos": "Cedeño Vera",
                "genero": "femenino", "carrera": "SOFT",
                "colegio": "U.E. Eloy Alfaro", "direccion": "Cdla. Los Ceibos, Manta",
                "estado_final": "en_revision", "docs": "todos_pendientes_revision",
            },
            {
                "username": "carlos_demo", "cedula": "1309874521",
                "nombres": "Carlos Andrés", "apellidos": "Mendoza Loor",
                "genero": "masculino", "carrera": "AGRO",
                "colegio": "U.E. 24 de Mayo", "direccion": "Vía a Charapotó, Manta",
                "estado_final": "aprobada", "docs": "todos_validados",
            },
            {
                "username": "genesis_demo", "cedula": "1312589634",
                "nombres": "Génesis Paola", "apellidos": "Zambrano Ponce",
                "genero": "femenino", "carrera": "PEC",
                "colegio": "U.E. Rocafuerte", "direccion": "Rocafuerte, Manabí",
                "estado_final": "docs_pendientes", "docs": "parcial",
            },
            {
                "username": "jonathan_demo", "cedula": "1318452297",
                "nombres": "Jonathan David", "apellidos": "Alcívar Bravo",
                "genero": "masculino", "carrera": "CONT",
                "colegio": "U.E. Eloy Alfaro", "direccion": "Manta",
                "estado_final": "rechazada", "docs": "uno_rechazado",
            },
        ]

        tipos_doc = [t for t, _ in Documento.TIPO_CHOICES]

        for datos in postulantes_demo:
            if Usuario.objects.filter(username=datos["username"]).exists():
                self.stdout.write(f"Ya existía el postulante {datos['username']}")
                continue

            usuario = Usuario.objects.create_user(
                username=datos["username"],
                email=f"{datos['username']}@example.com",
                password="Demo12345",
                rol="postulante",
                cedula=datos["cedula"],
                telefono="0999999999",
            )
            postulante = Postulante.objects.create(
                usuario=usuario,
                nombres=datos["nombres"],
                apellidos=datos["apellidos"],
                fecha_nacimiento=datetime.date(2008, 3, 14),
                genero=datos["genero"],
                direccion=datos["direccion"],
                colegio_procedencia=datos["colegio"],
            )
            inscripcion = Inscripcion.objects.create(
                postulante=postulante,
                convocatoria=convocatoria,
                carrera=carreras[datos["carrera"]],
            )

            if datos["docs"] == "todos_pendientes_revision":
                for tipo in tipos_doc:
                    Documento.objects.create(
                        inscripcion=inscripcion, tipo=tipo,
                        archivo=archivo_falso(f"{tipo}.pdf"),
                        estado="pendiente_revision",
                    )
            elif datos["docs"] == "todos_validados":
                for tipo in tipos_doc:
                    Documento.objects.create(
                        inscripcion=inscripcion, tipo=tipo,
                        archivo=archivo_falso(f"{tipo}.pdf"),
                        estado="validado",
                    )
            elif datos["docs"] == "parcial":
                for tipo in tipos_doc[:2]:
                    Documento.objects.create(
                        inscripcion=inscripcion, tipo=tipo,
                        archivo=archivo_falso(f"{tipo}.pdf"),
                        estado="pendiente_revision",
                    )
            elif datos["docs"] == "uno_rechazado":
                for i, tipo in enumerate(tipos_doc):
                    Documento.objects.create(
                        inscripcion=inscripcion, tipo=tipo,
                        archivo=archivo_falso(f"{tipo}.pdf"),
                        estado="rechazado" if i == 0 else "validado",
                        observaciones="Foto ilegible, sube una versión más clara." if i == 0 else "",
                    )

            inscripcion.estado = datos["estado_final"]
            inscripcion.save(update_fields=["estado"])

            self.stdout.write(self.style.SUCCESS(
                f"Creado postulante {datos['nombres']} {datos['apellidos']} ({inscripcion.numero_postulacion})"
            ))

        self.stdout.write(self.style.SUCCESS("\nListo. Datos de ejemplo creados."))
        self.stdout.write("Entra al panel en /panel/ con: admin_demo / Demo12345")
        self.stdout.write("O como postulante en /postulantes/mis-inscripciones/ con: maria_demo / Demo12345")