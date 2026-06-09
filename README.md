# Sistema de Gestión de Requerimientos de Materiales
## Corporación Novum – Cilindros GLP

Sistema web para digitalizar el proceso de requerimientos de materia prima y pedidos de compra, reemplazando el proceso manual en papel.

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
│   ├── main.py              # Punto de entrada FastAPI, CORS, rutas estáticas, no-cache headers
│   ├── database.py          # Motor SQLite con ruta absoluta, sesión SQLAlchemy
│   ├── models.py            # Modelos ORM (tablas)
│   ├── schemas.py           # Esquemas Pydantic (validación / serialización)
│   ├── auth.py              # JWT, hashing, dependencias de autenticación
│   ├── seed.py              # Datos base: líneas, materiales y usuarios (sin transacciones de ejemplo)
│   └── routers/
│       ├── usuarios.py      # Login, registro de usuarios
│       ├── materiales.py    # CRUD materiales + lógica de alertas automáticas
│       ├── solicitudes.py   # Crear / listar solicitudes de producción
│       ├── aprobaciones.py  # Aprobación / rechazo (coordinador); pedidos de compra se completan aquí
│       ├── bodega.py        # Despacho de requerimientos + creación/listado de pedidos de compra
│       ├── dashboard.py     # KPIs, gráficos e inventario (solo requerimientos de producción)
│       ├── reportes.py      # Reportes exportables
│       ├── alertas.py       # Gestión de alertas de stock
│       └── lineas.py        # Líneas de producción
├── frontend/
│   ├── index.html           # Login con redirección por rol
│   ├── dashboard.html       # Dashboard del coordinador (solo requerimientos)
│   ├── solicitudes.html     # Historial de solicitudes (solicitante)
│   ├── nueva-solicitud.html # Crear solicitud (solicitante)
│   ├── aprobaciones.html    # Aprobar / rechazar requerimientos y pedidos de compra (coordinador)
│   ├── materiales.html      # CRUD materiales (coordinador / bodeguero)
│   ├── bodega.html          # Despacho de requerimientos + pedidos de compra (bodeguero)
│   ├── reportes.html        # Reportes imprimibles (coordinador / bodeguero)
│   ├── alertas.html         # Alertas de stock con botón de pedido rápido (coordinador / bodeguero)
│   ├── css/styles.css       # Estilos globales
│   └── js/
│       ├── api.js           # Helper fetch, auth, formateadores, sidebar init con badge de alertas
│       └── sidebar.js       # Sidebar reutilizable con badge de alertas activas
├── requirements.txt
└── README.md
```

---

## Módulos del sistema

### Autenticación
- Login con email/password, JWT con expiración de 8 horas
- Protección de rutas por rol en frontend (`requireAuth`) y backend (`require_roles`)
- Redirección por rol al hacer login: solicitante → solicitudes, bodeguero → bodega, coordinador → dashboard
- Sin flash de página incorrecta: la página se oculta hasta confirmar la sesión

### Solicitudes de Producción (Solicitante)
- Crear nuevas solicitudes eligiendo línea de producción, fecha requerida y materiales
- El precio unitario se captura como snapshot en el momento de crear la solicitud
- Cálculo en tiempo real del subtotal por ítem y total de la solicitud

### Aprobaciones (Coordinador)
- Dos pestañas: **Requerimientos de Producción** y **Pedidos de Compra**
- Aprobar ajustando cantidades por ítem, o rechazar con comentario
- Al aprobar un **requerimiento**: pasa a estado `aprobada`, queda pendiente de despacho por bodeguero
- Al aprobar un **pedido de compra**: el stock de cada material aumenta inmediatamente y el pedido pasa a estado `recibida` (no requiere acción adicional del bodeguero)
- Registro automático en historial de estados

### Bodega (Bodeguero)
**Pestaña Despacho:**
- Ver solicitudes de producción aprobadas pendientes de entrega
- Confirmar entrega: descuenta `stock_actual` por `cantidad_aprobada`
- Verificación de stock antes de despachar; bloquea si hay faltantes
- Verifica alertas automáticamente tras el descuento

**Pestaña Pedidos de Compra:**
- Crear pedidos de compra para reponer stock (van al coordinador para aprobación)
- Historial de pedidos con estados: Pendiente / Recibido / Rechazado
- El restock es automático al momento de la aprobación del coordinador

### Alertas de Stock
- Tabla de alertas con estado visual (activa / resuelta)
- El bodeguero puede crear un pedido de compra directamente desde la alerta con cantidad presugerida (`stock_mínimo - stock_actual`)
- El coordinador puede resolver alertas manualmente
- Badge rojo con conteo en el sidebar para coordinador y bodeguero

### Materiales (Coordinador / Bodeguero)
- CRUD completo con validaciones
- Editar precio sin afectar solicitudes pasadas (snapshot)
- Alertas automáticas al guardar si `stock_actual ≤ stock_minimo`

### Dashboard (Coordinador)
- Filtro por rango de fechas; se actualiza automáticamente al cambiar cualquier fecha
- Botón "Este mes" que fija el rango completo del mes actual (del 1 al último día)
- **Solo contabiliza requerimientos de producción** (excluye pedidos de compra)
- KPIs: solicitudes del mes, monto total, pendientes de aprobación, alertas activas
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

## Flujo completo de operaciones

### Requerimiento de producción
```
Solicitante crea solicitud
  → Coordinador revisa y aprueba/rechaza (ajusta cantidades)
  → Si aprobada: Bodeguero despacha → stock disminuye → estado "entregada"
```

### Pedido de compra (reposición de stock)
```
Bodeguero crea pedido (desde Bodega → Pedidos o desde Alertas → Pedir)
  → Coordinador revisa y aprueba/rechaza
  → Si aprobado: stock aumenta inmediatamente → estado "recibida"
```

---

## Supuestos y decisiones de diseño

1. **Precio_unitario_snapshot**: Se guarda el precio al momento de crear la solicitud. Si el coordinador edita el precio del material después, las solicitudes anteriores no se ven afectadas. Esto garantiza trazabilidad del costo real.

2. **Subtotal estimado**: Mientras la solicitud está pendiente, el subtotal se calcula con `cantidad_solicitada × precio_snapshot`. Una vez aprobada, se usa `cantidad_aprobada × precio_snapshot`.

3. **Concurrencia en SQLite**: Se usa `check_same_thread=False` en la configuración de SQLAlchemy, apropiado para el volumen de usuarios internos esperado. Para producción con alta concurrencia se recomienda migrar a PostgreSQL.

4. **Alertas**: Una alerta por material. Si ya existe una alerta activa y el stock empeora, se actualiza el mensaje. Si el stock supera el mínimo (p. ej. tras recibir un pedido de compra), la alerta se desactiva automáticamente.

5. **Dashboard filtrable**: KPIs y gráficos son filtrables por rango de fechas; el filtro se aplica automáticamente al cambiar las fechas. Solo contabiliza requerimientos de producción, no pedidos de compra.

6. **Pedidos de compra vs requerimientos**: Ambos usan la tabla `solicitudes` con un campo `tipo` (`requerimiento` | `pedido_compra`). El flujo posterior es diferente: los requerimientos pasan por bodega para despacho y descuentan stock; los pedidos de compra aumentan stock al ser aprobados por el coordinador.

7. **Visibilidad por rol**:
   - **Solicitante**: solo ve sus propias solicitudes y puede crear nuevas; redirigido a `/solicitudes.html` al hacer login
   - **Coordinador**: ve todas las solicitudes y pedidos de compra, puede aprobar/rechazar, gestionar materiales, ver dashboard y reportes; redirigido a `/dashboard.html`
   - **Bodeguero**: despacha requerimientos aprobados, crea pedidos de compra, gestiona alertas, ve materiales y reportes; redirigido a `/bodega.html`

8. **Eliminación de materiales**: Soft delete (`activo = false`). Un material inactivo no aparece en nuevas solicitudes pero su historial se preserva.

9. **Estados de solicitud**:
   - Requerimiento: `pendiente → aprobada/rechazada → entregada`
   - Pedido de compra: `pendiente → recibida/rechazada` (el estado `aprobada` se salta, el stock sube en el mismo acto de aprobación)

10. **Ruta de la base de datos**: `database.py` usa `os.path.abspath(__file__)` para construir la ruta de `novum.db`, lo que garantiza que el servidor y el seed apunten siempre al mismo archivo independientemente del directorio de trabajo actual.

11. **Caché del navegador**: Los archivos HTML se sirven con `Cache-Control: no-store`. Los archivos JS llevan query string de versión (`?v=4`) para forzar recarga cuando cambia su contenido.
