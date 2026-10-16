"""Pruebas automáticas del sistema académico con distintos tipos de datos.

Usa una carpeta temporal para NO tocar los archivos reales de data/.
Ejecutar:  python pruebas.py
"""
import os
import shutil
import tempfile

from models import ModeloBase, Persona, Estudiante, Materia, Matricula
from views import (EstudianteController, MateriaController,
                   MatriculaController, CrudBase)

total = 0
fallos = 0


def verificar(descripcion, condicion):
    global total, fallos
    total += 1
    if condicion:
        print(f"  [OK]    {descripcion}")
    else:
        fallos += 1
        print(f"  [FALLA] {descripcion}")


def seccion(titulo):
    print(f"\n=== {titulo} ===")


def ultimo_id(controlador):
    return controlador.leer()[-1].id


carpeta = tempfile.mkdtemp()
try:
    ruta = lambda nombre: os.path.join(carpeta, nombre)
    estudiantes = EstudianteController(ruta("estudiantes.json"))
    materias = MateriaController(ruta("materias.json"))
    matriculas = MatriculaController(estudiantes, materias, ruta("matriculas.json"))

    # ------------------------------------------------------------------
    seccion("ESTUDIANTES · datos válidos y normalización")
    ok, msg = estudiantes.crear({"nombre": "ana", "apellido": "pérez",
                                 "email": "ANA@U.edu", "carnet": "est2026001",
                                 "carrera": "software"})
    verificar("crea estudiante válido", ok)
    e1 = estudiantes.obtener(1)
    verificar("nombre y apellido pasan a Title Case",
              e1.nombre == "Ana" and e1.apellido == "Pérez")
    verificar("email pasa a minúsculas", e1.email == "ana@u.edu")
    verificar("carnet pasa a MAYÚSCULAS", e1.carnet == "EST2026001")
    verificar("carrera pasa a Title Case", e1.carrera == "Software")
    ok, _ = estudiantes.crear({"nombre": "Luis", "apellido": "Mora",
                               "email": "luis@u.edu", "carnet": "EST2026002"})
    verificar("crea estudiante sin carrera", ok)
    verificar("etiqueta usa 'sin carrera'",
              "sin carrera" in estudiantes.obtener(2).etiqueta())
    verificar("etiqueta de Ana muestra nombre, carnet y carrera",
              estudiantes.obtener(1).etiqueta()
              == "Ana Pérez · EST2026001 · Software")

    seccion("ESTUDIANTES · datos inválidos")
    ok, msg = estudiantes.crear({"nombre": "X", "apellido": "Y",
                                 "email": "otro@u.edu", "carnet": "EST2026001"})
    verificar("rechaza carnet duplicado", not ok and "carnet" in msg)
    ok, _ = estudiantes.crear({"nombre": "X", "apellido": "Y",
                               "email": "otro@u.edu", "carnet": "est2026001"})
    verificar("rechaza carnet duplicado en minúsculas", not ok)
    ok, msg = estudiantes.crear({"nombre": "X", "apellido": "Y",
                                 "email": "ana@u.edu", "carnet": "EST9"})
    verificar("rechaza email duplicado", not ok and "ya está registrado" in msg)
    ok, _ = estudiantes.crear({"nombre": "X", "apellido": "Y",
                               "email": "ANA@U.EDU", "carnet": "EST9"})
    verificar("rechaza email duplicado con otra capitalización", not ok)
    for malo in ("sinarroba", "a@b", "@u.edu", "a@@u.edu", "a@u.", ""):
        ok, _ = estudiantes.crear({"nombre": "T", "apellido": "T",
                                   "email": malo, "carnet": "EST777"})
        verificar(f"rechaza email inválido {malo!r}", not ok)
    ok, msg = estudiantes.crear({"nombre": "T", "apellido": "T",
                                 "email": "t@u.edu"})
    verificar("rechaza si falta el carnet", not ok and "carnet" in msg)
    ok, _ = estudiantes.crear({"nombre": "T", "apellido": "T",
                               "email": "t@u.edu", "carnet": "   "})
    verificar("rechaza carnet solo con espacios", not ok)
    ok, _ = estudiantes.crear({"nombre": "   ", "apellido": "T",
                               "email": "t@u.edu", "carnet": "EST5"})
    verificar("rechaza nombre solo con espacios", not ok)
    ok, _ = estudiantes.crear({"nombre": None, "apellido": "T",
                               "email": "t@u.edu", "carnet": "EST5"})
    verificar("rechaza nombre None (no lo guarda como el texto 'None')", not ok)
    ok, _ = estudiantes.crear({"nombre": "T", "apellido": "T",
                               "email": "t@u.edu", "carnet": None})
    verificar("rechaza carnet None", not ok)
    ok, _ = estudiantes.crear({})
    verificar("rechaza diccionario vacío", not ok)
    verificar("no se crearon estudiantes de más", len(estudiantes.leer()) == 2)

    seccion("ESTUDIANTES · buscar, actualizar, eliminar")
    verificar("buscar por nombre", len(estudiantes.buscar("ana")) == 1)
    verificar("buscar por carnet (sin importar mayúsculas)",
              len(estudiantes.buscar("est2026002")) == 1)
    verificar("buscar por carrera", len(estudiantes.buscar("soft")) == 1)
    verificar("buscar por email parcial", len(estudiantes.buscar("u.edu")) == 2)
    verificar("un estudiante que coincide en varios campos sale una sola vez",
              len(estudiantes.buscar("a")) == len(set(e.id for e in estudiantes.buscar("a"))))
    verificar("buscar texto vacío devuelve lista vacía",
              estudiantes.buscar("") == [])
    verificar("buscar sin coincidencias", estudiantes.buscar("zzz") == [])
    ok, _ = estudiantes.actualizar(2, {"carrera": "redes"})
    verificar("actualiza carrera", ok and estudiantes.obtener(2).carrera == "Redes")
    ok, msg = estudiantes.actualizar(2, {"carnet": "EST2026001"})
    verificar("rechaza actualizar al carnet de otro", not ok)
    ok, _ = estudiantes.actualizar(2, {"carnet": "est2026002"})
    verificar("permite 'actualizar' al mismo carnet propio", ok)
    ok, _ = estudiantes.actualizar(2, {"email": "ana@u.edu"})
    verificar("rechaza actualizar al email de otro", not ok)
    ok, _ = estudiantes.actualizar(2, {"nombre": "  "})
    verificar("rechaza vaciar el nombre al actualizar", not ok)
    verificar("el nombre no cambió tras el error",
              estudiantes.obtener(2).nombre == "Luis")
    ok, msg = estudiantes.actualizar(2, {"color": "rojo"})
    verificar("rechaza campo desconocido", not ok and "color" in msg)
    ok, _ = estudiantes.actualizar(2, {})
    verificar("rechaza actualización sin cambios", not ok)
    ok, _ = estudiantes.actualizar(99, {"nombre": "X"})
    verificar("rechaza id inexistente al actualizar", not ok)
    verificar("carreras sin repetir y ordenadas",
              estudiantes.carreras() == ["Redes", "Software"])
    verificar("obtener id inexistente devuelve None",
              estudiantes.obtener(99) is None)
    verificar("obtener con None devuelve None", estudiantes.obtener(None) is None)

    # ------------------------------------------------------------------
    seccion("MATERIAS · datos válidos y reglas estáticas")
    ok, _ = materias.crear({"nombre": "cálculo i", "codigo": "mat101",
                            "creditos": "4"})
    verificar("crea materia con cupos vacíos", ok)
    m1 = materias.obtener(1)
    verificar("nombre Title Case y código MAYÚSCULAS",
              m1.nombre == "Cálculo I" and m1.codigo == "MAT101")
    verificar("cupos vacíos = CUPOS_MAXIMOS (30)",
              m1.cupos == Materia.CUPOS_MAXIMOS == 30)
    ok, _ = materias.crear({"nombre": "física", "codigo": "FIS201",
                            "creditos": 3, "cupos": 1})
    verificar("crea materia con números reales (int)", ok)
    ok, _ = materias.crear({"nombre": "química", "codigo": "QUI101",
                            "creditos": "2", "cupos": "0"})
    verificar("crea materia con 0 cupos", ok)
    verificar("etiqueta de Química avisa 'sin cupo'",
              "sin cupo" in materias.obtener(3).etiqueta())
    verificar("NOTA_APROBACION es 14", Materia.NOTA_APROBACION == 14)
    verificar("hay_cupo en materia con cupos", materias.obtener(1).hay_cupo())
    verificar("hay_cupo falso con 0 cupos", not materias.obtener(3).hay_cupo())
    verificar("es_nota_valida(0) y (20) son válidas",
              Materia.es_nota_valida(0) and Materia.es_nota_valida(20))
    verificar("es_nota_valida acepta '16.5' como texto",
              Materia.es_nota_valida("16.5"))
    for mala in (-0.1, 20.1, "abc", "", None, [10], "nan", "inf", "-inf"):
        verificar(f"es_nota_valida rechaza {mala!r}",
                  not Materia.es_nota_valida(mala))

    seccion("MATERIAS · datos inválidos")
    ok, msg = materias.crear({"nombre": "Otra", "codigo": "mat101",
                              "creditos": "3"})
    verificar("rechaza código duplicado (case-insensitive)",
              not ok and "ya está registrado" in msg)
    for malo in ("0", "11", "-1", "abc", "", "4.5", "²", "1e1"):
        ok, _ = materias.crear({"nombre": "N", "codigo": "COD1",
                                "creditos": malo})
        verificar(f"rechaza créditos {malo!r}", not ok)
    for bueno in ("1", "10"):
        ok, _ = materias.crear({"nombre": "L" + bueno, "codigo": "LIM" + bueno,
                                "creditos": bueno})
        verificar(f"acepta créditos límite {bueno}", ok)
    for malo in ("31", "-1", "x", "2.5", "²"):
        ok, _ = materias.crear({"nombre": "N", "codigo": "COD2",
                                "creditos": "3", "cupos": malo})
        verificar(f"rechaza cupos {malo!r}", not ok)
    ok, _ = materias.crear({"nombre": "Max", "codigo": "MAX30",
                            "creditos": "3", "cupos": "30"})
    verificar("acepta cupos = CUPOS_MAXIMOS", ok)
    ok, _ = materias.crear({"nombre": "N", "creditos": "3"})
    verificar("rechaza si falta el código", not ok)
    ok, _ = materias.crear({"nombre": "N", "codigo": None, "creditos": "3"})
    verificar("rechaza código None", not ok)
    ok, _ = materias.crear({"nombre": "N", "codigo": "C"})
    verificar("rechaza si faltan los créditos", not ok)
    ok, _ = materias.crear({})
    verificar("rechaza diccionario vacío", not ok)

    seccion("MATERIAS · buscar, actualizar, eliminar")
    verificar("buscar por código (minúsculas)", len(materias.buscar("fis")) == 1)
    verificar("buscar por nombre", len(materias.buscar("cálculo")) == 1)
    verificar("buscar texto vacío devuelve lista vacía", materias.buscar("") == [])
    ok, _ = materias.actualizar(2, {"creditos": "5", "cupos": "10"})
    verificar("actualiza créditos y cupos",
              ok and materias.obtener(2).creditos == 5
              and materias.obtener(2).cupos == 10)
    ok, _ = materias.actualizar(2, {"cupos": "1"})
    ok, _ = materias.actualizar(2, {"creditos": "3"})
    verificar("deja Física como estaba (3 créditos, 1 cupo)", ok)
    ok, _ = materias.actualizar(2, {"cupos": "99"})
    verificar("rechaza actualizar cupos por encima del máximo", not ok)
    ok, _ = materias.actualizar(2, {"codigo": "MAT101"})
    verificar("rechaza actualizar al código de otra", not ok)
    ok, _ = materias.actualizar(2, {"codigo": "fis201"})
    verificar("permite 'actualizar' al mismo código propio", ok)
    verificar("materias_sin_cupo incluye solo Química",
              [m.codigo for m in materias.materias_sin_cupo()] == ["QUI101"])
    ok, _ = materias.eliminar(materias.siguiente() - 1)
    verificar("elimina una materia (la última creada)", ok)
    ok, _ = materias.eliminar(99)
    verificar("eliminar id inexistente falla", not ok)

    # ------------------------------------------------------------------
    seccion("MATRÍCULAS · flujo normal")
    ok, msg = matriculas.crear({"estudiante_id": 1, "materia_id": 1,
                                "periodo": "2026-1"})
    verificar("matricula a Ana en Cálculo (2026-1)", ok)
    verificar("el cupo de Cálculo bajó de 30 a 29", materias.obtener(1).cupos == 29)
    id_m1 = ultimo_id(matriculas)
    ok, _ = matriculas.crear({"estudiante_id": 1, "materia_id": 1,
                              "periodo": "2026-2"})
    verificar("misma materia en OTRO período sí se permite", ok)
    id_m2 = ultimo_id(matriculas)
    ok, _ = matriculas.crear({"estudiante_id": 2, "materia_id": 1,
                              "periodo": "2026-1"})
    verificar("OTRO estudiante en la misma materia y período sí se permite", ok)
    id_m3 = ultimo_id(matriculas)
    ok, _ = matriculas.crear({"estudiante_id": "1", "materia_id": "2",
                              "periodo": " 2026-1 "})
    verificar("acepta ids como texto y período con espacios", ok)
    id_m4 = ultimo_id(matriculas)
    verificar("el período se guarda sin espacios",
              matriculas.obtener(id_m4).periodo == "2026-1")
    verificar("el cupo de Física bajó a 0", materias.obtener(2).cupos == 0)
    ok, _ = matriculas.crear({"estudiante_id": 2, "materia_id": 1,
                              "periodo": "2026-2", "nota": 18})
    verificar("matricula con nota inicial válida", ok)
    id_m5 = ultimo_id(matriculas)
    verificar("la nota inicial se guardó", matriculas.obtener(id_m5).nota == 18.0)
    verificar("el cupo de Cálculo bajó a 26", materias.obtener(1).cupos == 26)

    seccion("MATRÍCULAS · reglas del negocio (datos inválidos)")
    ok, msg = matriculas.crear({"estudiante_id": 1, "materia_id": 1,
                                "periodo": "2026-1"})
    verificar("rechaza matricular DOS VECES (estudiante+materia+período)",
              not ok and "ya está matriculado" in msg)
    ok, msg = matriculas.crear({"estudiante_id": 2, "materia_id": 2,
                                "periodo": "2026-1"})
    verificar("rechaza materia sin cupo (Física 0)", not ok and "cupos" in msg)
    ok, _ = matriculas.crear({"estudiante_id": 1, "materia_id": 3,
                              "periodo": "2026-1"})
    verificar("rechaza materia con 0 cupos desde el inicio (Química)", not ok)
    ok, _ = matriculas.crear({"estudiante_id": 99, "materia_id": 1,
                              "periodo": "2026-1"})
    verificar("rechaza estudiante inexistente", not ok)
    ok, _ = matriculas.crear({"estudiante_id": 1, "materia_id": 99,
                              "periodo": "2026-1"})
    verificar("rechaza materia inexistente", not ok)
    for malo in ("", "   ", None):
        ok, _ = matriculas.crear({"estudiante_id": 2, "materia_id": 1,
                                  "periodo": malo})
        verificar(f"rechaza período {malo!r}", not ok)
    ok, _ = matriculas.crear({"estudiante_id": "a", "materia_id": 1,
                              "periodo": "2026-3"})
    verificar("rechaza estudiante_id no numérico", not ok)
    ok, _ = matriculas.crear({"estudiante_id": None, "materia_id": 1,
                              "periodo": "2026-3"})
    verificar("rechaza estudiante_id None", not ok)
    ok, _ = matriculas.crear({"estudiante_id": 1, "materia_id": "1.5",
                              "periodo": "2026-3"})
    verificar("rechaza materia_id decimal", not ok)
    ok, _ = matriculas.crear({})
    verificar("rechaza diccionario vacío", not ok)
    for mala in (21, -1, "abc"):
        ok, _ = matriculas.crear({"estudiante_id": 1, "materia_id": 1,
                                  "periodo": "2026-3", "nota": mala})
        verificar(f"rechaza nota inicial {mala!r}", not ok)
    verificar("el cupo de Cálculo no cambió tras los rechazos",
              materias.obtener(1).cupos == 26)
    verificar("no se crearon matrículas de más", len(matriculas.leer()) == 5)
    ok, _ = matriculas.actualizar(id_m1, {"periodo": "2027-1"})
    verificar("las matrículas no se pueden actualizar", not ok)

    seccion("MATRÍCULAS · registrar notas y estado")
    verificar("sin nota, el estado es 'Sin nota'",
              matriculas.obtener(id_m4).estado() == "Sin nota"
              and not matriculas.obtener(id_m4).esta_aprobada())
    ok, msg = matriculas.registrar_nota(id_m1, "16.5")
    verificar("registra 16.5 (como texto) y aprueba",
              ok and matriculas.obtener(id_m1).estado() == "Aprobado")
    ok, _ = matriculas.registrar_nota(id_m2, 12)
    verificar("registra 12 y reprueba",
              ok and matriculas.obtener(id_m2).estado() == "Reprobado")
    ok, _ = matriculas.registrar_nota(id_m3, 14)
    verificar("14 justo en el límite: aprobado",
              ok and matriculas.obtener(id_m3).esta_aprobada())
    ok, _ = matriculas.registrar_nota(id_m3, 13.99)
    verificar("13.99: reprobado", ok and not matriculas.obtener(id_m3).esta_aprobada())
    ok, _ = matriculas.registrar_nota(id_m3, 14)
    ok, _ = matriculas.registrar_nota(id_m4, 0)
    verificar("acepta nota 0 (y 0 NO es 'sin nota')",
              ok and matriculas.obtener(id_m4).nota == 0.0
              and matriculas.obtener(id_m4).estado() == "Reprobado")
    ok, _ = matriculas.registrar_nota(id_m4, 20)
    verificar("acepta nota 20", ok)
    for mala in (20.1, -1, "abc", "", None, "nan", "inf"):
        ok, _ = matriculas.registrar_nota(id_m4, mala)
        verificar(f"rechaza nota {mala!r}", not ok)
    verificar("la nota no cambió tras los rechazos",
              matriculas.obtener(id_m4).nota == 20.0)
    ok, _ = matriculas.registrar_nota(99, 15)
    verificar("registrar nota en matrícula inexistente falla", not ok)
    matriculas.registrar_nota(id_m4, 0)

    seccion("MATRÍCULAS · certificado, promedio y agrupación")
    cert = matriculas.certificado(id_m1)
    verificar("certificado: encabezado con id y período",
              "CERTIFICADO #1   periodo: 2026-1" in cert)
    verificar("certificado: estudiante y carnet",
              "Estudiante: Ana Pérez   (EST2026001)" in cert)
    verificar("certificado: materia, código y créditos",
              "Materia   : Cálculo I   (MAT101) · 4 créditos" in cert)
    verificar("certificado: nota y estado",
              "Nota      : 16.5" in cert and "Estado    : Aprobado" in cert)
    cert_sin = matriculas.certificado(id_m4)
    verificar("certificado de nota 0 muestra 0, no 'sin nota'",
              "Nota      : 0\n" in cert_sin)
    verificar("certificado de matrícula inexistente es None",
              matriculas.certificado(99) is None)
    # Notas: Ana = 16.5, 12, 0 -> 9.5 ; Luis = 14, 18 -> 16.0
    verificar("promedio de Ana = 9.5",
              matriculas.promedio_de_estudiante(1) == 9.5)
    verificar("promedio de Luis = 16.0",
              matriculas.promedio_de_estudiante(2) == 16.0)
    verificar("promedio de estudiante inexistente es None",
              matriculas.promedio_de_estudiante(99) is None)
    agrupadas = matriculas.matriculas_por_estudiante()
    verificar("matriculas_por_estudiante: dict de listas",
              set(agrupadas) == {1, 2}
              and len(agrupadas[1]) == 3 and len(agrupadas[2]) == 2)
    verificar("buscar matrículas por período", len(matriculas.buscar("2026-1")) == 3)
    verificar("buscar matrículas con texto vacío", matriculas.buscar("") == [])
    verificar("total_aprobadas = 3 (16.5, 14 y 18)", matriculas.total_aprobadas() == 3)

    seccion("MATRÍCULAS · retirar")
    cupos_antes = materias.obtener(1).cupos
    ok, _ = matriculas.eliminar(id_m2)
    verificar("retira la matrícula de 12", ok)
    verificar("el cupo de Cálculo volvió (+1)",
              materias.obtener(1).cupos == cupos_antes + 1)
    ok, _ = matriculas.eliminar(id_m2)
    verificar("retirar dos veces la misma falla", not ok)
    ok, _ = matriculas.eliminar(99)
    verificar("retirar matrícula inexistente falla", not ok)
    ok, _ = matriculas.crear({"estudiante_id": 1, "materia_id": 1,
                              "periodo": "2026-2"})
    verificar("tras retirar, se puede volver a matricular", ok)
    verificar("el id nuevo no reutiliza ids vivos",
              ultimo_id(matriculas) == id_m5 + 1)
    verificar("Ana ya no tiene el 12: promedio 8.25",
              matriculas.promedio_de_estudiante(1) == 8.25)

    # ------------------------------------------------------------------
    seccion("PERSISTENCIA · reiniciar el programa")
    est2 = EstudianteController(ruta("estudiantes.json"))
    mat2 = MateriaController(ruta("materias.json"))
    mtr2 = MatriculaController(est2, mat2, ruta("matriculas.json"))
    verificar("estudiantes se recuperan del JSON",
              len(est2.leer()) == len(estudiantes.leer()))
    verificar("materias se recuperan del JSON",
              len(mat2.leer()) == len(materias.leer()))
    verificar("matrículas se recuperan del JSON",
              len(mtr2.leer()) == len(matriculas.leer()))
    verificar("los cupos persistidos coinciden",
              mat2.obtener(1).cupos == materias.obtener(1).cupos)
    verificar("las notas persistidas coinciden (incluida la nota 0)",
              mtr2.obtener(id_m4).nota == 0.0
              and mtr2.obtener(id_m1).nota == 16.5)
    verificar("una matrícula sin nota vuelve como None",
              mtr2.obtener(ultimo_id(mtr2)).nota is None)
    verificar("los objetos recuperados son de la clase correcta",
              isinstance(est2.obtener(1), Estudiante)
              and isinstance(mat2.obtener(1), Materia)
              and isinstance(mtr2.obtener(id_m1), Matricula))
    verificar("el estado NO está guardado en el JSON",
              "estado" not in matriculas.obtener(id_m1).a_diccionario())

    seccion("PERSISTENCIA · archivos dañados o vacíos")
    ruta_mala = ruta("malo.json")
    with open(ruta_mala, "w", encoding="utf-8") as f:
        f.write("{esto no es json")
    verificar("JSON corrupto -> lista vacía, sin romper",
              EstudianteController(ruta_mala).leer() == [])
    with open(ruta_mala, "w", encoding="utf-8") as f:
        f.write('{"no": "es lista"}')
    verificar("JSON que no es lista -> lista vacía",
              MateriaController(ruta_mala).leer() == [])
    with open(ruta_mala, "w", encoding="utf-8") as f:
        f.write("")
    verificar("archivo vacío -> lista vacía",
              MatriculaController(est2, mat2, ruta_mala).leer() == [])

    seccion("CARACTERES ESPECIALES")
    ok, _ = estudiantes.crear({"nombre": "José María", "apellido": "Peña Ñúñez",
                               "email": "jose@u.edu", "carnet": "EST2026003",
                               "carrera": "Ingeniería En Software"})
    verificar("acepta tildes y ñ", ok)
    id_jose = ultimo_id(estudiantes)
    est3 = EstudianteController(ruta("estudiantes.json"))
    verificar("tildes y ñ sobreviven al guardar y leer",
              est3.obtener(id_jose).apellido == "Peña Ñúñez")
    ok, _ = estudiantes.crear({"nombre": "Robert'); DROP", "apellido": "Tables",
                               "email": "bob@u.edu", "carnet": "EST'--"})
    verificar("texto raro se guarda como texto, sin efectos", ok)
    ok, _ = estudiantes.crear({"nombre": "Ana" * 200, "apellido": "Larga",
                               "email": "larga@u.edu", "carnet": "EST-LARGO"})
    verificar("acepta un nombre muy largo", ok)

    seccion("ELIMINAR con matrículas existentes")
    ok, _ = matriculas.crear({"estudiante_id": id_jose, "materia_id": 1,
                              "periodo": "2026-3"})
    id_mj = ultimo_id(matriculas)
    ok_del, _ = estudiantes.eliminar(id_jose)
    verificar("se puede eliminar el estudiante", ok and ok_del)
    verificar("el certificado dice 'eliminado' en vez de romperse",
              "Estudiante: eliminado" in matriculas.certificado(id_mj))
    ok, _ = materias.eliminar(1)
    verificar("se puede eliminar la materia", ok)
    verificar("el certificado dice 'eliminada' en vez de romperse",
              "Materia   : eliminada" in matriculas.certificado(id_mj))
    ok, _ = matriculas.eliminar(id_mj)
    verificar("retirar una matrícula de materia eliminada no rompe", ok)

    # ------------------------------------------------------------------
    seccion("HERENCIA, POLIMORFISMO Y ESTÁTICOS")
    verificar("Estudiante ES UNA Persona", issubclass(Estudiante, Persona))
    verificar("Persona ES UN ModeloBase", issubclass(Persona, ModeloBase))
    verificar("Materia y Matricula son ModeloBase",
              issubclass(Materia, ModeloBase) and issubclass(Matricula, ModeloBase))
    verificar("nombre_completo() se hereda de Persona",
              "nombre_completo" not in vars(Estudiante)
              and estudiantes.obtener(1).nombre_completo() == "Ana Pérez")
    verificar("NINGÚN modelo reescribe desde_diccionario()",
              all("desde_diccionario" not in vars(c)
                  for c in (Persona, Estudiante, Materia, Matricula)))
    verificar("desde_diccionario es el único @classmethod (en ModeloBase)",
              isinstance(vars(ModeloBase)["desde_diccionario"], classmethod))
    verificar("print(objeto) usa etiqueta() en los tres modelos",
              all(str(o).startswith(f"[{o.id}] ") for o in
                  (estudiantes.obtener(1), mat2.obtener(1), matriculas.obtener(id_m1))))
    verificar("las tres etiquetas son distintas entre sí",
              len({estudiantes.obtener(1).etiqueta(), mat2.obtener(1).etiqueta(),
                   matriculas.obtener(id_m1).etiqueta()}) == 3)
    try:
        CrudBase()
        verificar("CrudBase no se puede instanciar", False)
    except TypeError:
        verificar("CrudBase no se puede instanciar", True)
    d = {"id": 7, "nombre": "A", "apellido": "B", "email": "a@b.com",
         "carnet": "E1", "carrera": "C"}
    verificar("desde_diccionario no modifica el dict original",
              Estudiante.desde_diccionario(d).id == 7 and "id" in d)
    verificar("Estudiante: a_diccionario -> desde_diccionario es reversible",
              Estudiante.desde_diccionario(d).a_diccionario() == d)
    dm = {"id": 3, "nombre": "M", "codigo": "C1", "creditos": 4, "cupos": 9}
    verificar("Materia: ida y vuelta",
              Materia.desde_diccionario(dm).a_diccionario() == dm)
    dx = {"id": 5, "estudiante_id": 1, "materia_id": 2, "periodo": "2026-1",
          "nota": None, "fecha": "2026-10-14"}
    verificar("Matricula sin nota: ida y vuelta",
              Matricula.desde_diccionario(dx).a_diccionario() == dx)

finally:
    shutil.rmtree(carpeta, ignore_errors=True)

print(f"\n{'=' * 50}")
print(f"Pruebas: {total}   Correctas: {total - fallos}   Fallidas: {fallos}")
raise SystemExit(1 if fallos else 0)
