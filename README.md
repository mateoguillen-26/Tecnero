# Sistema de Gestión de Requerimientos de Materiales
## Corporación Novum – Cilindros GLP

Sistema web para digitalizar el proceso de requerimientos de materia prima, reemplazando el proceso manual en papel.

---

## Requisitos

- Python 3.10 o superior
- pip

---

## Instalación

```bash
# 1. Clonar / descomprimir el proyecto
cd TECNERO

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Cargar datos iniciales (ejecutar desde la carpeta backend/)
cd backend
python seed.py

# 4. Levantar el servidor (ejecutar desde la carpeta backend/)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Abrir en el navegador: **http://localhost:8000**

---

## Usuarios de prueba

| Email                      | Contraseña  | Rol         |
|----------------------------|-------------|-------------|
| solicitante@novum.com      | password123 | Solicitante |
| coordinador@novum.com      | password123 | Coordinador |
| bodeguero@novum.com        | password123 | Bodeguero   |

---

## Estructura del proyecto

```
TECNERO/
├── backend/
│   ├── main.py              # Punto de entrada FastAPI, CORS, rutas estáticas
│   ├── database.py          # Motor SQLite, sesión SQLAlchemy
│   ├── models.py            # Modelos ORM (tablas)
│   ├── schemas.py           # Esquemas Pydantic (validación / serialización)
│   ├── auth.py              # JWT, hashing, dependencias de autenticación
│   ├── seed.py              # Datos iniciales de prueba
│   └── routers/
│       ├── usuarios.py      # Login, registro de usuarios
│       ├── materiales.py    # CRUD materiales + lógica de alertas
│       ├── solicitudes.py   # Crear / listar solicitudes
│       ├── aprobaciones.py  # Aprobación / rechazo (coordinador)
│       ├── bodega.py        # Despacho y descuento de stock
│       ├── dashboard.py     # KPIs, gráficos, inventario
│       ├── reportes.py      # Reportes exportables
│       ├── alertas.py       # Gestión de alertas de stock
│       └── lineas.py        # Líneas de producción
├── frontend/
│   ├── index.html           # Login
│   ├── dashboard.html       # Dashboard principal
│   ├── solicitudes.html     # Historial de solicitudes (solicitante)
│   ├── nueva-solicitud.html # Crear solicitud (solicitante)
│   ├── aprobaciones.html    # Aprobar / rechazar (coordinador)
│   ├── materiales.html      # CRUD materiales (coordinador / bodeguero)
│   ├── bodega.html          # Despacho (bodeguero)
│   ├── reportes.html        # Reportes imprimibles
│   ├── alertas.html         # Alertas de stock
│   ├── css/styles.css       # Estilos globales
│   └── js/
│       ├── api.js           # Helper fetch, auth, formateadores
│       └── sidebar.js       # Sidebar reutilizable
├── requirements.txt
└── README.md
```

---

## Módulos del sistema

### Autenticación
- Login con email/password, JWT con expiración de 8 horas
- Protección de rutas por rol

### Solicitudes (Solicitante)
- Crear nuevas solicitudes eligiendo línea de producción, fecha requerida y materiales
- El precio unitario se captura como snapshot en el momento de crear la solicitud
- Cálculo en tiempo real del subtotal por ítem y total de la solicitud

### Aprobaciones (Coordinador)
- Ver todas las solicitudes pendientes
- Aprobar ajustando cantidades por ítem, o rechazar con comentario
- Registro automático en historial de estados

### Bodega / Despacho (Bodeguero)
- Ver solicitudes aprobadas pendientes de entrega
- Confirmar entrega: descuenta stock_actual por cantidad_aprobada
- Verifica alertas automáticamente tras el descuento

### Materiales (Coordinador / Bodeguero)
- CRUD completo con validaciones
- Editar precio sin afectar solicitudes pasadas (snapshot)
- Alertas automáticas al guardar si stock_actual ≤ stock_minimo

### Dashboard (todos los roles)
- KPIs del mes (solicitudes, monto, pendientes, alertas)
- Gráfico de gasto por línea de producción con porcentajes
- Top 5 materiales por valor
- Semáforo de inventario en tiempo real
- Panel de alertas activas

### Reportes (Coordinador / Bodeguero)
- Gasto por línea de producción con desglose por material
- Historial por material específico
- Estado actual del inventario con valor total
- Todos imprimibles con `window.print()` (CSS de impresión incluido)

---

## Supuestos y decisiones de diseño

1. **Precio_unitario_snapshot**: Se guarda el precio al momento de crear la solicitud. Si el coordinador edita el precio del material después, las solicitudes anteriores no se ven afectadas. Esto garantiza trazabilidad del costo real.

2. **Subtotal estimado**: Mientras la solicitud está pendiente, el subtotal se calcula con `cantidad_solicitada × precio_snapshot`. Una vez aprobada, se usa `cantidad_aprobada × precio_snapshot`.

3. **Concurrencia en SQLite**: Se usa `check_same_thread=False` en la configuración de SQLAlchemy, que es apropiado para el volumen de usuarios internos esperado. Para producción con alta concurrencia se recomienda migrar a PostgreSQL.

4. **Alertas**: Una alerta por material. Si ya existe una alerta activa para un material y el stock empeora, se actualiza el mensaje. Si el stock mejora (supera el mínimo), la alerta se desactiva automáticamente.

5. **Dashboard filtrable**: El gráfico de gasto por línea y los KPIs de monto son filtrables por rango de fechas. Por defecto muestran el mes actual.

6. **Visibilidad por rol**:
   - Solicitante: solo ve sus propias solicitudes y puede crear nuevas
   - Coordinador: ve todas las solicitudes, puede aprobar/rechazar, gestionar materiales, ver reportes
   - Bodeguero: ve solicitudes aprobadas para despachar, puede editar stock de materiales, ver reportes

7. **Eliminación de materiales**: Soft delete (activo = false). Un material inactivo no aparece en nuevas solicitudes pero su historial se preserva.

8. **Estados de solicitud**: Flujo estricto pendiente → aprobada/rechazada → entregada. No se puede saltar estados ni retroceder.
