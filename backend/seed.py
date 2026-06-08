"""
Seed inicial para Corporacion Novum – Sistema de Requerimientos de Materiales.
Ejecutar desde la carpeta backend/: python seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
import models
from auth import hash_password

# Recrear todas las tablas (maneja cambios de esquema)
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    print("Tablas recreadas. Insertando datos base...")

    # ─── Lineas de produccion ─────────────────────────────────────────────────
    lineas_nombres = [
        "Fabricación de cilindro de 15 kg",
        "Reparación de cilindro de 15 kg",
        "Fabricación de asas para cilindro de 15 kg",
        "Fabricación de bases para cilindro de 15 kg",
        "Reparación de válvulas de cilindro de 15 kg",
    ]
    lineas = []
    for nombre in lineas_nombres:
        l = models.LineaProduccion(nombre=nombre, activo=True)
        db.add(l)
        lineas.append(l)
    db.flush()
    print(f"  OK {len(lineas)} lineas de produccion")

    # ─── Materiales ──────────────────────────────────────────────────────────
    # (codigo, nombre, categoria, unidad_medida, precio_unitario, stock_actual, stock_minimo)
    # Precio en 1.00 como placeholder — actualizar desde la interfaz

    materiales_data = [
        # ── PRODUCCION: Serie MAPD ────────────────────────────────────────────
        ("M-MAPD-014", "FLEJE L-C DE 120 X 2 PARA ASAS",         "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPD-015", "FLEJE L-C DE 70 X 2 PARA BASES",          "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPD-019", "PINTURA AMARILLA DURAGAS",                 "produccion", "litro",  1.00, 0.0, 0.0),
        ("M-MAPD-025", "PINTURA EN POLVO AZUL",                    "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPD-026", "PINTURA EN POLVO AMARILLA DURAGAS",        "produccion", "kg",     1.00, 0.0, 0.0),
        # ── PRODUCCION: Serie MAPI ────────────────────────────────────────────
        ("M-MAPI-001", "ALAMBRE DE SUELDA 0,9 MM",                 "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPI-002", "ALAMBRE DE SUELDA 1.2 MM",                 "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPI-003", "ALAMBRE DE SUELDA SAW 1/8",                "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPI-004", "BOQUILLA DE CONTACTO 0,9 MM",              "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-005", "BOQUILLA DE CONTACTO 1.2 MM",              "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-006", "CO2",                                       "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPI-007", "DIFUSOR",                                   "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-008", "DISOLVENTE (X GALON / ENVASE 50 GALON)",   "produccion", "litro",  1.00, 0.0, 0.0),
        ("M-MAPI-009", "FUNDENTE",                                  "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPI-011", "GRANALLA",                                  "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPI-016", "TOBERA",                                    "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-020", "ELECTRODO EXTENDIDO PLASMA",               "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-021", "CERAMICA AISLANTE PARA EL PLASMA",         "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-022", "DEFLECTOR PARA EL PLASMA",                 "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-023", "BOQUILLA PARA ELECTRODO EXTENDIDO PLASMA", "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-039", "INDURMIG",                                  "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPI-044", "MANTECA",                                   "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPI-045", "ANILLO DIFUSOR",                            "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-050", 'DISCO DE LIJA DE 4"',                       "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-051", 'DISCO DE CORTE DE 4"',                      "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-052", 'DISCO DE DESBASTE DE 4"',                   "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-054", "RETARDANTE",                                "produccion", "litro",  1.00, 0.0, 0.0),
        ("M-MAPI-057", "PINTURA AZUL DURAGAS",                      "produccion", "litro",  1.00, 0.0, 0.0),
        ("M-MAPI-061", "CEPILLO DE BRONCE 1/4",                    "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-063", "VASTAGO CUELLO CORTO",                      "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-064", "TEFLON",                                    "produccion", "unidad", 1.00, 0.0, 0.0),
        ('M-MAPI-066', 'DISCO DE DESBASTE DE 7"',                   "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-067", "PLASTICO DE EMBALAJE",                      "produccion", "kg",     1.00, 0.0, 0.0),
        ("M-MAPI-068", "SILICON TRANSPARENTE",                      "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-069", "ACEITE EN SPRAY WD-40",                    "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-074", "ESPONJA",                                   "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-075", "RESORTE",                                   "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-076", "GUIA PLASTICA",                             "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-077", "RETENEDOR M14",                             "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-083", "PUNTA DE CONTACTO 1/8 (ARCO SUMERIGIDO)",  "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-084", "DISOLVENTE LACA",                           "produccion", "litro",  1.00, 0.0, 0.0),
        ("M-MAPI-085", "GRATA",                                     "produccion", "unidad", 1.00, 0.0, 0.0),
        ("M-MAPI-093", "PINTURA BLANCA AUTOMOTRIZ (+ CATALIZADOR)", "produccion", "litro",  1.00, 0.0, 0.0),
        ("M-MAPI-094", "DISOLVENTE DE POLIURETANO",                 "produccion", "litro",  1.00, 0.0, 0.0),
        ("M-MAPI-095", "BANDAS DE LIJA",                            "produccion", "unidad", 1.00, 0.0, 0.0),
        # ── EPPS: Serie A-SEGU ────────────────────────────────────────────────
        ("A-SEGU-002", "GUANTE NITRILO G40 TALLA 8",               "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-003", "GUANTE LATEX G40 TALLA 8",                 "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-004", "GUANTE HYCRON TALLA 8 (MASTER NITRILO)",   "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-005", "GUANTE SOL-VEX TALLA 9",                   "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-006", "GUANTE CUERO NARANJA TIPO API",             "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-007", "PECHERA PARA SOLDAR",                       "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-008", "CARETAS DE ESMERIL",                        "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-009", "PANTALLA PARA ESMERIL",                     "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-010", "MANGAS DE CUERO",                           "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-011", "POLINAS DE CUERO",                          "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-012", "TAPONES AUDITIVOS",                         "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-015", "GAFAS TRANSPARENTES",                       "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-016", "GAFAS OSCURAS",                             "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-017", "MONOGAFA ANTIEMPANANTE",                    "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-019", "MALETIN NEGRO PORTA EPP",                   "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-022", "GUANTES CAUCHO NITRILO G-40",               "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-025", "CARETA DE SUELDA",                          "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-026", "VIDRIO OBSCURO",                            "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-027", "VIDRIO TRANSPARENTE",                       "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-028", "GUANTE NITRILO G40 TALLA 9",               "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-029", "GUANTE LATEX G40 TALLA 9",                 "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-030", "GUANTE HYCRON TALLA 9 (MASTER NITRILO)",   "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-031", "GUANTE SOL-VEX TALLA 8",                   "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-034", "MONJAS",                                    "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-035", "MASCARILLA N95B PARA SOLDADURA",            "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-040", "FILTRO QUIMICO VO/GA",                      "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-042", "DISCO FILTRANTE P100",                      "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-043", "TRAJE KALEENGUARD",                         "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-044", "MASCARILLA MEDIA CARA",                     "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-045", "PREFILTRO N95 PARA PARTICULAS",             "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-046", "PROTECTOR RETENEDOR FILTRO",                "epps", "unidad", 1.00, 0.0, 0.0),
        ("A-SEGU-051", "GUANTE DE CUERO GAMUSADO",                  "epps", "unidad", 1.00, 0.0, 0.0),
        # ── MANTENIMIENTO: Serie R-MATL ───────────────────────────────────────
        ("R-MATL-001", "SUELDA 6011",                               "mantenimiento", "kg",    1.00, 0.0, 0.0),
        ("R-MATL-031", "SUELDA 7018",                               "mantenimiento", "kg",    1.00, 0.0, 0.0),
        ("R-MATL-047", "CEMENTO DE CONTACTO DE 1/4",               "mantenimiento", "litro", 1.00, 0.0, 0.0),
    ]

    materiales = []
    for cod, nom, cat, unidad, precio, stock, minimo in materiales_data:
        m = models.Material(
            codigo=cod,
            nombre=nom,
            categoria=cat,
            unidad_medida=unidad,
            precio_unitario=precio,
            stock_actual=stock,
            stock_minimo=minimo,
        )
        db.add(m)
        materiales.append(m)
    db.flush()
    print(f"  OK {len(materiales)} materiales cargados (produccion: 45, epps: 32, mantenimiento: 3)")
    print("  NOTA: Precios en $1.00 como placeholder. Actualizar desde la interfaz de Materiales.")

    # ─── Usuarios ────────────────────────────────────────────────────────────
    usuarios_data = [
        ("Ana Martinez",   "solicitante@novum.com",  "solicitante"),
        ("Carlos Lopez",   "coordinador@novum.com",  "coordinador"),
        ("Pedro Gomez",    "bodeguero@novum.com",     "bodeguero"),
    ]
    usuarios = []
    for nombre, email, rol in usuarios_data:
        u = models.Usuario(nombre=nombre, email=email, rol=rol, password_hash=hash_password("password123"))
        db.add(u)
        usuarios.append(u)
    db.flush()
    print(f"  OK {len(usuarios)} usuarios creados")

    db.commit()

    print("\n" + "="*55)
    print("  Base de datos lista para pruebas")
    print("="*55)
    print("\n  Usuarios de prueba:")
    print("  Email                           | Rol")
    print("  --------------------------------|----------------")
    print("  solicitante@novum.com           | solicitante")
    print("  coordinador@novum.com           | coordinador")
    print("  bodeguero@novum.com             | bodeguero")
    print("  Password para todos: password123")
    print()

    db.close()


if __name__ == "__main__":
    seed()
