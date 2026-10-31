# Smart Data Syncro

Sistema de punto de venta de escritorio (PySide6/Qt + SQLite) para un negocio de retail: clientes, inventario, ventas, ventas a crédito ("separados"), usuarios/permisos por rol, reportes e impresión nativa de facturas.

## Stack

- Python 3 + PySide6/Qt (UI de escritorio)
- SQLAlchemy sobre SQLite (capa de datos)
- `QPrinter`/`QPainter` (facturas en PDF e impresión nativa, sin reportlab), matplotlib (gráficos de reportes), openpyxl (import/export a Excel)

## Instalación

```bash
pip install -r requirements.txt
```

## Cómo correr

Desde la carpeta **padre** de `Smart_data_syncro` (los imports del proyecto son absolutos, tipo `Smart_data_syncro.algo`):

```bash
cd ..
python -m Smart_data_syncro.index
```

Correrlo con `python index.py` directo desde adentro de la carpeta **no funciona** — rompe los imports.

La base de datos vive en `Smart_data_syncro/database.db` (SQLite). El esquema completo está en `db/schema.sql`, para recrearla desde cero si hace falta.

## Arquitectura

El proyecto está organizado en capas, cada una con una sola responsabilidad:

```text
UI (qt_ui/*.py)   → solo PySide6, nada de SQL
    ↓
services/   → reglas de negocio y validación (la UI solo llama a esto)
    ↓
repositories/   → único lugar que habla SQLAlchemy/SQL por tabla
    ↓
db/models.py, db/engine.py   → modelos ORM y conexión
```

Ningún archivo de UI abre conexiones SQL directo — todo pasa por un service. Cada tabla tiene su propio repository (`cliente_repository.py`, `venta_repository.py`, etc.) y su service correspondiente (`cliente_service.py`, `venta_service.py`, etc.), siguiendo siempre el mismo molde: repository habla con la base, service valida y aplica reglas de negocio, la UI solo pinta y reacciona a clicks.

## Estructura

```text
index.py                 punto de entrada (QApplication → Login → MainWindow, en loop por el logout)

qt_ui/
  login_window.py         login y auto-registro (con código de registro configurable)
  main_window.py           ventana principal, barra de módulos segun permisos
  ventas_window.py          carrito, cobro, factura PDF + impresión nativa
  ventas_reporte_window.py   reporte de ventas realizadas
  separados_window.py        ventas a crédito/fiado + su reporte
  inventario_window.py       artículos, stock, import Excel/CSV
  clientes_window.py          alta/edición/búsqueda de clientes
  usuarios_window.py           alta de usuarios, rol y sucursal
  configuracion_window.py       sucursales, datos de empresa, backup/restore, permisos
  permisos_window.py             admin de permisos por rol (checkbox por módulo)
  reportes_window.py              ventas totales, ganancias, gráficos, export Excel
  theme.py                         QSS compartido por todas las pantallas

pos_ticket.py            genera el ticket (PDF vía QPrinter) e imprime nativo (QPrintDialog)

db/
  models.py           modelos SQLAlchemy
  engine.py            conexión (SessionLocal)
  schema.sql            esquema completo, para recrear la base

repositories/          un archivo por tabla, única capa que toca SQL
services/               reglas de negocio, lo único que la UI conoce

utils.py                helpers de rutas (independientes del cwd) e imágenes
excel_import.py          lectura de archivos Excel/CSV para import de inventario
```

Los `.py` de Tkinter en la raíz (`manager.py`, `container.py`, `login.py`, `ventas.py`, `inventario.py`, `clientes.py`, `usuarios.py`, `configuracion.py`, `reportes.py`, `separados.py`) son código muerto: quedaron del diseño anterior, `index.py` ya no los importa. La migración a Qt está completa en los 7 módulos.

## Módulos

- **Clientes**: alta/edición/búsqueda de clientes.
- **Inventario**: artículos por código único, stock por sucursal, importación/actualización masiva por Excel/CSV.
- **Ventas**: carrito con autocompletado por nombre/código, cobro (efectivo/transferencia/tarjeta/pago parcial), descuenta stock, genera factura PDF e imprime nativo (`QPrintDialog`, elige impresora real), reporte de ventas realizadas.
- **Separados**: ventas a crédito/fiado — abono inicial, abonos adicionales con historial, se convierte automáticamente en venta al quedar pagado.
- **Usuarios**: alta de usuarios, rol (Administrador/Cajero) y sucursal asignada.
- **Configuración**: sucursales, datos de la empresa (incluye código de registro para el auto-registro del login), copia de seguridad/restauración de la base, administración de permisos.
- **Permisos**: pantalla de checkboxes (rol × módulo) que otorga/revoca acceso en vivo contra la tabla `permisos`.
- **Reportes**: ventas totales, ganancias, gráficos por mes, export a Excel.

## Pendientes conocidos

- **Contraseñas en texto plano**: `login_window.py` compara la contraseña tal cual contra la base, sin hash. Pendiente de migrar a bcrypt o similar.
- **Sin tests automatizados**: todo se probó manualmente (y con scripts ad hoc headless) durante el desarrollo, no hay suite de tests.
- **Sin commits de esta migración**: el repo tiene cambios acumulados sin commitear desde que arrancó el rediseño.
- **Assets faltantes**: `icono.ico` y la carpeta `imagenes/` (íconos de botones) no están en el repo — la app corre igual, sin esas imágenes/ícono.
- **Impresión térmica sin probar en hardware real**: `imprimir_ticket()` usa el diálogo nativo de Qt (`QPrintDialog`), pero nunca se probó contra una impresora térmica POS física — solo se validó generando PDF.
