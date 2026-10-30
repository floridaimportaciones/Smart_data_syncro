from tkinter import *
from tkcalendar import Calendar
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
import threading

import sys
import os
from PIL import Image, ImageTk
from Smart_data_syncro.utils import rutas
from Smart_data_syncro.pos_ticket import generar_ticket_pdf
from Smart_data_syncro.services.articulo_service import ArticuloService
from Smart_data_syncro.services.cliente_service import ClienteService
from Smart_data_syncro.services.usuario_service import UsuarioService
from Smart_data_syncro.services.venta_service import VentaService
from Smart_data_syncro.services.empresa_service import EmpresaService

class Ventas(tk.Frame):
    import os

    def __init__(self, padre, username=None):
        super().__init__(padre)
        self.articulo_service = ArticuloService()
        self.cliente_service = ClienteService()
        self.usuario_service = UsuarioService()
        self.venta_service = VentaService(articulo_service=self.articulo_service)
        self.empresa_service = EmpresaService()
        self.username = username
        self.sucursal = None
        if self.username:
            self.sucursal = self.obtener_sucursal_usuario()
        self.numero_factura = self.obtener_numero_factura_actual()
        self.productos_seleccionados = []
        self.folio_inicial = 1  
        self.folio_final = 99999  
        self.widgets()
        self.cargar_productos()
        self.cargar_clientes()
        self.timer_producto = None
        self.timer_cliente = None
        # Timer para detectar scanners que no envían <Return>
        self.barcode_timer_producto = None
        self.bind("<<ClienteActualizado>>", lambda e: self.cargar_clientes())
        self.actualizar_folios_disponibles()

    def actualizar_folios_disponibles(self):
        folio_actual = self.numero_factura
        folios_restantes = max(self.folio_final - folio_actual + 1, 0)
        if hasattr(self, 'label_folios'):
            self.label_folios.config(text=f"Folios disponibles: {folios_restantes}")
        else:
            self.label_folios = tk.Label(self, text=f"Folios disponibles: {folios_restantes}", font="sans 12 bold", bg="#c9dbe1")
            self.label_folios.place(x=900, y=10)



    def obtener_numero_factura_actual(self):
        try:
            return self.venta_service.siguiente_numero_factura()
        except Exception as e:
            print("Error al obtener el número de factura actual: ", e)
            return 1
        
    def cargar_clientes(self):
        try:
            self.clientes = [cliente.nombre for cliente in self.cliente_service.listar()]
            self.entry_cliente["values"] = self.clientes
        except Exception as e:
            print("Error al cargar los clientes en Ventas: ", e)

    def filtrar_clientes(self, event): 
        if self.timer_cliente:
            self.timer_cliente.cancel()
        self.timer_cliente = threading.Timer(0.5, self._filter_clientes)
        self.timer_cliente.start()
        
    def _filter_clientes(self):
        """Filtra la lista de clientes en el Combobox."""
        typed = self.entry_cliente.get()
        if typed == '':
            data = self.clientes # Si no hay texto, muestra todos los clientes
        else:
            # Filtra directamente sobre la lista de strings self.clientes
            data = [p for p in self.clientes if typed.lower() in p.lower()]
        
        self.entry_cliente['values'] = data if data else ['No se encontraron resultados']
        self.entry_cliente.event_generate('<Down>') # Abre la lista desplegable
        if not data:
            self.entry_cliente.delete(0, tk.END) 

    def cargar_productos(self):
        try:
            # Mostrar TODOS los productos sin excepción
            self.products = [{"id": a.id, "nombre": a.articulo, "codigo": a.codigo} for a in self.articulo_service.listar()]
            # Mostrar en el combo "Nombre [Código]" si hay código, para forzar selección por código
            def _display(p):
                code = str(p.get("codigo") or '').strip()
                return f"{p['nombre']} [{code}]" if code else p['nombre']
            self.entry_producto["values"] = [_display(p) for p in self.products]
        except Exception as e:
            print("Error al cargar los productos: ", e)

    def filtrar_productos(self, event): 
        if self.timer_producto:
            self.timer_producto.cancel()
        self.timer_producto = threading.Timer(0.5, self._filter_products)
        self.timer_producto.start()
        # Detección por temporizador para lectores que no envían <Return>
        try:
            if getattr(self, 'barcode_timer_producto', None):
                try:
                    self.barcode_timer_producto.cancel()
                except Exception:
                    pass
            typed_now = self.entry_producto.get().strip()
            # Heurística: si contiene dígitos y tiene al menos 3 caracteres, probablemente sea un código
            if typed_now and (typed_now.isdigit() or (any(ch.isdigit() for ch in typed_now) and len(typed_now) >= 3)):
                def _call():
                    try:
                        self.after(0, self._maybe_on_producto_enter)
                    except Exception:
                        pass
                self.barcode_timer_producto = threading.Timer(0.25, _call)
                self.barcode_timer_producto.start()
        except Exception:
            pass

    def _maybe_on_producto_enter(self):
        """Llama a on_producto_enter solo si el campo producto aún tiene el foco.
        Esto permite que el usuario salga del combobox sin que el timer obligue una selección.
        """
        try:
            # Si el focus está en el combobox, proceder
            if self.entry_producto.focus_get() == self.entry_producto:
                self.on_producto_enter()
        except Exception:
            pass

    def _cancel_barcode_timers(self, event=None):
        """Cancela timers pendientes para evitar ejecuciones automáticas tras perder foco."""
        try:
            if getattr(self, 'timer_producto', None):
                try:
                    self.timer_producto.cancel()
                except Exception:
                    pass
            if getattr(self, 'barcode_timer_producto', None):
                try:
                    self.barcode_timer_producto.cancel()
                except Exception:
                    pass
        except Exception:
            pass
        
    def _filter_products(self):
        typed = self.entry_producto.get()
        if typed == '':
            data = [
                f"{p['nombre']} [{str(p.get('codigo') or '').strip()}]" if p.get('codigo') else p['nombre']
                for p in self.products
            ]
        else:
            data = [
                (f"{p['nombre']} [{str(p.get('codigo') or '').strip()}]" if p.get('codigo') else p['nombre'])
                for p in self.products
                if typed.lower() in p["nombre"].lower() or typed in (str(p["codigo"]) if p.get("codigo") is not None else '')
            ]
        # Actualizar las opciones mostradas en el combobox.
        # No borramos el texto del campo: si el usuario o el escáner han puesto un valor
        # preferimos mantenerlo visible aunque no haya coincidencias inmediatamente.
        self.entry_producto['values'] = data if data else ['No se encontraron resultados']

    def _extract_codigo(self, value: str):
        """Devuelve el código a partir del valor del combobox.
        Soporta formatos: "Nombre [COD]" o directamente "COD".
        Si recibe un nombre sin código pero hay un único producto con ese nombre,
        usa el código de ese único producto; si hay varios, retorna None para forzar elección por código.
        """
        if not value:
            return None
        val = str(value).strip()
        # Caso "Nombre [COD]"
        if val.endswith("]") and "[" in val:
            try:
                return val[val.rfind("[") + 1:-1].strip()
            except Exception:
                pass
        # Si coincide exactamente con un código existente
        for p in self.products:
            code = str(p.get("codigo") or '').strip()
            if code and val == code:
                return code
        # Si coincide por nombre exacto
        matches = [p for p in self.products if p["nombre"] == val]
        if len(matches) == 1:
            return str(matches[0].get("codigo") or '').strip() or None
        # Si nombre parcial y hay varios códigos, forzar a elegir con código
        return None

    def on_producto_enter(self, event=None):
        """Detecta cuando se ingresa un código (p. ej. por escáner) en `entry_producto`.
        Si el valor coincide con el campo `codigo` de algún producto, lo agrega
        directamente al Treeview con la cantidad indicada en el campo "Cantidad"
        (si es válida); de lo contrario usa 1. Mantiene el foco en el campo de
        producto para permitir escaneos consecutivos rápidos.
        """
        try:
            # Cancelar timers pendientes para evitar que el filtrado posterior sobreescriba el valor
            try:
                if getattr(self, 'timer_producto', None):
                    self.timer_producto.cancel()
            except Exception:
                pass
            try:
                if getattr(self, 'barcode_timer_producto', None):
                    self.barcode_timer_producto.cancel()
            except Exception:
                pass
            val = str(self.entry_producto.get()).strip()
            if not val:
                return

            # Buscar coincidencia exacta por código
            matched = None
            for p in getattr(self, 'products', []):
                code = str(p.get('codigo') or '').strip()
                if code and val == code:
                    matched = p
                    break

            # Si no hay coincidencia exacta, intentar limpiar caracteres no imprimibles
            if not matched:
                cleaned = ''.join(ch for ch in val if ch.isprintable()).strip()
                for p in getattr(self, 'products', []):
                    code = str(p.get('codigo') or '').strip()
                    if code and cleaned == code:
                        matched = p
                        break

            if matched:
                code = str(matched.get('codigo') or '').strip()
                # Determinar cantidad: si el usuario digitó una válida, usarla; si no, 1
                qty_text = None
                try:
                    qty_text = self.entry_cantidad.get()
                except Exception:
                    qty_text = None
                try:
                    cantidad = int(qty_text) if qty_text and str(qty_text).isdigit() and int(qty_text) > 0 else 1
                except Exception:
                    cantidad = 1
                # Agregar de inmediato por código
                try:
                    self._agregar_articulo_por_codigo(code, cantidad)
                except Exception as _e:
                    print(f"[WARN] No se pudo agregar por código {code}: {_e}")
                # Limpiar el campo de producto y mantener el foco para el siguiente escaneo
                try:
                    self.entry_producto.set('')
                except Exception:
                    try:
                        self.entry_producto.delete(0, 'end')
                    except Exception:
                        pass
                try:
                    self.entry_producto.focus_set()
                except Exception:
                    pass

        except Exception as e:
            print(f"[WARN] Error en on_producto_enter: {e}")

    def _agregar_articulo_por_codigo(self, codigo: str, cantidad: int = 1):
        """Agrega directamente un artículo al Treeview usando su código de barras.
        - Respeta validación de cliente seleccionado.
        - Verifica stock total por código.
        - Actualiza self.productos_seleccionados y el total a pagar.
        """
        if not codigo:
            return
        cliente = self.entry_cliente.get()
        if not cliente:
            messagebox.showerror("Error", "Por favor, seleccione un cliente antes de escanear.")
            return
        try:
            art = self.articulo_service.obtener_por_codigo(codigo)
            if not art:
                messagebox.showerror("Error", "No se encontró un artículo con ese código.")
                return
            if cantidad > art.stock:
                messagebox.showerror("Error", f"No hay suficiente stock. Solo hay {int(art.stock)} unidades disponibles para el código {codigo}.")
                return
            total = cantidad * float(art.precio)
            total_cop = "{:,.0f}".format(total)
            # Insertar al Treeview
            self.tre.insert("", "end", values=(self.numero_factura, cliente, art.articulo, "{:,.0f}".format(art.precio), cantidad, total_cop))
            # Registrar internamente, preservando el código
            self.productos_seleccionados.append((self.numero_factura, cliente, art.articulo, float(art.precio), cantidad, total_cop, float(art.costo), codigo))
            # Recalcular total
            self.calcular_precio_total()
        except Exception as e:
            print("Error al agregar por código: ", e)

    def show_all_products(self, event=None):
        """Muestra todos los productos en el combobox (útil cuando el producto no tiene código).
        Se usa al enfocar o al hacer click en el combobox para desplegar la lista completa.
        """
        try:
            vals = [
                f"{p['nombre']} [{str(p.get('codigo') or '').strip()}]" if p.get('codigo') else p['nombre']
                for p in getattr(self, 'products', [])
            ]
            if vals:
                try:
                    self.entry_producto['values'] = vals
                except Exception:
                    pass
            # No abrir automáticamente el desplegable; el usuario puede abrirlo con la flecha o tecla.
        except Exception:
            pass

    def agregar_articulo(self):
        cliente = self.entry_cliente.get()
        producto_val = self.entry_producto.get()
        cantidad = self.entry_cantidad.get()
        
        if not cliente:
            messagebox.showerror("Error", "Por favor, seleccione un cliente.")
        
        if not producto_val:
            messagebox.showerror("Error", "Por favor, seleccione un producto.")
            
        if not cantidad.isdigit() or int(cantidad)<= 0:
            messagebox.showerror("Error", "Por favor, ingrese una cantidad válida.")
            return
        
        cantidad = int (cantidad)
        cliente= self.entry_cliente.get()
        
        try:
            # Intentar extraer código desde el valor (Nombre [COD] o COD)
            codigo = self._extract_codigo(producto_val)
            used_exact_code = bool(codigo)

            art = None

            if codigo:
                # Buscar por código
                art = self.articulo_service.obtener_por_codigo(codigo)
                if not art:
                    messagebox.showerror("Error", "No se encontró un artículo con ese código.")
                    return
                if cantidad > art.stock:
                    messagebox.showerror("Error", f"No hay suficiente stock. Solo hay {int(art.stock)} unidades disponibles para el código {codigo}.")
                    return
            else:
                # No se proporcionó código: intentar buscar por nombre exacto
                art = self.articulo_service.obtener_por_nombre(producto_val)
                if art:
                    if cantidad > art.stock:
                        messagebox.showerror("Error", f"No hay suficiente stock. Solo hay {int(art.stock)} unidades disponibles para el producto {art.articulo}.")
                        return
                else:
                    # Intentar búsqueda parcial (no obligatoria seleccionar de la lista)
                    coincidencias = self.articulo_service.listar(producto_val)
                    art = coincidencias[0] if coincidencias else None
                    if art:
                        if cantidad > art.stock:
                            messagebox.showerror("Error", f"No hay suficiente stock. Solo hay {int(art.stock)} unidades disponibles para el producto {art.articulo}.")
                            return
                    else:
                        # No se encontró por nombre ni por parcial; informar al usuario
                        messagebox.showerror("Error", "No se encontró el producto. Escriba el nombre exactamente o use el código del producto.")
                        return

            art_nombre, precio, costo = art.articulo, art.precio, art.costo
            codigo = str(art.codigo).strip() if art.codigo is not None else None
            total = cantidad * precio
            total_cop = "{:,.0f}".format(total)

            self.tre.insert("", "end", values = (self.numero_factura, cliente, art_nombre, "{:,.0f}".format(precio), cantidad, total_cop))
            # Guardar el CÓDIGO del producto para rebajar stock estrictamente por código
            # Si no hay código, almacenamos None en la tupla (manteniendo compatibilidad)
            self.productos_seleccionados.append((self.numero_factura, cliente, art_nombre, precio, cantidad, total_cop, costo, codigo))

            self.calcular_precio_total()

            # Solo limpiar el campo producto si el usuario ingresó un código explícito (escaneo o escritura del código)
            if used_exact_code:
                try:
                    self.entry_producto.set('')
                except Exception:
                    pass
            # Siempre limpiar la cantidad para la siguiente entrada
            try:
                self.entry_cantidad.delete(0,'end')
            except Exception:
                pass

        except Exception as e:
            print("Error al agregar articulo: ", e)
            
    def calcular_precio_total(self):
        total_pagar = sum(float(str(self.tre.item(item)["values"][-1]).replace(" ","").replace(",","")) for item in self.tre.get_children())
        try:
            descuento = float(self.entry_descuento.get()) if self.entry_descuento.get() else 0
        except ValueError:
            descuento = 0
        total_final = max(total_pagar - descuento, 0)
        total_pagar_cop = "{:,.0f}".format(total_final)
        self.label_precio_total.config(text=f"Precio a pagar: ${total_pagar_cop}")
        self.total_con_descuento = total_final
        self.descuento_actual = descuento

    def actualizar_stock(self, event=None):
        producto_seleccionado = self.entry_producto.get()

        try:
            codigo = self._extract_codigo(producto_seleccionado)
            art = self.articulo_service.obtener_por_codigo(codigo) if codigo else None
            if art:
                self.label_stock.config(text=f"Stock: {int(art.stock)}")
                # Cerrar dropdown del combobox de producto si está abierto y pasar foco a cantidad
                try:
                    try:
                        self.entry_producto.event_generate('<Escape>')
                    except Exception:
                        pass
                    self.entry_cantidad.focus_set()
                except Exception:
                    pass
            else:
                self.label_stock.config(text="Stock: No encontrado.")
        except Exception as e:
            print("Error al obtener el stock del producto", e)
    
    def realizar_pago(self):
        if not self.tre.get_children():
            messagebox.showerror("Error", "No hay productos seleccionados para realizar el pago.")
            return
        # Usar el total con descuento
        total_venta = getattr(self, 'total_con_descuento', None)
        if total_venta is None:
            self.calcular_precio_total()
            total_venta = getattr(self, 'total_con_descuento', 0)
        total_formateado = "{:,.0f}".format(total_venta)
        
        ventana_pago = tk.Toplevel(self)
        ventana_pago.title("Realizar pago")
        ventana_pago.geometry("420x620+450+80")
        ventana_pago.config(bg="#c9dbe1")
        ventana_pago.resizable(False,False)
        ventana_pago.transient(self.master)
        ventana_pago.grab_set()
        ventana_pago.focus_set()
        ventana_pago.lift()
        
        label_titulo = tk.Label(ventana_pago, text = "Realizar pago", font ="sans 30 bold", bg="#c9dbe1")
        label_titulo.place(x=70, y=10)
        
        label_total = tk.Label(ventana_pago, text = f"Total a pagar: ${total_formateado}", font ="sans 14 bold", bg="#c9dbe1")
        label_total.place(x=80, y=80)
        
        # Frame para método de pago
        metodo_frame = tk.LabelFrame(ventana_pago, text="Método de pago", font="sans 14 bold", bg="#c9dbe1")
        metodo_frame.place(x=50, y=120, width=300, height=120)
        

        metodo_pago = tk.StringVar(value="efectivo")
        banco_opcion = tk.StringVar(value="Bancolombia")

        rb_efectivo = tk.Radiobutton(metodo_frame, text="Efectivo", font="sans 12", 
                                   variable=metodo_pago, value="efectivo",
                                   bg="#c9dbe1", command=lambda: mostrar_campo_pago("efectivo"))
        rb_efectivo.place(x=20, y=10)

        rb_transferencia = tk.Radiobutton(metodo_frame, text="Transferencia", font="sans 12",
                                        variable=metodo_pago, value="transferencia",
                                        bg="#c9dbe1", command=lambda: mostrar_campo_pago("transferencia"))
        rb_transferencia.place(x=20, y=50)

        rb_tarjeta = tk.Radiobutton(metodo_frame, text="Tarjeta", font="sans 12",
                                    variable=metodo_pago, value="tarjeta",
                                    bg="#c9dbe1", command=lambda: mostrar_campo_pago("tarjeta"))
        rb_tarjeta.place(x=150, y=10)

        rb_parcial = tk.Radiobutton(metodo_frame, text="Pago parcial", font="sans 12",
                                     variable=metodo_pago, value="pago parcial",
                                     bg="#c9dbe1", command=lambda: mostrar_campo_pago("pago parcial"))
        rb_parcial.place(x=150, y=50)
        
        # Frame para detalles del pago
        detalles_frame = tk.Frame(ventana_pago, bg="#c9dbe1")
        detalles_frame.place(x=50, y=220, width=320, height=360)
        def mostrar_campo_pago(metodo):
            for widget in detalles_frame.winfo_children():
                widget.destroy()
            if metodo == "efectivo":
                label_monto = tk.Label(detalles_frame, text="Ingrese el monto pagado", 
                                     font="sans 14 bold", bg="#c9dbe1")
                label_monto.pack(pady=10)
                entry_monto = ttk.Entry(detalles_frame, font="sans 14 bold")
                entry_monto.pack(pady=10)
                button_confirmar = tk.Button(detalles_frame, text="Confirmar pago", 
                                           font="sans 14 bold",
                                           command=lambda: self.procesar_pago(entry_monto.get(),
                                                                           ventana_pago, 
                                                                           total_venta,
                                                                           "efectivo", descuento=getattr(self, 'descuento_actual', 0)))
                button_confirmar.pack(pady=20)
            elif metodo == "transferencia":
                tk.Label(detalles_frame, text="Seleccione el banco:", font="sans 14 bold", bg="#c9dbe1").pack(pady=5)
                banco_frame = tk.Frame(detalles_frame, bg="#c9dbe1")
                banco_frame.pack(pady=5)
                rb_bancolombia = tk.Radiobutton(banco_frame, text="Bancolombia", font="sans 12", variable=banco_opcion, value="Bancolombia", bg="#c9dbe1")
                rb_bancolombia.pack(anchor='w')
                rb_daviplata = tk.Radiobutton(banco_frame, text="Daviplata", font="sans 12", variable=banco_opcion, value="Daviplata", bg="#c9dbe1")
                rb_daviplata.pack(anchor='w')
                button_confirmar = tk.Button(detalles_frame, text="Confirmar pago", 
                                           font="sans 14 bold",
                                           command=lambda: self.procesar_pago('',  # No se requiere monto
                                                                           ventana_pago, 
                                                                           total_venta,
                                                                           "transferencia", referencia=banco_opcion.get(), descuento=getattr(self, 'descuento_actual', 0)))
                button_confirmar.pack(pady=20)
            elif metodo == "tarjeta":
                label_tarjeta = tk.Label(detalles_frame, text="Pago con tarjeta", font="sans 14 bold", bg="#c9dbe1")
                label_tarjeta.pack(pady=10)
                button_confirmar = tk.Button(detalles_frame, text="Confirmar pago", 
                                           font="sans 14 bold",
                                           command=lambda: self.procesar_pago(total_formateado,
                                                                           ventana_pago, 
                                                                           total_venta,
                                                                           "tarjeta", descuento=getattr(self, 'descuento_actual', 0)))
                button_confirmar.pack(pady=20)
            elif metodo == "pago parcial":
                # Entradas para efectivo y transferencia
                tk.Label(detalles_frame, text="Efectivo:", font="sans 14 bold", bg="#c9dbe1").pack(pady=(10, 0))
                entry_efectivo = ttk.Entry(detalles_frame, font="sans 14 bold")
                entry_efectivo.pack(pady=5)
                tk.Label(detalles_frame, text="Transferencia:", font="sans 14 bold", bg="#c9dbe1").pack(pady=(10, 0))
                entry_transfer = ttk.Entry(detalles_frame, font="sans 14 bold")
                entry_transfer.pack(pady=5)
                # Selección de banco (para la parte en transferencia)
                tk.Label(detalles_frame, text="Banco:", font="sans 14 bold", bg="#c9dbe1").pack(pady=(10, 0))
                banco_frame = tk.Frame(detalles_frame, bg="#c9dbe1")
                banco_frame.pack(pady=5)
                rb_bancolombia = tk.Radiobutton(banco_frame, text="Bancolombia", font="sans 12", variable=banco_opcion, value="Bancolombia", bg="#c9dbe1")
                rb_bancolombia.pack(anchor='w')
                rb_daviplata = tk.Radiobutton(banco_frame, text="Daviplata", font="sans 12", variable=banco_opcion, value="Daviplata", bg="#c9dbe1")
                rb_daviplata.pack(anchor='w')
                msg_lbl = tk.Label(detalles_frame, text="La suma puede ser MAYOR o IGUAL al total. El cambio sale del EFECTIVO.", font="sans 12", bg="#c9dbe1", fg="#444")
                msg_lbl.pack(pady=(10, 0))
                def confirmar_parcial():
                    try:
                        ef = float(entry_efectivo.get() or 0)
                        tr = float(entry_transfer.get() or 0)
                    except ValueError:
                        messagebox.showerror("Error", "Ingrese montos numéricos válidos para efectivo y transferencia.")
                        return
                    if ef < 0 or tr < 0:
                        messagebox.showerror("Error", "Los montos no pueden ser negativos.")
                        return
                    # La transferencia no puede exceder el total (no hay cambio por transferencia)
                    if tr > total_venta:
                        messagebox.showerror("Error", "La transferencia no puede ser mayor que el total a pagar.")
                        return
                    requerido_ef = max(total_venta - tr, 0)
                    if ef < requerido_ef:
                        faltante = requerido_ef - ef
                        messagebox.showerror("Error", f"Efectivo insuficiente. Faltan ${faltante:,.0f}.")
                        return
                    banco_sel = banco_opcion.get() if tr > 0 else None
                    self.procesar_pago('', ventana_pago, total_venta, "pago parcial", referencia=banco_sel, descuento=getattr(self, 'descuento_actual', 0), efectivo_monto=ef, transferencia_monto=tr)
                tk.Button(detalles_frame, text="Confirmar pago parcial", font="sans 14 bold", command=confirmar_parcial).pack(pady=12)
        
        # Mostrar campos de efectivo por defecto
        mostrar_campo_pago("efectivo")   
    
    def procesar_pago(self, cantidad_pagada, ventana_pago, total_venta, metodo_pago, referencia="", descuento=0, efectivo_monto=None, transferencia_monto=None):
        cliente = self.entry_cliente.get()
        banco = None
        if metodo_pago == "transferencia":
            banco = referencia if referencia else None
            total_formateado = "{:,.0f}".format(total_venta)
            mensaje = f"Total: ${total_formateado}\nMétodo: Transferencia\nBanco: {banco if banco else ''}"
        elif metodo_pago == "tarjeta":
            total_formateado = "{:,.0f}".format(total_venta)
            mensaje = f"Total: ${total_formateado}\nMétodo: Tarjeta"
        elif metodo_pago == "pago parcial":
            try:
                ef = float(efectivo_monto or 0)
                tr = float(transferencia_monto or 0)
            except Exception:
                messagebox.showerror("Error", "Montos inválidos para pago parcial.")
                return
            if tr > total_venta:
                messagebox.showerror("Error", "La transferencia no puede ser mayor que el total a pagar.")
                return
            requerido_ef = max(total_venta - tr, 0)
            if ef < requerido_ef:
                faltante = requerido_ef - ef
                messagebox.showerror("Error", f"Efectivo insuficiente. Faltan ${faltante:,.0f}.")
                return
            cambio = max(ef - requerido_ef, 0)
            ef_aplicado = ef - cambio
            banco = referencia if tr > 0 else None
            total_formateado = "{:,.0f}".format(total_venta)
            msg_bank = f"\nBanco: {banco}" if banco else ""
            cambio_str = f"\nCambio: ${cambio:,.0f}" if cambio > 0 else ""
            mensaje = (
                f"Total: ${total_formateado}\nMétodo: Pago parcial\n"
                f"Efectivo: ${ef_aplicado:,.0f}\nTransferencia: ${tr:,.0f}{msg_bank}{cambio_str}"
            )
        else:  # efectivo
            try:
                cantidad_pagada = float(cantidad_pagada)
                if cantidad_pagada < total_venta:
                    messagebox.showerror("Error", "El monto pagado es menor al total de la venta.")
                    return
                cambio = cantidad_pagada - total_venta
                total_formateado = "{:,.0f}".format(total_venta)
                mensaje = f"Total: ${total_formateado}\nCantidad pagada: ${cantidad_pagada:,.0f}\nCambio: ${cambio:,.0f}\nMétodo: Efectivo"
            except ValueError:
                messagebox.showerror("Error", "Por favor, ingrese un monto válido.")
                return
        self.banco_pago = banco
        messagebox.showinfo("Pago realizado", mensaje)

        # Registrar venta y actualizar stock
        try:
            fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
            hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
            sucursal_venta = None
            if self.username:
                usuario = self.usuario_service.obtener_por_username(self.username.strip())
                if usuario:
                    if usuario.rol.lower() in ["admin", "administrador"]:
                        sucursal_venta = "ADMIN"
                    else:
                        sucursal_venta = usuario.sucursal
            if not sucursal_venta or sucursal_venta == "None":
                messagebox.showerror("Error", f"El usuario '{self.username}' no tiene una sucursal asignada. Contacte al administrador.")
                return

            self.venta_service.registrar_venta(
                self.productos_seleccionados, fecha_actual, hora_actual,
                metodo_pago, sucursal_venta, banco, descuento,
            )

            # Si el método fue pago parcial, registrar desglose en abonos_separados para esta factura
            if metodo_pago == "pago parcial":
                try:
                    ef = float(efectivo_monto or 0)
                    tr = float(transferencia_monto or 0)
                except Exception:
                    ef = 0.0
                    tr = 0.0
                # Calcular efectivo aplicado (descontando el cambio)
                requerido_ef = max(total_venta - tr, 0)
                ef_aplicado = max(min(ef, requerido_ef), 0)
                if ef_aplicado and ef_aplicado > 0:
                    self.venta_service.registrar_abono(self.numero_factura, fecha_actual, ef_aplicado, 'efectivo', None, sucursal_venta)
                if tr and tr > 0:
                    self.venta_service.registrar_abono(self.numero_factura, fecha_actual, tr, 'transferencia', banco, sucursal_venta)
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar la venta: {e}")
            return

        # Pasar desglose a la factura si es pago parcial
        if metodo_pago == "pago parcial":
            try:
                ef = float(efectivo_monto or 0)
                tr = float(transferencia_monto or 0)
            except Exception:
                ef = None
                tr = None
            # Calcular efectivo aplicado (sin el cambio) para mostrar en PDF
            requerido_ef = max(total_venta - (tr or 0), 0)
            ef_aplicado = None
            if ef is not None:
                try:
                    ef_aplicado = max(min(ef, requerido_ef), 0)
                except Exception:
                    ef_aplicado = None
            self.generar_factura_pdf(total_venta, cliente, descuento=descuento, banco=banco, efectivo_pagado=ef_aplicado if ef_aplicado and ef_aplicado > 0 else None, transferencia_pagada=tr if tr and tr > 0 else None)
        else:
            self.generar_factura_pdf(total_venta, cliente, descuento=descuento, banco=banco)

        self.numero_factura += 1
        self.label_numero_factura.config(text=str(self.numero_factura))
        self.actualizar_folios_disponibles()
        self.productos_seleccionados = []
        self.limpiar_campos()
        ventana_pago.destroy()
        
    def limpiar_campos(self):
        for item in self.tre.get_children():
            self.tre.delete(item)

    # Limpiar campos de entrada
        self.entry_cliente.set('')
        self.entry_producto.set('')
        self.entry_cantidad.delete(0, 'end')
    
    # Restablecer precio total
        self.label_precio_total.config(text="Precio a pagar: $ 0")

    def limpiar_lista(self):
        self.tre.delete(*self.tre.get_children())
        self.productos_seleccionados.clear()
        self.calcular_precio_total()
        
    def eliminar_articulo(self):
        item_seleccionado = self.tre.selection()
        if not item_seleccionado:
            messagebox.showerror("Error", "No ha seleccionado ningún artículo")
            return
        
        item_id = item_seleccionado[0]
        valores_item = self.tre.item(item_id)["values"]
        factura, cliente, articulo, precio, cantidad , total = valores_item
        
        self.tre.delete(item_id)
        
        self.productos_seleccionados = [producto for producto in self.productos_seleccionados if producto[2] != articulo]
        
        self.calcular_precio_total()
        
    def editar_articulo(self):
        selected_item = self.tre.selection()
        if not selected_item: 
            messagebox.showerror("Error", "No ha seleccionado ningún artículo")
            return
        
        item_values= self.tre.item(selected_item[0], 'values')
        if not item_values:
            return
        
        current_product = item_values[2]
        current_cantidad = item_values[4]
        
        new_cantidad = simpledialog.askinteger("Editar articulo", "ingrese la nueva cantidad: ", initialvalue=current_cantidad)
        
        if new_cantidad is not None:
            try:
                art = self.articulo_service.obtener_por_nombre(current_product)

                if art is None:
                    messagebox.showerror("Error", "Producto no encontrado")
                    return

                precio, costo, stock = art.precio, art.costo, art.stock

                if new_cantidad > stock:
                    messagebox.showerror("Error", f"No hay suficiente stock. Solo hay {stock} unidades disponibles")
                    return

                total = precio*new_cantidad
                total_cop = "{:,.0f}".format(total)
                self.tre.item(selected_item[0], values=(self.numero_factura, self.entry_cliente.get(), current_product, "{:,.0f}".format(precio),new_cantidad,total_cop))

                for idx, producto in enumerate(self.productos_seleccionados):
                    if producto[2] == current_product:
                        # Preservar el código si existe (tupla de longitud 8)
                        codigo_existente = producto[7] if len(producto) >= 8 else None
                        nuevo_item = (self.numero_factura, self.entry_cliente.get(), current_product, precio, new_cantidad, total_cop, costo)
                        if codigo_existente is not None:
                            nuevo_item = nuevo_item + (codigo_existente,)
                        self.productos_seleccionados[idx] = nuevo_item
                        break

                self.calcular_precio_total()
            except Exception as e:
                print("Error al editar el articulo: ", e)
                
    def ver_ventas_realizadas(self):
        try:
            ventas = self.venta_service.listar_reporte(self.sucursal)

            ventana_ventas = tk.Toplevel(self)
            ventana_ventas.title("Ventas realizadas")
            ventana_ventas.geometry("1100x700+120+20")
            ventana_ventas.config(bg="#c9dbe1")
            ventana_ventas.resizable(False, False)
            ventana_ventas.transient(self.master)
            ventana_ventas.grab_set()
            ventana_ventas.focus_set()
            ventana_ventas.lift()
            
            label_ventas_realizadas = tk.Label(ventana_ventas, text="Ventas realizadas", font="sans 26 bold", bg="#c9dbe1")
            label_ventas_realizadas.place(x=350, y=20)
            
            # Frame para el Treeview
            tree_frame = tk.Frame(ventana_ventas, bg="white")
            tree_frame.place(x=20, y=130, width=1060, height=450)
            
            scrol_y = ttk.Scrollbar(tree_frame)
            scrol_y.pack(side=RIGHT, fill=Y)
            
            scrol_x = ttk.Scrollbar(tree_frame, orient=HORIZONTAL)
            scrol_x.pack(side=BOTTOM, fill=X)
            tree = ttk.Treeview(tree_frame, columns=("Factura","Cliente","Producto","Precio","Cantidad","Total","Descuento","Fecha","Hora","forma","Sucursal","Banco","Efectivo","Transferencia"), show="headings")
            tree.pack(expand=True, fill=BOTH)
            
            scrol_y.config(command=tree.yview)
            scrol_x.config(command=tree.xview)
            
            tree.heading("Factura", text="Factura")
            tree.heading("Cliente", text="Cliente")
            tree.heading("Producto", text="Producto")
            tree.heading("Precio", text="Precio")
            tree.heading("Cantidad", text="Cantidad")
            tree.heading("Total", text="Total")
            tree.heading("Descuento", text="Descuento")
            tree.heading("Fecha", text="Fecha")
            tree.heading("Hora", text="Hora")
            tree.heading("forma", text="Forma de Pago")
            tree.heading("Sucursal", text="Sucursal")
            tree.heading("Banco", text="Banco")
            tree.heading("Efectivo", text="Efectivo")
            tree.heading("Transferencia", text="Transferencia")
            
            tree.column("Factura", width=60, anchor="center")
            tree.column("Cliente", width=120, anchor="center")
            tree.column("Producto", width=120, anchor="center")
            tree.column("Precio", width=80, anchor="center")
            tree.column("Cantidad", width=80, anchor="center")
            tree.column("Total", width=80, anchor="center")
            tree.column("Descuento", width=80, anchor="center")
            tree.column("Fecha", width=80, anchor="center")            
            tree.column("Hora", width=80, anchor="center")
            tree.column("forma", width=120, anchor="center")
            tree.column("Sucursal", width=120, anchor="center")
            tree.column("Banco", width=100, anchor="center")
            tree.column("Efectivo", width=100, anchor="center")
            tree.column("Transferencia", width=120, anchor="center")
            
            # Frame para mostrar los totales
            totales_frame = tk.Frame(ventana_ventas, bg="#c9dbe1")
            totales_frame.place(x=20, y=590, width=860, height=100)
            
            if self.sucursal:
                # Para usuarios normales, mostrar solo el total de su sucursal
                label_total_dia = tk.Label(totales_frame, 
                                         text=f"Total del día Sucursal {self.sucursal}: $0", 
                                         font="sans 16 bold", bg="#c9dbe1")
                label_total_dia.pack(pady=10)
            else:
                # Para administradores, mostrar totales por sucursal
                label_total_dia = tk.Label(totales_frame, 
                                         text="Totales del día por Sucursal:", 
                                         font="sans 16 bold", bg="#c9dbe1")
                label_total_dia.pack(pady=5)
                
                # Frame para los totales por sucursal
                totales_sucursales_frame = tk.Frame(totales_frame, bg="#c9dbe1")
                totales_sucursales_frame.pack(fill="x", pady=5)
                
                # Diccionario para almacenar los labels de totales por sucursal
                labels_totales = {}

            # Botón para ver factura
            def ver_factura():
                selected = tree.selection()
                if not selected:
                    messagebox.showerror("Error", "Por favor, seleccione una venta.")
                    return
                
                venta = tree.item(selected[0])['values']
                num_factura = venta[0]  # El número de factura está en la primera columna
                cliente = venta[1]      # El cliente está en la segunda columna
                try:
                    detalle = self.venta_service.obtener_detalle_factura(num_factura, cliente)
                    if detalle["productos"]:
                        self.generar_factura_pdf(
                            detalle["total"], cliente, num_factura, descuento=detalle["descuento"],
                            efectivo_pagado=detalle["efectivo"], transferencia_pagada=detalle["transferencia"],
                        )
                        messagebox.showinfo("Éxito", f"La factura {num_factura} ha sido regenerada.")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al regenerar la factura: {e}")

            btn_ver_factura = tk.Button(ventana_ventas, text="Ver factura", font="sans 14 bold", command=ver_factura)
            btn_ver_factura.place(x=900, y=600, width=180, height=40)

            filtro_frame = tk.Frame(ventana_ventas, bg="#c9dbe1")
            filtro_frame.place(x=20,y=60, width=1060, height=60)
            
            def obtener_desglose_pagos_por_factura(num_factura):
                try:
                    efec, trans = self.venta_service.obtener_desglose_pagos(num_factura)
                    efec_str = f"${efec:,.0f}" if efec > 0 else ""
                    trans_str = f"${trans:,.0f}" if trans > 0 else ""
                    return efec_str, trans_str
                except Exception:
                    return "", ""

            def filtrar_por_fecha(fecha_seleccionada=None):
                if fecha_seleccionada is None:
                    fecha_seleccionada = datetime.datetime.now().strftime("%Y-%m-%d")
                # Limpiar el árbol
                for item in tree.get_children():
                    tree.delete(item)
                # Filtrar ventas por fecha (solo comparar la parte de la fecha)
                ventas_dia = []
                for venta in ventas:
                    fecha_db = str(venta[7])
                    # Extraer solo la parte de la fecha (YYYY-MM-DD)
                    fecha_db_simple = fecha_db[:10]
                    if fecha_db_simple == fecha_seleccionada:
                        ventas_dia.append(venta)
                total_dia = 0
                for venta in ventas_dia:
                    try:
                        valores_mostrar = list(venta)
                        if isinstance(valores_mostrar[5], str):
                            valores_mostrar[5] = float(valores_mostrar[5].replace(",", "").replace(" ", ""))
                        valores_mostrar[5] = "{:,.0f}".format(valores_mostrar[5])
                        if isinstance(valores_mostrar[7], str):
                            try:
                                fecha_obj = datetime.datetime.strptime(valores_mostrar[7][:10], "%Y-%m-%d")
                                valores_mostrar[7] = fecha_obj.strftime("%d-%m-%Y")
                            except ValueError:
                                pass
                        # Asegurar que las columnas hasta Banco estén presentes
                        if len(valores_mostrar) < 12:
                            valores_mostrar += [""] * (12 - len(valores_mostrar))
                        # Agregar columnas Efectivo y Transferencia
                        try:
                            efc, trs = obtener_desglose_pagos_por_factura(valores_mostrar[0])
                        except Exception:
                            efc, trs = "", ""
                        valores_mostrar += [efc, trs]
                        tree.insert("", "end", values=valores_mostrar)
                        total_dia += float(valores_mostrar[5].replace(",", ""))
                    except (ValueError, TypeError) as e:
                        print(f"Error procesando venta: {venta}, Error: {e}")
                        continue
                fecha_mostrar = datetime.datetime.strptime(fecha_seleccionada, "%Y-%m-%d").strftime("%d-%m-%Y")
                label_total_dia.config(text=f"Total del día {fecha_mostrar}: ${total_dia:,.0f}")

            def mostrar_calendario():
                def seleccionar_fecha():
                    fecha_seleccionada = cal.selection_get()
                    fecha_actual = datetime.datetime.now().date()
                    if fecha_seleccionada > fecha_actual:
                        messagebox.showerror("Error", "No puede seleccionar una fecha futura")
                        return
                        
                    fecha_formato = fecha_seleccionada.strftime("%Y-%m-%d")
                    entry_fecha.delete(0, END)
                    entry_fecha.insert(0, fecha_seleccionada.strftime("%d-%m-%Y"))
                    ventana_cal.destroy()
                    filtrar_por_fecha(fecha_formato)
                
                ventana_cal = tk.Toplevel(ventana_ventas)
                ventana_cal.title("Seleccionar fecha")
                ventana_cal.geometry("300x250")
                
                cal = Calendar(ventana_cal, selectmode='day', date_pattern='yyyy-mm-dd')
                cal.pack(pady=20)
                
                btn_ok = tk.Button(ventana_cal, text="Seleccionar", command=seleccionar_fecha)
                btn_ok.pack()            
                
            def actualizar_totales(ventas_mostradas):
                if self.sucursal:
                    # Para usuarios normales, calcular solo el total de su sucursal
                    total_sucursal = sum(float(str(venta[5]).replace(",","")) for venta in ventas_mostradas)
                    fecha_mostrar = datetime.datetime.strptime(entry_fecha.get(), "%d-%m-%Y").strftime("%d-%m-%Y")
                    label_total_dia.config(text=f"Total del día {fecha_mostrar} - Sucursal {self.sucursal}: ${total_sucursal:,.0f}")
                else:
                    # Para administradores, calcular totales por sucursal
                    totales_por_sucursal = {}
                    for venta in ventas_mostradas:
                        sucursal = venta[9]  # sucursal está en el índice 9
                        total = float(str(venta[5]).replace(",",""))
                        totales_por_sucursal[sucursal] = totales_por_sucursal.get(sucursal, 0) + total
                        
                    # Actualizar o crear labels para cada sucursal
                    for sucursal, total in totales_por_sucursal.items():
                        if sucursal not in labels_totales:
                            labels_totales[sucursal] = tk.Label(totales_sucursales_frame, 
                                                        font="sans 14", bg="#c9dbe1")
                            labels_totales[sucursal].pack(anchor="w", padx=20)
                        labels_totales[sucursal].config(text=f"Sucursal {sucursal}: ${total:,.0f}")
                    
            def filtrar_ventas():
                try:
                    factura_a_buscar = entry_factura.get()
                    cliente_a_buscar = entry_cliente.get()
                    fecha_actual = datetime.datetime.strptime(entry_fecha.get(), "%d-%m-%Y").strftime("%Y-%m-%d")
                    for item in tree.get_children():
                        tree.delete(item)
                    ventas_filtradas = []
                    for venta in ventas:
                        fecha_db = str(venta[7])
                        fecha_db_simple = fecha_db[:10]
                        if (str(venta[0]) == factura_a_buscar or not factura_a_buscar) and \
                           (venta[1].lower() == cliente_a_buscar.lower() or not cliente_a_buscar) and \
                           (fecha_db_simple == fecha_actual):
                            ventas_filtradas.append(venta)
                    for venta in ventas_filtradas:
                        try:
                            valores_mostrar = list(venta)
                            if isinstance(valores_mostrar[5], str):
                                valores_mostrar[5] = float(valores_mostrar[5].replace(",", "").replace(" ", ""))
                            valores_mostrar[5] = "{:,.0f}".format(valores_mostrar[5])
                            if isinstance(valores_mostrar[7], str):
                                try:
                                    fecha_obj = datetime.datetime.strptime(valores_mostrar[7][:10], "%Y-%m-%d")
                                    valores_mostrar[7] = fecha_obj.strftime("%d-%m-%Y")
                                except ValueError:
                                    pass
                            # Asegurar que las columnas hasta Banco estén presentes
                            if len(valores_mostrar) < 12:
                                valores_mostrar += [""] * (12 - len(valores_mostrar))
                            # Agregar columnas Efectivo y Transferencia
                            try:
                                efc, trs = obtener_desglose_pagos_por_factura(valores_mostrar[0])
                            except Exception:
                                efc, trs = "", ""
                            valores_mostrar += [efc, trs]
                            tree.insert("", "end", values=valores_mostrar)
                        except (ValueError, TypeError) as e:
                            print(f"Error procesando venta filtrada: {venta}, Error: {e}")
                            actualizar_totales(ventas_filtradas)
                        except ValueError as e:
                            messagebox.showerror("Error", "Formato de fecha inválido. Use DD-MM-YYYY")
                            print(f"Error en filtro: {e}")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al filtrar ventas: {e}")
                    print(f"Error al filtrar ventas: {e}")

            # Controles de filtro
            label_fecha = tk.Label(filtro_frame, text="Fecha:", font="sans 14 bold", bg="#c9dbe1")
            label_fecha.place(x=10, y=15)
            
            entry_fecha = ttk.Entry(filtro_frame, font="sans 12", width=12)
            entry_fecha.place(x=80, y=15)
            entry_fecha.insert(0, datetime.datetime.now().strftime("%d-%m-%Y"))  
            
            btn_calendario = tk.Button(filtro_frame, text="📅", command=mostrar_calendario)
            btn_calendario.place(x=180, y=15)
            
            label_factura = tk.Label(filtro_frame, text="Factura:", font="sans 14 bold", bg= "#c9dbe1")
            label_factura.place(x=250, y=15)
            
            entry_factura = ttk.Entry(filtro_frame, font="sans 14 bold")
            entry_factura.place(x=340, y=10, width=200, height=40)
            
            label_cliente = tk.Label(filtro_frame, text="Cliente:", font="sans 14 bold", bg="#c9dbe1")
            label_cliente.place(x=560, y=15)
            
            entry_cliente = ttk.Entry(filtro_frame, font="sans 14 bold")
            entry_cliente.place(x=660, y=10, width=200, height=40)
            
            btn_filtrar = tk.Button(filtro_frame, text="Filtrar", font="sans 14 bold", command=filtrar_ventas)
            btn_filtrar.place(x=880, y=10, width=120, height=40)

            # Mostrar ventas del día actual por defecto
            filtrar_por_fecha()

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar las ventas: {e}")
            print(f"Error al cargar las ventas: {e}")
    
    def generar_factura_pdf(self, total_venta, cliente, num_factura=None, descuento=0, banco=None, efectivo_pagado=None, transferencia_pagada=None):
        try:
            if num_factura is None:
                num_factura = self.numero_factura
            # Usar ruta absoluta para el archivo PDF, anclada a la carpeta del proyecto (no al cwd)
            factura_path = rutas(f"facturas/factura_{num_factura}.pdf")
            os.makedirs(os.path.dirname(factura_path), exist_ok=True)

            # Obtener información de la empresa
            try:
                info_empresa = self.empresa_service.obtener()
                if info_empresa:
                    empresa_nombre = info_empresa.nombre
                    empresa_direccion = info_empresa.direccion
                    empresa_telefono = info_empresa.telefono
                    empresa_email = info_empresa.email
                    empresa_nit = info_empresa.nit if info_empresa.nit else "NIT no configurado"
                else:
                    empresa_nombre = "Empresa no configurada"
                    empresa_direccion = "Dirección no configurada"
                    empresa_telefono = "Teléfono no configurado"
                    empresa_email = "Email no configurado"
                    empresa_nit = "NIT no configurado"
            except Exception as e:
                print(f"Error al obtener información de la empresa: {e}")
                empresa_nombre = "Error al cargar datos"
                empresa_direccion = "Error al cargar datos"
                empresa_telefono = "Error al cargar datos"
                empresa_email = "Error al cargar datos"
                empresa_nit = "Error al cargar datos"

            # Cliente y método de pago
            try:
                metodo_result = self.venta_service.obtener_metodo_pago_banco(num_factura)
                metodo = metodo_result[0] if metodo_result and metodo_result[0] else "No especificado"
                banco_val = banco if banco else getattr(self, 'banco_pago', None) or (metodo_result[1] if metodo_result and len(metodo_result) > 1 else None)
            except Exception:
                metodo = "No especificado"
                banco_val = banco if banco else getattr(self, 'banco_pago', None)

            cliente_str = cliente if cliente else "No especificado"
            metodo_str = str(metodo).upper() if metodo else "NO ESPECIFICADO"

            # Obtener productos: de la base si es una factura existente, o del carrito actual
            if num_factura != self.numero_factura:
                try:
                    productos_factura = self.venta_service.listar_para_pdf(num_factura)
                except Exception:
                    productos_factura = []
            else:
                productos_factura = []
                for item in self.productos_seleccionados:
                    if len(item) < 6:
                        print(f"[ERROR] Item mal formado en productos_seleccionados para PDF: {item}")
                        continue
                    # item = (factura, cliente, producto, precio, cantidad, total_cop, costo)
                    productos_factura.append((item[2], item[4], item[3], item[5]))

            items_ticket = []
            for producto, cantidad, precio, total in productos_factura:
                if isinstance(precio, str):
                    precio = float(precio.replace(",", "").replace(" ", ""))
                if isinstance(total, str):
                    total = float(total.replace(",", "").replace(" ", ""))
                items_ticket.append((producto, cantidad, precio, total))

            encabezado = [
                f"Factura: {num_factura}",
                f"Fecha: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
                f"Cliente: {cliente_str}",
                f"Método de pago: {metodo_str}",
            ]
            if ("TRANSFERENCIA" in metodo_str) and banco_val:
                encabezado.append(f"Banco: {banco_val}")

            resumen = [(f"Total bruto: ${total_venta:,.0f}", False)]
            if descuento and descuento > 0:
                resumen.append((f"Descuento: -${descuento:,.0f}", False))
            total_neto = max(total_venta - descuento, 0)
            resumen.append((f"TOTAL A PAGAR: ${total_neto:,.0f}", True))
            if efectivo_pagado and efectivo_pagado > 0:
                resumen.append((f"Pago efectivo: ${efectivo_pagado:,.0f}", False))
            if transferencia_pagada and transferencia_pagada > 0:
                resumen.append((f"Pago transferencia: ${transferencia_pagada:,.0f}", False))

            empresa = {
                "nombre": empresa_nombre, "direccion": empresa_direccion,
                "telefono": empresa_telefono, "email": empresa_email, "nit": empresa_nit,
            }
            pie = [
                "¡Gracias por su compra!",
                "Los productos no tienen cambio ni devolución.",
                "Conserve este ticket para cualquier reclamo (30 días).",
            ]
            generar_ticket_pdf(factura_path, empresa, "FACTURA DE VENTA", encabezado, items_ticket, resumen, pie)

            # Imprimir o abrir el PDF
            if os.path.exists(factura_path):
                try:
                    respuesta = messagebox.askyesno("Imprimir", "¿Desea imprimir la factura ahora?")
                    if respuesta:
                        os.startfile(factura_path, "print")
                    else:
                        os.startfile(factura_path)
                    messagebox.showinfo("Éxito", f"La factura {num_factura} se ha generado correctamente")
                except Exception as e:
                    messagebox.showwarning("Aviso", f"No se pudo imprimir automáticamente. Por favor imprima manualmente.\nError: {e}")
                    os.startfile(factura_path)
            else:
                raise FileNotFoundError(f"No se encontró el archivo: {factura_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar la factura: {e}")
            print(f"Error al generar la factura: {e}") 
                
    def obtener_sucursal_usuario(self):
        if not self.username:
            return None
        try:
            usuario = self.usuario_service.obtener_por_username(self.username)
            if usuario:
                if usuario.rol.lower() in ["admin", "administrador"]:
                    return None  # Admin puede ver todas las sucursales
                return usuario.sucursal
            return None
        except Exception as e:
            print("Error al obtener sucursal del usuario:", e)
            return None

    def widgets(self):
        labelframe = tk.LabelFrame(self, font="sans 12 bold", bg="#c9dbe1")
        labelframe.place(x=25, y=30, width=1045, height=180)

        label_cliente = tk.Label(labelframe, text="Cliente:", font="sans 14 bold", bg="#c9dbe1")
        label_cliente.place(x=10, y=11)
        self.entry_cliente = ttk.Combobox(labelframe, font="sans 14 bold")
        self.entry_cliente.place(x=120, y=8, width=260, height=40)
        self.entry_cliente.bind('<KeyRelease>', self.filtrar_clientes)

        label_producto = tk.Label(labelframe, text="Producto:", font="sans 14 bold", bg="#c9dbe1")
        label_producto.place(x=10, y=70)
        self.entry_producto = ttk.Combobox(labelframe, font="sans 14 bold")
        self.entry_producto.place(x=120, y=66, width=260, height=40)
        self.entry_producto.bind('<KeyRelease>', self.filtrar_productos)
        # Manejar Enter (retorno) para lectores de código de barras que envían Enter al terminar
        self.entry_producto.bind('<Return>', self.on_producto_enter)
    # Permitir salir del combobox sin forzar selección: cancelar timers al perder foco
        self.entry_producto.bind('<FocusOut>', self._cancel_barcode_timers)

        label_cantidad = tk.Label(labelframe, text="Cantidad:", font="sans 14 bold", bg="#c9dbe1")
        label_cantidad.place(x=500, y=11)
        self.entry_cantidad = ttk.Entry(labelframe, font="sans 14 bold")
        self.entry_cantidad.place(x=610, y=8, width=100, height=40)

        self.label_stock = tk.Label(labelframe, text="Stock:", font="sans 14 bold", bg="#c9dbe1")
        self.label_stock.place(x=500, y=70)
        self.entry_producto.bind("<<ComboboxSelected>>", self.actualizar_stock)

        label_factura = tk.Label(labelframe, text=" Número de Factura", font="sans 14 bold", bg="#c9dbe1")
        label_factura.place(x=750, y=11)
        self.label_numero_factura = tk.Label(labelframe, text=f"{self.numero_factura}", font="sans 14 bold", bg="#c9dbe1")
        self.label_numero_factura.place(x=950, y=11)

        # Entry para descuento
        label_descuento = tk.Label(labelframe, text="Descuento:", font="sans 14 bold", bg="#c9dbe1")
        label_descuento.place(x=750, y=70)
        self.entry_descuento = ttk.Entry(labelframe, font="sans 14 bold")
        self.entry_descuento.place(x=870, y=70, width=100, height=40)
        self.entry_descuento.bind('<KeyRelease>', lambda e: self.calcular_precio_total())

        btn_agregar = tk.Button(labelframe, text="Agregar artículo", font="sans 14 bold", command=self.agregar_articulo)
        btn_agregar.place(x=90, y=120, width=200, height=40)

        btn_eliminar = tk.Button(labelframe, text="Eliminar artículo", font="sans 14 bold", command=self.eliminar_articulo)
        btn_eliminar.place(x=310, y=120, width=200, height=40)

        btn_editar = tk.Button(labelframe, text="Editar artículos", font="sans 14 bold", command=self.editar_articulo)
        btn_editar.place(x=530, y=120, width=200, height=40)

        btn_limpiar = tk.Button(labelframe, text="Limpiar lista", font="sans 14 bold", command=self.limpiar_lista)
        btn_limpiar.place(x=750, y=120, width=200, height=40)

        treFrame = tk.Frame(self, bg="white")
        treFrame.place(x=70, y=220, width=950, height=300)

        scrol_y = ttk.Scrollbar(treFrame)
        scrol_y.pack(side=RIGHT, fill=Y)

        scrol_x = ttk.Scrollbar(treFrame, orient=HORIZONTAL)
        scrol_x.pack(side=BOTTOM, fill=X)

        self.tre = ttk.Treeview(treFrame, yscrollcommand=scrol_y.set, xscrollcommand=scrol_x.set, height=40, columns=("Factura","Cliente","Producto","Precio","Cantidad","Total"), show="headings")
        self.tre.pack(expand=True, fill=BOTH)

        scrol_y.config(command=self.tre.yview)
        scrol_x.config(command=self.tre.xview)

        self.tre.heading("Factura", text="Factura")
        self.tre.heading("Cliente", text="Cliente")
        self.tre.heading("Producto", text="Producto")
        self.tre.heading("Precio", text="Precio")
        self.tre.heading("Cantidad", text="Cantidad")
        self.tre.heading("Total", text="Total")

        self.tre.column("Factura", width=60, anchor="center")
        self.tre.column("Cliente", width=120, anchor="center")
        self.tre.column("Producto", width=120, anchor="center")
        self.tre.column("Precio", width=80, anchor="center")
        self.tre.column("Cantidad", width=80, anchor="center")
        self.tre.column("Total", width=80, anchor="center")

        self.label_precio_total = tk.Label(self, text="Precio a pagar: $ 0", font="sans 18 bold", bg="#c9dbe1")
        self.label_precio_total.place(x=680, y=550)

        boton_pagar = tk.Button(self, text="Pagar", font="sans 14 bold", command=self.realizar_pago)
        boton_pagar.place(x=70, y=550, width=180, height=40)

        boton_ver_ventas = tk.Button(self, text="Ver ventas realizadas", font="sans 14 bold", command=self.ver_ventas_realizadas)
        boton_ver_ventas.place(x=290, y=550, width=210, height=40)
