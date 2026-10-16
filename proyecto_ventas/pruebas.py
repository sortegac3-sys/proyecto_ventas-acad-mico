"""Pruebas automáticas del sistema de ventas con distintos tipos de datos.

Usa una carpeta temporal para NO tocar los archivos reales de data/.
Ejecutar:  python pruebas.py
"""
import os
import shutil
import tempfile

from models import Cliente, Producto, Venta, ModeloBase
from views import (ClienteController, ProductoController, VentaController,
                   CrudBase)

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


carpeta = tempfile.mkdtemp()
try:
    clientes = ClienteController(os.path.join(carpeta, "clientes.json"))
    productos = ProductoController(os.path.join(carpeta, "productos.json"))
    ventas = VentaController(clientes, productos,
                             os.path.join(carpeta, "ventas.json"))

    # ------------------------------------------------------------------
    seccion("CLIENTES · datos válidos y normalización")
    ok, msg = clientes.crear({"nombre": "ana", "apellido": "pérez",
                              "email": "ANA@X.com", "telefono": "0987654321",
                              "ciudad": "guayaquil"})
    verificar("crea cliente válido", ok)
    c1 = clientes.obtener(1)
    verificar("nombre pasa a Title Case", c1.nombre == "Ana")
    verificar("email pasa a minúsculas", c1.email == "ana@x.com")
    verificar("ciudad pasa a Title Case", c1.ciudad == "Guayaquil")

    ok, _ = clientes.crear({"nombre": "Luis", "apellido": "Mora",
                            "email": "luis@x.com"})
    verificar("crea cliente sin teléfono ni ciudad", ok)
    verificar("etiqueta usa 'sin ciudad'",
              "sin ciudad" in clientes.obtener(2).etiqueta())

    seccion("CLIENTES · datos inválidos")
    ok, msg = clientes.crear({"nombre": "Ana", "apellido": "Pérez",
                              "email": "ana@x.com"})
    verificar("rechaza email duplicado", not ok and "ya está registrado" in msg)
    ok, msg = clientes.crear({"nombre": "Ana", "apellido": "Pérez",
                              "email": "ANA@X.COM"})
    verificar("rechaza email duplicado con otra capitalización", not ok)
    ok, msg = clientes.crear({"nombre": "Zoe", "apellido": "Ruiz",
                              "email": "zoe@x.com", "telefono": "09AB"})
    verificar("rechaza teléfono con letras", not ok and "números" in msg)
    for malo in ("sinarroba", "a@b", "@x.com", "a@@x.com", "a@x.", ""):
        ok, _ = clientes.crear({"nombre": "T", "apellido": "T", "email": malo})
        verificar(f"rechaza email inválido {malo!r}", not ok)
    ok, msg = clientes.crear({"nombre": "   ", "apellido": "X",
                              "email": "x@x.com"})
    verificar("rechaza nombre solo con espacios", not ok and "obligatorio" in msg)
    ok, _ = clientes.crear({})
    verificar("rechaza diccionario vacío", not ok)
    verificar("no se crearon clientes de más", len(clientes.leer()) == 2)

    seccion("CLIENTES · buscar, actualizar, eliminar")
    verificar("buscar por nombre", len(clientes.buscar("ana")) == 1)
    verificar("buscar por ciudad", len(clientes.buscar("guayaquil")) == 1)
    verificar("buscar por email parcial", len(clientes.buscar("x.com")) == 2)
    verificar("buscar texto vacío devuelve lista vacía",
              clientes.buscar("") == [])
    verificar("buscar sin coincidencias", clientes.buscar("zzz") == [])
    ok, _ = clientes.actualizar(2, {"ciudad": "quito"})
    verificar("actualiza ciudad", ok and clientes.obtener(2).ciudad == "Quito")
    ok, msg = clientes.actualizar(2, {"email": "ana@x.com"})
    verificar("rechaza actualizar a email de otro", not ok)
    ok, _ = clientes.actualizar(2, {"email": "luis@x.com"})
    verificar("permite 'actualizar' al mismo email propio", ok)
    ok, msg = clientes.actualizar(2, {"color": "rojo"})
    verificar("rechaza campo desconocido", not ok and "color" in msg)
    ok, _ = clientes.actualizar(2, {})
    verificar("rechaza actualización sin cambios", not ok)
    ok, _ = clientes.actualizar(99, {"nombre": "X"})
    verificar("rechaza id inexistente al actualizar", not ok)
    verificar("ciudades sin repetir y ordenadas",
              clientes.ciudades() == ["Guayaquil", "Quito"])
    verificar("obtener id inexistente devuelve None",
              clientes.obtener(99) is None)
    verificar("obtener con None devuelve None", clientes.obtener(None) is None)

    # ------------------------------------------------------------------
    seccion("PRODUCTOS · datos válidos y reglas estáticas")
    ok, _ = productos.crear({"nombre": "teclado", "precio": "25.5",
                             "stock": "6"})
    verificar("crea producto con precio decimal como texto", ok)
    ok, _ = productos.crear({"nombre": "mouse", "precio": 12, "stock": 3})
    verificar("crea producto con números reales (int)", ok)
    ok, _ = productos.crear({"nombre": "Monitor", "precio": "150"})
    verificar("stock vacío empieza en 0",
              ok and productos.obtener(3).stock == 0)
    verificar("mouse sale con stock bajo", productos.obtener(2).stock_bajo())
    verificar("teclado (6) no tiene stock bajo",
              not productos.obtener(1).stock_bajo())
    verificar("etiqueta de mouse muestra alerta",
              "⚠" in productos.obtener(2).etiqueta())
    verificar("Producto.con_iva(51) == 58.65", Producto.con_iva(51) == 58.65)
    verificar("contador estático total_creados > 0",
              Producto.total_creados >= 3)

    seccion("PRODUCTOS · datos inválidos")
    for malo in ("abc", "0", "-5", "", "1,5", None):
        ok, _ = productos.crear({"nombre": "X" + str(malo), "precio": malo})
        verificar(f"rechaza precio {malo!r}", not ok)
    ok, msg = productos.crear({"nombre": "TECLADO", "precio": 10})
    verificar("rechaza nombre duplicado (case-insensitive)",
              not ok and "Ya existe" in msg)
    ok, _ = productos.crear({"nombre": "Cable", "precio": 5, "stock": "abc"})
    verificar("rechaza stock con letras", not ok)
    ok, _ = productos.crear({"nombre": "Cable", "precio": 5, "stock": "-2"})
    verificar("rechaza stock negativo", not ok)
    ok, _ = productos.crear({"nombre": "Cable", "precio": 5, "stock": "2.5"})
    verificar("rechaza stock decimal", not ok)
    verificar("es_precio_valido acepta 0.01", Producto.es_precio_valido("0.01"))
    verificar("es_precio_valido rechaza None",
              not Producto.es_precio_valido(None))
    verificar("es_precio_valido rechaza lista",
              not Producto.es_precio_valido([1]))

    seccion("PRODUCTOS · buscar, actualizar, eliminar")
    verificar("buscar 'tec' encuentra teclado", len(productos.buscar("tec")) == 1)
    ok, _ = productos.actualizar(1, {"precio": "30", "stock": "10"})
    verificar("actualiza precio y stock",
              ok and productos.obtener(1).precio == 30.0
              and productos.obtener(1).stock == 10)
    ok, _ = productos.actualizar(1, {"precio": "30", "stock": "10"})
    ok, _ = productos.actualizar(1, {"precio": "25.5", "stock": "6"})
    verificar("vuelve a precio y stock originales", ok)
    ok, _ = productos.actualizar(1, {"precio": "abc"})
    verificar("rechaza actualizar con precio inválido", not ok)
    verificar("el precio no cambió tras el error",
              productos.obtener(1).precio == 25.5)
    verificar("con_stock_bajo incluye mouse y monitor",
              {p.nombre for p in productos.con_stock_bajo()}
              == {"Mouse", "Monitor"})

    # ------------------------------------------------------------------
    seccion("VENTAS · flujo normal")
    ok, msg = ventas.crear({"cliente_id": 1, "producto_id": 1, "cantidad": 2})
    verificar("registra venta de 2 teclados", ok and "51.00" in msg)
    verificar("el stock del teclado bajó de 6 a 4",
              productos.obtener(1).stock == 4)
    ok, _ = ventas.crear({"cliente_id": "1", "producto_id": "2",
                          "cantidad": "1"})
    verificar("acepta ids y cantidad como texto numérico", ok)
    verificar("total vendido = 51 + 12 = 63", ventas.total_vendido() == 63.0)
    comp = ventas.comprobante(1)
    verificar("comprobante tiene SUBTOTAL 51.00", "SUBTOTAL: $51.00" in comp)
    verificar("comprobante tiene TOTAL con IVA 58.65",
              "TOTAL con IVA: $58.65" in comp)
    verificar("comprobante de venta inexistente es None",
              ventas.comprobante(99) is None)
    agrupadas = ventas.ventas_por_cliente()
    verificar("ventas_por_cliente agrupa en dict de listas",
              list(agrupadas.keys()) == [1] and len(agrupadas[1]) == 2)
    verificar("buscar venta por año", len(ventas.buscar("20")) == 2)

    seccion("VENTAS · datos inválidos")
    ok, msg = ventas.crear({"cliente_id": 1, "producto_id": 2, "cantidad": 99})
    verificar("rechaza stock insuficiente", not ok and "insuficiente" in msg)
    ok, _ = ventas.crear({"cliente_id": 1, "producto_id": 1, "cantidad": 0})
    verificar("rechaza cantidad 0", not ok)
    ok, _ = ventas.crear({"cliente_id": 1, "producto_id": 1, "cantidad": -3})
    verificar("rechaza cantidad negativa", not ok)
    ok, _ = ventas.crear({"cliente_id": 99, "producto_id": 1, "cantidad": 1})
    verificar("rechaza cliente inexistente", not ok)
    ok, _ = ventas.crear({"cliente_id": 1, "producto_id": 99, "cantidad": 1})
    verificar("rechaza producto inexistente", not ok)
    ok, _ = ventas.crear({"cliente_id": "a", "producto_id": 1, "cantidad": 1})
    verificar("rechaza cliente_id no numérico", not ok)
    ok, _ = ventas.crear({"cliente_id": 1, "producto_id": 1,
                          "cantidad": "1.5"})
    verificar("rechaza cantidad decimal", not ok)
    ok, _ = ventas.crear({"cliente_id": None, "producto_id": 1,
                          "cantidad": 1})
    verificar("rechaza cliente_id None", not ok)
    ok, _ = ventas.crear({})
    verificar("rechaza diccionario vacío", not ok)
    ok, _ = ventas.crear({"cliente_id": 1, "producto_id": 3, "cantidad": 1})
    verificar("rechaza vender producto con stock 0", not ok)
    ok, _ = ventas.actualizar(1, {"cantidad": 5})
    verificar("las ventas no se pueden actualizar", not ok)
    verificar("el stock no cambió tras los rechazos",
              productos.obtener(1).stock == 4
              and productos.obtener(2).stock == 2)

    seccion("VENTAS · precio histórico y anulación")
    productos.actualizar(1, {"precio": "30"})
    verificar("la venta 1 conserva el precio histórico 25.5",
              ventas.obtener(1).precio_unitario == 25.5)
    productos.actualizar(1, {"precio": "25.5"})
    ok, msg = ventas.eliminar(1)
    verificar("anula la venta 1", ok)
    verificar("el stock del teclado volvió a 6",
              productos.obtener(1).stock == 6)
    ok, _ = ventas.eliminar(1)
    verificar("anular dos veces la misma venta falla", not ok)
    ok, _ = ventas.eliminar(99)
    verificar("anular venta inexistente falla", not ok)
    ventas.crear({"cliente_id": 1, "producto_id": 1, "cantidad": 1})
    verificar("el id nuevo de venta no reutiliza ids vivos",
              ventas.siguiente() == 4)

    # ------------------------------------------------------------------
    seccion("PERSISTENCIA · reiniciar el programa")
    clientes2 = ClienteController(os.path.join(carpeta, "clientes.json"))
    productos2 = ProductoController(os.path.join(carpeta, "productos.json"))
    ventas2 = VentaController(clientes2, productos2,
                              os.path.join(carpeta, "ventas.json"))
    verificar("clientes se recuperan del JSON", len(clientes2.leer()) == 2)
    verificar("productos se recuperan del JSON", len(productos2.leer()) == 3)
    verificar("ventas se recuperan del JSON",
              len(ventas2.leer()) == len(ventas.leer()))
    verificar("el stock persistido coincide",
              productos2.obtener(1).stock == productos.obtener(1).stock)
    verificar("el objeto recuperado es de la clase correcta",
              isinstance(clientes2.obtener(1), Cliente)
              and isinstance(productos2.obtener(1), Producto)
              and isinstance(ventas2.obtener(2), Venta))

    seccion("PERSISTENCIA · archivos dañados o vacíos")
    ruta_mala = os.path.join(carpeta, "malo.json")
    with open(ruta_mala, "w", encoding="utf-8") as f:
        f.write("{esto no es json")
    verificar("JSON corrupto -> lista vacía, sin romper",
              ClienteController(ruta_mala).leer() == [])
    with open(ruta_mala, "w", encoding="utf-8") as f:
        f.write('{"no": "es lista"}')
    verificar("JSON que no es lista -> lista vacía",
              ClienteController(ruta_mala).leer() == [])
    with open(ruta_mala, "w", encoding="utf-8") as f:
        f.write("")
    verificar("archivo vacío -> lista vacía",
              ProductoController(ruta_mala).leer() == [])

    seccion("CARACTERES ESPECIALES")
    ok, _ = clientes.crear({"nombre": "José María", "apellido": "Peña Ñúñez",
                            "email": "jose@x.com", "ciudad": "Cuenca"})
    verificar("acepta tildes y ñ", ok)
    clientes3 = ClienteController(os.path.join(carpeta, "clientes.json"))
    verificar("tildes y ñ sobreviven al guardar y leer",
              clientes3.obtener(3).apellido == "Peña Ñúñez")
    ok, _ = clientes.crear({"nombre": "Robert'); DROP", "apellido": "Tables",
                            "email": "bob@x.com"})
    verificar("texto raro se guarda como texto, sin efectos", ok)
    ok, _ = clientes.crear({"nombre": "Ana" * 200, "apellido": "Larga",
                            "email": "larga@x.com"})
    verificar("acepta un nombre muy largo", ok)

    # ------------------------------------------------------------------
    seccion("HERENCIA Y POLIMORFISMO")
    verificar("Cliente es ModeloBase", issubclass(Cliente, ModeloBase))
    verificar("Producto es ModeloBase", issubclass(Producto, ModeloBase))
    verificar("print(objeto) usa etiqueta() en los tres modelos",
              all(str(o).startswith(f"[{o.id}] ") for o in
                  (clientes.obtener(1), productos.obtener(1), ventas.obtener(2))))
    try:
        CrudBase()
        verificar("CrudBase no se puede instanciar", False)
    except TypeError:
        verificar("CrudBase no se puede instanciar", True)
    d = {"id": 7, "nombre": "A", "apellido": "B", "email": "a@b.com",
         "telefono": "1", "ciudad": "C"}
    verificar("desde_diccionario no modifica el dict original",
              Cliente.desde_diccionario(d).id == 7 and "id" in d)
    verificar("a_diccionario -> desde_diccionario es reversible",
              Cliente.desde_diccionario(d).a_diccionario() == d)

finally:
    shutil.rmtree(carpeta, ignore_errors=True)

print(f"\n{'=' * 50}")
print(f"Pruebas: {total}   Correctas: {total - fallos}   Fallidas: {fallos}")
raise SystemExit(1 if fallos else 0)
