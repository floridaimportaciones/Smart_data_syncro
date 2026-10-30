# Smart Data Syncro

Sistema de punto de venta de escritorio (Tkinter + SQLite) para un negocio de retail: clientes, inventario, ventas, ventas a crédito ("separados"), usuarios/permisos por sucursal, y reportes.

## Stack

- Python 3 + Tkinter (UI de escritorio)
- SQLAlchemy sobre SQLite (capa de datos)
- reportlab (facturas en PDF), matplotlib (gráficos de reportes), openpyxl (export a Excel), tkcalendar (selector de fechas)

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
UI (clientes.py, ventas.py, inventario.py, ...)   → solo Tkinter, nada de SQL
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
index.py            punto de entrada (Manager → Login → Container)
manager.py           ventana principal
container.py         pestañas del menú principal
login.py              login y registro de usuarios

clientes.py, inventario.py, ventas.py, separados.py,
usuarios.py, configuracion.py, reportes.py            módulos de UI (uno por pestaña)

db/
  models.py           modelos SQLAlchemy
  engine.py            conexión (SessionLocal)
  schema.sql            esquema completo, para recrear la base

repositories/          un archivo por tabla, única capa que toca SQL
services/               reglas de negocio, lo único que la UI conoce

utils.py                helpers de rutas (independientes del cwd) e imágenes
permisos.py              permisos por rol (hardcodeado, ver Pendientes)
```

## Módulos

- **Clientes**: alta/edición/búsqueda de clientes.
- **Inventario**: artículos por código único, stock por sucursal, importación/actualización masiva por Excel/CSV.
- **Ventas**: carrito, cobro (efectivo/transferencia/tarjeta/pago parcial), descuenta stock, genera factura PDF, reporte de ventas realizadas.
- **Separados**: ventas a crédito/fiado — abono inicial, abonos adicionales, se convierte automáticamente en venta al quedar pagado.
- **Usuarios**: alta de usuarios, rol (Administrador/Cajero) y sucursal asignada.
- **Configuración**: sucursales, datos de la empresa, copia de seguridad/restauración de la base.
- **Reportes**: ventas totales, ganancias, gráficos por mes, export a Excel.

## Pendientes conocidos

- **Contraseñas en texto plano**: `login.py` compara la contraseña tal cual contra la base, sin hash. Pendiente de migrar a bcrypt o similar.
- **`permisos.py` hardcodeado**: los permisos por rol están en código (`if rol == "Administrador"`), la tabla `permisos` de la base nunca se usa.
- **Sin tests automatizados**: todo se probó manualmente durante el desarrollo, no hay suite de tests.
- **Assets faltantes**: `icono.ico` y la carpeta `imagenes/` (íconos de botones) no están en el repo — la app corre igual, sin esas imágenes.
