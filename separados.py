import sqlite3
from tkinter import *
from tkcalendar import Calendar
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
import threading
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import sys
import os
from PIL import Image, ImageTk
from Smart_data_syncro.utils import rutas
import time

class Separados(tk.Frame):
    db_name = os.path.abspath('database.db')
    
    def __init__(self, padre,username=None):
        super().__init__(padre, bg="#c9dbe1")
        self.username = username
        self.sucursal = None  
        if self.username:
            self.sucursal = self.obtener_sucursal_usuario()
        self.numero_factura = self.obtener_numero_factura_actual()
        self.crear_tabla_abonos()  # <-- Add this line
        self.widgets()
        self.cargar_productos()
        self.cargar_clientes()
        self.productos_seleccionados = []
        self.timer_producto = None
        self.timer_cliente = None
        self.bind("<<ClienteActualizado>>", lambda e: self.cargar_clientes())

    def crear_tabla_abonos(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                c = conn.cursor()
                c.execute('''
                    CREATE TABLE IF NOT EXISTS abonos_separados (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        factura INTEGER,
                        fecha TEXT,
                        monto REAL,
                        metodo_pago TEXT,
                        banco TEXT,
                        sucursal TEXT
                    )
                ''')
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error creando tabla abonos_separados: {e}")

    def obtener_numero_factura_actual(self):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("SELECT MAX(CAST(factura AS INTEGER)) FROM (SELECT factura FROM ventas UNION ALL SELECT factura FROM separados)")
            max_factura = c.fetchone()[0]
            conn.close()
            return (max_factura or 0) + 1  # Siempre el máximo + 1, nunca se repite
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al obtener el número de factura actual: {e}")
            return 1

    def cargar_clientes(self):
        try:
            with sqlite3.connect(self.db_name) as conn:
                c = conn.cursor()
                c.execute("SELECT nombre FROM clientes")
                clientes = c.fetchall()
                self.clientes = [cliente[0] for cliente in clientes] # self.clientes ahora es una lista de strings
                self.entry_cliente["values"] = self.clientes
        except sqlite3.Error as e:
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
            data = self.clientes 
        else:
      
            data = [p for p in self.clientes if typed.lower() in p.lower()]
        
        self.entry_cliente['values'] = data if data else ['No se encontraron resultados']
        self.entry_cliente.event_generate('<Down>' )# Abre la lista desplegable
        if not data:
            self.entry_cliente.delete(0, tk.END) 

    def cargar_productos(self):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            # Si self.sucursal tiene valor, solo mostrar productos de esa sucursal
            if self.sucursal:
                c.execute("SELECT articulo, codigo FROM articulos WHERE sucursal = ?", (self.sucursal,))
            else:
                # Si es admin (self.sucursal es None), mostrar todos los productos
                c.execute("SELECT articulo, codigo FROM articulos")
            resultados = c.fetchall()
            conn.close()
            self.products = [{"nombre": r[0], "codigo": r[1]} for r in resultados]
            self.entry_producto["values"] = [p["nombre"] for p in self.products]
        except sqlite3.Error as e:
            print("Error al cargar los productos: ", e)

    def filtrar_productos(self, event):
        if hasattr(self, 'timer_producto') and self.timer_producto:
            self.timer_producto.cancel()
        self.timer_producto = threading.Timer(0.5, self._filter_products)
        self.timer_producto.start()
        
    def _filter_products(self):
        typed = self.entry_producto.get()
        if typed == '':
            data = [p["nombre"] for p in self.products]
        else:
            data = [
                p["nombre"] for p in self.products
                if typed.lower() in p["nombre"].lower() or (p["codigo"] and typed in str(p["codigo"]))
            ]
        self.entry_producto['values'] = data if data else ['No se encontraron resultados']
        self.entry_producto.event_generate('<Down>')
        if not data:
            self.entry_producto.delete(0, tk.END)

    def actualizar_stock(self, event=None):
        producto_seleccionado = self.entry_producto.get()

        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""
             SELECT stock FROM articulos 
                WHERE articulo = ? OR codigo = ?
            """, (producto_seleccionado, producto_seleccionado))
            resultado = c.fetchone()
            conn.close()
            if resultado:
                self.label_stock.config(text=f"Stock: {resultado[0]}")
            else:
                self.label_stock.config(text="Stock: No encontrado")
        except sqlite3.Error as e:
            print("Error al obtener el stock del producto", e)

    def agregar_articulo(self):
        self.numero_factura = self.obtener_numero_factura_actual()

        cliente = self.entry_cliente.get()
        producto = self.entry_producto.get()
        cantidad = self.entry_cantidad.get()
        
        if not cliente:
            messagebox.showerror("Error", "Por favor, seleccione un cliente.")
        
        if not producto:
            messagebox.showerror("Error", "Por favor, seleccione un producto.")
            
        if not cantidad.isdigit() or int(cantidad)<= 0:
            messagebox.showerror("Error", "Por favor, ingrese una cantidad válida.")
            return
        
        cantidad = int (cantidad)
        cliente= self.entry_cliente.get()
        
        try:
            conn = sqlite3.connect(self.db_name)
            c= conn.cursor()
            c.execute("SELECT precio, costo, stock From articulos WHERE articulo = ? ", (producto,))
            resultado = c.fetchone()
            
            if resultado is None:
                messagebox.showerror("Error", "El producto no existe.")
                return
            
            precio, costo , stock = resultado
            
            if cantidad > stock:
                messagebox.showerror("Error", f"No hay suficiente stock. Solo hay {stock} unidades disponibles.")

            total = cantidad * precio
            total_cop = "{:,.0f}".format(total)
            
            self.tre.insert("", "end", values = (self.numero_factura, cliente, producto,"{:,.0f}".format(precio),cantidad,total_cop))
            self.productos_seleccionados.append((self.numero_factura, cliente,producto,precio,cantidad,total_cop,costo))
            
            self.calcular_precio_total()
            conn.close ()
            self.entry_producto.set('')
            self.entry_cantidad.delete(0,'end')
        
        except sqlite3.Error as e:
            print("Error al agregar articulo: ", e)

    def calcular_precio_total(self):
        total_pagar = 0
        for item in self.tre.get_children():
            valores = self.tre.item(item)["values"]
            # El total está en la última columna (índice -1)
            try:
                total_item = float(str(valores[-1]).replace(" ", "").replace(",", ""))
                total_pagar += total_item
            except (ValueError, IndexError):
                continue
        self.label_precio_total.config(text=f"Precio a Pagar: $ {total_pagar:,.0f}")
       
    def eliminar_articulo(self):
        item_seleccionado = self.tre.selection()
        if not item_seleccionado:
            messagebox.showerror("Error", "No ha seleccionado ningún artículo.")
            return
        
        item_id = item_seleccionado[0]
        valores_item = self.tre.item(item_id)["values"]
        factura, cliente, articulo, precio, cantidad , total = valores_item
        
        self.tre.delete(item_id)
        
        self.productos_seleccionados = [producto for producto in self.productos_seleccionados if producto[2] != articulo]
        
        self.calcular_precio_total()

    def limpiar_lista(self):
        self.tre.delete(*self.tre.get_children())
        self.productos_seleccionados.clear()
        self.calcular_precio_total() 

    def editar_articulo(self):
        selected_item = self.tre.selection()
        if not selected_item: 
            messagebox.showerror("Error", "No ha seleccionado ningún artículo.")
            return
        
        item_values= self.tre.item(selected_item[0], 'values')
        if not item_values:
            return
        
        current_product = item_values[2]
        current_cantidad = item_values[4]
        
        new_cantidad = simpledialog.askinteger("Editar articulo", "ingrese la nueva cantidad: ", initialvalue=current_cantidad)
        
        if new_cantidad is not None:
            try:
                conn= sqlite3.connect(self.db_name)
                c = conn.cursor()
                c.execute ("SELECT precio,costo,stock FROM articulos WHERE articulo = ?", (current_product,))
                resultado = c.fetchone()
                
                if resultado is None:
                    messagebox.showerror("Error", "Producto no encontrado.")
                    
                precio,costo,stock = resultado
                
                if new_cantidad > stock:
                    messagebox.showerror("Error", f"No hay suficiente stock. Solo hay {stock} unidades disponibles.")
                    return
                
                total = precio*new_cantidad
                total_cop = "{:,.0f}".format(total)
                self.tre.item(selected_item[0], values=(self.numero_factura, self.entry_cliente.get(), current_product, "{:,.0f}".format(precio),new_cantidad,total_cop))

                for idx, producto in enumerate(self.productos_seleccionados):
                    if producto[2] == current_product:
                        self.productos_seleccionados[idx]= (self.numero_factura, self.entry_cliente.get(), current_product, precio,new_cantidad, total_cop, costo)
                        break
                    
                conn.close()
                
                self.calcular_precio_total()
            except sqlite3.Error as e:
                print("Error al editar el articulo: ", e)

    def obtener_sucursal_usuario(self):
        if not self.username:
            return None
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("SELECT sucursal, rol FROM usuarios WHERE username = ?", (self.username,))
            resultado = c.fetchone()
            conn.close()
            if resultado:
                sucursal, rol = resultado
                if rol and rol.lower() in ["admin", "administrador"]:
                    return None  # Admin puede ver todas las sucursales
                return sucursal
            else:
                return None
        except sqlite3.Error as e:
            print("Error al obtener la sucursal del usuario: ", e)
            return None

    def realizar_pago(self):
        if not self.tre.get_children():
            messagebox.showerror("Error", "No hay productos seleccionados para realizar el pago.")
            return
        # Calcular el total
        total_venta = sum(float(str(self.tre.item(item)["values"][-1]).replace(" ","").replace(",","")) for item in self.tre.get_children())
        total_formateado = "{:,.0f}".format(total_venta)
        ventana_abono = tk.Toplevel(self)
        ventana_abono.title("Abonar a Separado")
        ventana_abono.geometry("400x250+500+200")
        ventana_abono.config(bg="#c9dbe1")
        ventana_abono.resizable(False, False)
        ventana_abono.transient(self.master)
        ventana_abono.grab_set()
        ventana_abono.focus_set()
        ventana_abono.lift()
        
        tk.Label(ventana_abono, text="Abonar a Separado", font="sans 22 bold", bg="#c9dbe1").place(x=70, y=10)
        tk.Label(ventana_abono, text=f"Total a pagar: $ {total_formateado}", font="sans 14 bold", bg="#c9dbe1").place(x=80, y=60)
        tk.Label(ventana_abono, text="Monto a abonar:", font="sans 14 bold", bg="#c9dbe1").place(x=80, y=100)
       
        entry_abono = ttk.Entry(ventana_abono, font="sans 14 bold")
        entry_abono.place(x=210, y=120, width=100, height=30)
        label_error = tk.Label(ventana_abono, text="", font="sans 12", fg="red", bg="#c9dbe1")
        label_error.place(x=80, y=140)
        def continuar():
            try:
                abono = float(entry_abono.get())
            except ValueError:
                label_error.config(text="Ingrese un monto válido")
                return
            if abono <= 0 or abono > total_venta:
                label_error.config(text="El abono debe ser mayor que 0 y menor o igual al total.")
                return
            ventana_abono.destroy()
            self.mostrar_metodo_pago(total_venta, abono)
        btn_continuar = tk.Button(ventana_abono, text="Continuar", font="sans 14 bold", command=continuar)
        btn_continuar.place(x=140, y=210, width=120, height=40)

    def mostrar_metodo_pago(self, total_venta, abono):
        total_formateado = "{:,.0f}".format(total_venta)
        abono_formateado = "{:,.0f}".format(abono)
        deuda_restante = total_venta - abono
        deuda_formateada = "{:,.0f}".format(deuda_restante)
        ventana_pago = tk.Toplevel(self)
        ventana_pago.title("Realizar Separado")
        ventana_pago.geometry("400x500+450+80")
        ventana_pago.config(bg="#c9dbe1")
        ventana_pago.resizable(False,False)
        ventana_pago.transient(self.master)
        ventana_pago.grab_set()
        ventana_pago.focus_set()
        ventana_pago.lift()
        
        label_titulo = tk.Label(ventana_pago, text = "Realizar Separado", font ="sans 24 bold", bg="#c9dbe1")
        label_titulo.place(x=70, y=10)
        
        label_total = tk.Label(ventana_pago, text = f"Total: ${total_formateado}", font ="sans 14 bold", bg="#c9dbe1")
        label_total.place(x=80, y=60)
        
        label_abono = tk.Label(ventana_pago, text = f"Abono: ${abono_formateado}", font ="sans 14 bold", bg="#c9dbe1")
        label_abono.place(x=80, y=90)

        label_deuda = tk.Label(ventana_pago, text = f"Deuda restante: $ {deuda_formateada}", font ="sans 14 bold", bg="#c9dbe1")
        label_deuda.place(x=80, y=120)
        
        metodo_frame = tk.LabelFrame(ventana_pago, text="Método de Pago", font="sans 14 bold", bg="#c9dbe1")
        metodo_frame.place(x=50, y=170, width=300, height=100)
        
        metodo_pago = tk.StringVar(value="efectivo")
        
        rb_efectivo = tk.Radiobutton(metodo_frame, text="Efectivo", font="sans 12", variable=metodo_pago, value="efectivo", bg="#c9dbe1")
        rb_efectivo.place(x=20, y=10)
        
        rb_transferencia = tk.Radiobutton(metodo_frame, text="Transferencia", font="sans 12", variable=metodo_pago, value="transferencia", bg="#c9dbe1")
        rb_transferencia.place(x=20, y=40)
        
        # Frame para seleccionar banco (solo visible si transferencia)
        banco_frame = tk.Frame(ventana_pago, bg="#c9dbe1")
        banco_opcion = tk.StringVar(value="Bancolombia")
        def mostrar_bancos(*args):
            if metodo_pago.get() == "transferencia":
                banco_frame.place(x=50, y=280, width=300, height=60)
            else:
                banco_frame.place_forget()
        metodo_pago.trace_add('write', mostrar_bancos)
        
        tk.Label(banco_frame, text="Banco:", font="sans 14 bold", bg="#c9dbe1").place(x=10, y=5)
        
        rb_bancolombia = tk.Radiobutton(banco_frame, text="Bancolombia", font="sans 12", variable=banco_opcion, value="Bancolombia", bg="#c9dbe1")
        rb_bancolombia.place(x=100, y=5)
        
        rb_daviplata = tk.Radiobutton(banco_frame, text="Daviplata", font="sans 12", variable=banco_opcion, value="Daviplata", bg="#c9dbe1")
        rb_daviplata.place(x=100, y=30)
        
        def confirmar_pago():
            banco = banco_opcion.get() if metodo_pago.get() == "transferencia" else None
            self.procesar_pago(abono, ventana_pago, total_venta, metodo_pago.get(), banco)
        btn_confirmar = tk.Button(ventana_pago, text="Confirmar pago", font="sans 14 bold", command=confirmar_pago)
        btn_confirmar.place(x=120, y=380, width=160, height=40)
        
    def procesar_pago(self, abono, ventana_pago, total_venta, metodo_pago, banco=None):
        # Registrar el separado en la base de datos
        try:
            self.numero_factura = self.obtener_numero_factura_actual()
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
            fecha_alerta = (datetime.datetime.now() + datetime.timedelta(days=61)).strftime("%Y-%m-%d")
            estado_deuda = "pendiente" if total_venta - abono > 0 else "pagado"
            deuda_restante = total_venta - abono
            alerta_mostrada = 0
            sucursal = self.sucursal if self.sucursal else None
            for item in self.productos_seleccionados:
                factura, cliente, producto, precio, cantidad, total, costo = item
                # Descontar stock: actualizar sólo una fila que coincida (evita decrementar todos los artículos con mismo nombre)
                try:
                    c.execute("SELECT id FROM articulos WHERE articulo = ? LIMIT 1", (producto,))
                    f_id = c.fetchone()
                    if f_id:
                        art_id = f_id[0]
                        c.execute("UPDATE articulos SET stock = stock - ? WHERE id = ?", (cantidad, art_id))
                    else:
                        c.execute("UPDATE articulos SET stock = stock - ? WHERE articulo = ?", (cantidad, producto))
                except Exception:
                    c.execute("UPDATE articulos SET stock = stock - ? WHERE articulo = ?", (cantidad, producto))
                # Registrar separado
                c.execute("""
                    INSERT INTO separados (factura, cliente, producto, precio, cantidad, total, abono, deuda_restante, estado_deuda, fecha_separado, fecha_alerta, alerta_mostrada, sucursal, metodo_pago, banco)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.numero_factura, cliente, producto, precio, cantidad, total, abono, deuda_restante, estado_deuda, fecha_actual, fecha_alerta, alerta_mostrada, sucursal, metodo_pago, banco
                ))
            conn.commit()
            # Obtener el número de factura real insertado
            c.execute("SELECT factura FROM separados ORDER BY ROWID DESC LIMIT 1")
            factura_real = c.fetchone()[0]
            self.generar_factura_separado(factura_real, self.productos_seleccionados, cliente, total_venta, metodo_pago, banco)
            conn.close()
            messagebox.showinfo("Separado registrado", "El separado se ha registrado correctamente.")
            self.numero_factura = self.obtener_numero_factura_actual()
            self.label_numero_factura.config(text=str(self.numero_factura))
            self.productos_seleccionados = []
            self.limpiar_lista()
            ventana_pago.destroy()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al registrar el separado: {e}")
            if conn:
                conn.close()
   
    def generar_factura_separado(self, num_factura, productos, cliente, total_venta, metodo_pago, banco):
        # Genera una factura PDF diferenciada para separados
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            import os
            nombre_archivo = f"facturas/factura_separado_{num_factura}.pdf"            
            c = canvas.Canvas(nombre_archivo, pagesize=letter)
            
            # Obtener información de la empresa desde la base de datos
            try:
                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("SELECT nombre, direccion, telefono, email FROM empresa WHERE id = 1")
                info_empresa = cursor.fetchone()
                conn.close()
                
                if info_empresa:
                    empresa_nombre = info_empresa[0]
                    empresa_direccion = info_empresa[1]
                    empresa_telefono = info_empresa[2]
                    empresa_email = info_empresa[3]
                else:
                    empresa_nombre = "Empresa no configurada"
                    empresa_direccion = "Dirección no configurada"
                    empresa_telefono = "Teléfono no configurado"
                    empresa_email = "Email no configurado"
            except sqlite3.Error as e:
                print(f"Error al obtener información de la empresa: {e}")
                empresa_nombre = "Error al cargar datos"
                empresa_direccion = "Error al cargar datos"
                empresa_telefono = "Error al cargar datos"
                empresa_email = "Error al cargar datos"
            
            # Encabezado con información de la empresa
            c.setFont("Helvetica-Bold", 30)
            c.drawString(50, 780, empresa_nombre)
            c.setFont("Helvetica", 12)
            c.drawString(50, 760, f"Dirección: {empresa_direccion}")
            c.drawString(50, 740, f"Teléfono: {empresa_telefono}")
            c.drawString(50, 720, f"Email: {empresa_email}")
            
            # Información del separado
            c.setFont("Helvetica-Bold", 24)
            c.drawString(50, 690, "Factura de Separado")
            c.setFont("Helvetica", 20)
            c.drawString(50, 670, f"Factura N°: {num_factura}")
            c.drawString(250, 670, f"Fecha: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
            c.drawString(50, 650, f"Cliente: {cliente}")
            c.drawString(50, 630, f"Método de pago: {metodo_pago}{' - ' + banco if banco else ''}")
            # Consultar total abonado y deuda restante SIEMPRE desde la base de datos
            total_venta = 0
            total_abonado = 0
            deuda_restante = 0
            try:
                conn = sqlite3.connect(self.db_name)
                cur = conn.cursor()
                # Usar num_factura como número de factura en las consultas
                factura = num_factura
                cur.execute("SELECT producto, cantidad, precio, total FROM separados WHERE factura = ?", (factura,))
                productos_factura = cur.fetchall()
                # Sumar el total de todos los productos de la factura
                cur.execute("SELECT total FROM separados WHERE factura = ?", (factura,))
                totales = cur.fetchall()
                total_venta = sum(float(str(t[0]).replace(",", "").replace(" ", "")) for t in totales)
                # Tomar el abono inicial solo de UNA fila (la primera de la factura)
                cur.execute("SELECT abono FROM separados WHERE factura = ? LIMIT 1", (factura,))
                row = cur.fetchone()
                abono_actual = row[0] if row else 0
                # Sumar abonos adicionales
                cur.execute("SELECT SUM(monto) FROM abonos_separados WHERE factura = ?", (factura,))
                abonos_adicionales = cur.fetchone()[0] or 0
                total_abonado = abono_actual + abonos_adicionales
                deuda_restante = total_venta - total_abonado
                # Obtener la deuda_restante real de la base de datos (como en la vista de separados realizados)
                cur.execute("SELECT deuda_restante FROM separados WHERE factura = ? LIMIT 1", (factura,))
                row_deuda = cur.fetchone()
                deuda_restante = float(row_deuda[0]) if row_deuda and row_deuda[0] is not None else deuda_restante
                # Obtener datos de la empresa
                cur.execute("SELECT nombre, direccion, telefono, email FROM empresa WHERE id = 1")
                info_empresa = cur.fetchone()
                if info_empresa:
                    empresa_nombre = info_empresa[0]
                    empresa_direccion = info_empresa[1]
                    empresa_telefono = info_empresa[2]
                    empresa_email = info_empresa[3]
                else:
                    empresa_nombre = "Empresa no configurada"
                    empresa_direccion = "Dirección no configurada"
                    empresa_telefono = "Teléfono no configurado"
                    empresa_email = "Email no configurado"
                conn.close()
            except Exception as e:
                productos_factura = []
            c.drawString(50, 670, f"Total venta: ${total_venta:,.0f}")
            c.drawString(50, 650, f"Total abonado: ${total_abonado:,.0f}")
            c.drawString(50, 630, f"Deuda restante: ${deuda_restante:,.0f}")
            c.drawString(50, 610, "Detalle de productos:")
            y = 590
            c.setFont("Helvetica-Bold", 20)
            c.drawString(50, y, "Producto")
            c.drawString(200, y, "Cantidad")
            c.drawString(300, y, "Precio")
            c.drawString(400, y, "Total")
            c.setFont("Helvetica", 10)
            y -= 30
            for prod, cant, precio, total in productos_factura:
                c.drawString(50, y, str(prod))
                c.drawString(200, y, str(cant))
                try:
                    precio_float = float(str(precio).replace(",", "").replace(" ", ""))
                except Exception:
                    precio_float = 0
                try:
                    total_float = float(str(total).replace(",", "").replace(" ", ""))
                except Exception:
                    total_float = 0
                c.drawString(300, y, f"${precio_float:,.0f}")
                c.drawString(400, y, f"${total_float:,.0f}")
                y -= 20
                if y < 100:
                    c.showPage()
                    y = 700
            # Al final del detalle de productos, mostrar el total bruto y total a pagar
            if y < 100:
                c.showPage()
                y = 700
            y -= 20
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, f"Total bruto: ${total_venta:,.0f}")
            y -= 25
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, f"Total a pagar: ${(deuda_restante + total_abonado):,.0f}")
            c.save()
        except Exception as e:
            print(f"Error generando factura de separado: {e}")
    
    def widgets(self):
        labelframe = tk.LabelFrame(self, font="sans 12 bold", bg="#c9dbe1")
        labelframe.place(x=25, y = 30, width = 1045,height = 180)
        
        label_cliente = tk.Label(labelframe, text="Cliente:", font="sans 14 bold", bg="#c9dbe1")
        label_cliente.place(x=10, y = 11)

        self.entry_cliente = ttk.Combobox(labelframe, font="sans 14 bold")
        self.entry_cliente.place(x=120, y = 8, width = 260, height = 40)
        self.entry_cliente.bind('<KeyRelease>', self.filtrar_clientes)
       
        label_producto = tk.Label(labelframe, text="Producto:", font="sans 14 bold", bg="#c9dbe1")
        label_producto.place(x=10, y = 70)
        self.entry_producto = ttk.Combobox(labelframe, font="sans 14 bold")
        self.entry_producto.place(x=120, y = 66, width = 260, height = 40)
        self.entry_producto.bind('<KeyRelease>', self.filtrar_productos)
       
        label_cantidad = tk.Label(labelframe, text="Cantidad:", font="sans 14 bold", bg="#c9dbe1")
        label_cantidad.place(x=500,y=11)
        self.entry_cantidad = ttk.Entry(labelframe, font="sans 14 bold")
        self.entry_cantidad.place(x=610, y=8,width=100,height=40)      
       
        self.label_stock = tk.Label(labelframe, text="Stock:", font="sans 14 bold", bg="#c9dbe1")
        self.label_stock.place(x=500,y=70)
        self.entry_producto.bind("<<ComboboxSelected>>", self.actualizar_stock)
       
        label_factura = tk.Label(labelframe, text=" Numero de Factura", font="sans 14 bold", bg= "#c9dbe1") 
        label_factura.place(x=750, y = 11)
        self.label_numero_factura = tk.Label(labelframe, text=f"{self.numero_factura}", font= "sans 14 bold", bg= "#c9dbe1")
        self.label_numero_factura.place(x=950, y=11)
    
        btn_agregar = tk.Button(labelframe,text="Agregar Articulo", font="sans 14 bold", command=self.agregar_articulo)
        btn_agregar.place(x=90,y=120, width=200, height=40)
       
        btn_eliminar = tk.Button(labelframe,text="Eliminar Articulo", font="sans 14 bold",command=self.eliminar_articulo)
        btn_eliminar.place(x=310,y=120, width=200, height=40)
       
        btn_editar = tk.Button(labelframe,text="Editar articulos", font="sans 14 bold", command=self.editar_articulo)
        btn_editar.place(x=530,y=120, width=200, height=40)
       
        btn_limpiar = tk.Button(labelframe,text="Limpiar lista", font="sans 14 bold", command=self.limpiar_lista)
        btn_limpiar.place(x=750,y=120, width=200, height=40)
       
        treFrame = tk.Frame(self, bg="#c9dbe1")  # Cambiar fondo aquí también
        treFrame.place(x=70, y=220 , width=950,height=300) 
       
        scrol_y = ttk.Scrollbar(treFrame)
        scrol_y.pack(side=RIGHT, fill=Y)
       
        # Empaquetar el Scrollbar horizontal justo debajo del Treeview
        scrollx = ttk.Scrollbar(treFrame , orient=HORIZONTAL)
        scrollx.pack(side=TOP, fill=X)
       
        self.tre = ttk.Treeview(treFrame, yscrollcommand=scrol_y.set, xscrollcommand=scrollx.set, height=40, columns=("Factura","Cliente","Producto","Precio","Cantidad","Total"), show="headings")
        self.tre.pack(side=LEFT, fill=BOTH, expand=True)
       
        scrol_y.config(command=self.tre.yview)
        scrollx.config(command=self.tre.xview)
       
        self.tre.heading("Factura", text="Factura")
        self.tre.heading("Cliente", text="Cliente")
        self.tre.heading("Producto", text="Producto")
        self.tre.heading("Precio", text="Precio")
        self.tre.heading("Cantidad", text="Cantidad")
        self.tre.heading("Total", text="Total")
       
        self.tre.column("Factura",width=60, anchor="center")
        self.tre.column("Cliente",width=120, anchor="center")
        self.tre.column("Producto",width=120, anchor="center")
        self.tre.column("Precio",width=80, anchor="center")
        self.tre.column("Cantidad",width=80, anchor="center")
        self.tre.column("Total",width=80, anchor="center")

        self.label_precio_total =tk.Label(self, text="Precio a Pagar: $ 0",font="sans 18 bold", bg="#c9dbe1")
        self.label_precio_total.place(x=680, y=550)
       
       
        boton_separar = tk.Button(self, text="Separar", font=" sans 14 bold", command=self.realizar_pago)
        boton_separar.place(x=70, y=550, width=180, height=40)
       
        boton_ver_separados = tk.Button(self, text="Ver separados", font=" sans 14 bold", command=self.ver_separados_realizados)
        boton_ver_separados.place(x=290, y=550, width=210, height=40)

    def ver_separados_realizados(self):
        # Alerta de separados vencidos con detalle
        try:
            import datetime
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            hoy = datetime.datetime.now().strftime("%Y-%m-%d")
            c.execute("""
                SELECT factura, cliente, fecha_alerta FROM separados
                WHERE estado_deuda = 'pendiente' AND fecha_alerta <= ?
            """, (hoy,))
            vencidos = c.fetchall()
            conn.close()
            if vencidos:
                mensaje = "Separados vencidos (más de 60 días):\n\n"
                for factura, cliente, fecha_alerta in vencidos:
                    mensaje += f"Factura: {factura} | Cliente: {cliente} | Fecha alerta: {fecha_alerta}\n"
                messagebox.showwarning("Separados vencidos", mensaje)
        except Exception as e:
            print("Error al verificar separados vencidos:", e)
        # Ventana para mostrar separados y permitir abonos adicionales
        ventana = tk.Toplevel(self)
        ventana.title("Separados Realizados")
        ventana.geometry("1100x600+120+60")
        ventana.config(bg="#c9dbe1")
        label = tk.Label(ventana, text="Separados Realizados", font="sans 22 bold", bg="#c9dbe1")
        label.pack(pady=10)

        filtro_frame = tk.Frame(ventana, bg="#c9dbe1")
        filtro_frame.pack(pady=(0, 10))
        
        tk.Label(filtro_frame, text="Factura:", font="sans 14 bold", bg="#c9dbe1").pack(side=tk.LEFT, padx=(10, 2))
        
        entry_factura = ttk.Entry(filtro_frame, font="sans 14 bold", width=10)
        
        entry_factura.pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(filtro_frame, text="Cliente:", font="sans 14 bold", bg="#c9dbe1").pack(side=tk.LEFT, padx=(10, 2))
        
        entry_cliente = ttk.Entry(filtro_frame, font="sans 14 bold", width=20)
        entry_cliente.pack(side=tk.LEFT, padx=(0, 20))
        
        btn_filtrar = tk.Button(filtro_frame, text="Filtrar", font="sans 14 bold")
        btn_filtrar.pack(side=tk.LEFT, padx=10)

        frame = tk.Frame(ventana, bg="#c9dbe1")
        frame.pack(fill=BOTH, expand=True, padx=20, pady=10)

        columns = ("Factura", "Cliente", "Producto", "Total", "Abono", "Deuda", "Método", "Banco", "Estado", "Fecha", "Fecha Alerta")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=18)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=100)
        # Empaquetar el Scrollbar horizontal justo debajo del Treeview
        scrollx = ttk.Scrollbar(frame, orient=HORIZONTAL, command=tree.xview)
        scrollx.pack(side=TOP, fill=X)
        tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrolly = ttk.Scrollbar(frame, orient=VERTICAL, command=tree.yview)
        scrolly.pack(side=RIGHT, fill=Y)
        tree.configure(yscrollcommand=scrolly.set, xscrollcommand=scrollx.set)

        def cargar_separados(factura_filtro=None, cliente_filtro=None):
            for item in tree.get_children():
                tree.delete(item)
            try:
                import datetime
                conn = sqlite3.connect(self.db_name)
                c = conn.cursor()
                hoy = datetime.datetime.now().strftime("%Y-%m-%d")
                query = """
                    SELECT factura, cliente, producto, total, abono, deuda_restante, metodo_pago, banco, estado_deuda, fecha_separado, fecha_alerta
                    FROM separados
                    WHERE estado_deuda != 'pagado'
                """
                params = []
                # Si el usuario NO es admin, filtra por sucursal
                if self.sucursal:
                    query += " AND (sucursal = ? OR sucursal IS NULL)"
                    params.append(self.sucursal)
                if factura_filtro:
                    query += " AND factura = ?"
                    params.append(factura_filtro)
                if cliente_filtro:
                    query += " AND cliente LIKE ?"
                    params.append(f"%{cliente_filtro}%")
                query += " ORDER BY fecha_separado DESC"
                c.execute(query, params)
                rows = c.fetchall()
                for row in rows:
                    # row[10] es fecha_alerta
                    values = row[:11]  # Incluye hasta fecha_alerta
                    if len(row) > 10 and row[10] and row[10] <= hoy:
                        tree.insert("", "end", values=values, tags=("vencido",))
                    else:
                        tree.insert("", "end", values=values)
                tree.tag_configure("vencido", background="#ffcccc")
                conn.close()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al cargar separados: {e}")

        def filtrar():
            factura_val = entry_factura.get().strip()
            cliente_val = entry_cliente.get().strip()
            factura_filtro = factura_val if factura_val else None
            cliente_filtro = cliente_val if cliente_val else None
            cargar_separados(factura_filtro, cliente_filtro)

        btn_filtrar.config(command=filtrar)
        cargar_separados()

        # Botón para ver historial de abonos y abonar
        btn_historial = tk.Button(ventana, text="Ver Historial / Abonar", font="sans 14 bold", command=lambda: self.abrir_historial_abonos(tree))
        btn_historial.pack(pady=10, side=tk.LEFT, anchor="w")

        # Botón para borrar separado
        btn_borrar = tk.Button(ventana, text="Borrar Separado", font="sans 14 bold", bg="#ff6b6b", fg="white", command=lambda: self.borrar_separado(tree))
        btn_borrar.pack(pady=10, side=tk.LEFT, anchor="w", padx=(10, 0))

        def ver_factura_separado():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Seleccione un separado para ver la factura.")
                return
            values = tree.item(selected[0], "values")
            factura = values[0] if values else None
            if not factura:
                messagebox.showerror("Error", "No se pudo determinar el número de factura.")
                return
            cliente = values[1]
            # Obtener todos los productos de ese separado
            try:
                conn = sqlite3.connect(self.db_name)
                c = conn.cursor()
                c.execute("SELECT producto, cantidad, precio, total FROM separados WHERE factura = ?", (factura,))
                productos = c.fetchall()
                # Sumar el total de todos los productos de la factura
                c.execute("SELECT total FROM separados WHERE factura = ?", (factura,))
                totales = c.fetchall()
                total_venta = sum(float(str(t[0]).replace(",", "").replace(" ", "")) for t in totales)
                # Tomar el abono inicial solo de UNA fila (la primera de la factura)
                c.execute("SELECT abono FROM separados WHERE factura = ? LIMIT 1", (factura,))
                row = c.fetchone()
                abono_actual = row[0] if row else 0
                # Sumar abonos adicionales
                c.execute("SELECT SUM(monto) FROM abonos_separados WHERE factura = ?", (factura,))
                abonos_adicionales = c.fetchone()[0] or 0
                total_abonado = abono_actual + abonos_adicionales
                deuda_restante = total_venta - total_abonado
                # Obtener la deuda_restante real de la base de datos (como en la vista de separados realizados)
                c.execute("SELECT deuda_restante FROM separados WHERE factura = ? LIMIT 1", (factura,))
                row_deuda = c.fetchone()
                deuda_restante = float(row_deuda[0]) if row_deuda and row_deuda[0] is not None else deuda_restante
                # Obtener datos de la empresa
                c.execute("SELECT nombre, direccion, telefono, email FROM empresa WHERE id = 1")
                info_empresa = c.fetchone()
                if info_empresa:
                    empresa_nombre = info_empresa[0]
                    empresa_direccion = info_empresa[1]
                    empresa_telefono = info_empresa[2]
                    empresa_email = info_empresa[3]
                else:
                    empresa_nombre = "Empresa no configurada"
                    empresa_direccion = "Dirección no configurada"
                    empresa_telefono = "Teléfono no configurado"
                    empresa_email = "Email no configurado"
                conn.close()
            except Exception as e:
                messagebox.showerror("Error", f"Error al consultar productos/abonos/empresa: {e}")
                return
            metodo = values[6] if len(values) > 6 and values[6] else "No especificado"
            banco = values[7] if len(values) > 7 and values[7] else None
            if not metodo or metodo == "No especificado":
                try:
                    conn = sqlite3.connect(self.db_name)
                    c = conn.cursor()
                    c.execute("SELECT metodo_pago, banco FROM separados WHERE factura = ? LIMIT 1", (factura,))
                    row = c.fetchone()
                    if row:
                        metodo = row[0] if row[0] else "No especificado"
                        banco = row[1] if row[1] else None
                    conn.close()
                except Exception:
                    metodo = "No especificado"
                    banco = None
            # Generar PDF en carpeta facturasSeparados con el número de factura correcto
            carpeta_facturas = "facturasSeparados"
            abs_carpeta = os.path.abspath(carpeta_facturas)
            if not os.path.exists(abs_carpeta):
                try:
                    os.makedirs(abs_carpeta)
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo crear la carpeta de facturas: {e}")
                    return
            nombre_archivo = os.path.join(abs_carpeta, f"factura_separado_{factura}.pdf")
            # Eliminar el archivo anterior si existe para forzar la regeneración
            if os.path.exists(nombre_archivo):
                try:
                    os.remove(nombre_archivo)
                except Exception as e:
                    messagebox.showwarning("Aviso", f"No se pudo eliminar el PDF anterior: {e}")
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                cpdf = canvas.Canvas(nombre_archivo, pagesize=letter)
                # Encabezado empresa
                cpdf.setFont("Helvetica-Bold", 28)
                cpdf.drawString(50, 770, empresa_nombre)
                cpdf.setFont("Helvetica", 18)
                cpdf.drawString(50, 745, f"Dirección: {empresa_direccion}")
                cpdf.drawString(50, 725, f"Teléfono: {empresa_telefono}")
                cpdf.drawString(50, 705, f"Email: {empresa_email}")
                # Título y datos de la factura
                cpdf.setFont("Helvetica-Bold", 26)
                cpdf.drawString(50, 670, "Factura de Separado")
                cpdf.setFont("Helvetica", 20)
                cpdf.drawString(50, 640, f"Factura N°: {factura}")
                cpdf.drawString(350, 640, f"Fecha: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
                cpdf.drawString(50, 610, f"Cliente: {cliente}")
                cpdf.drawString(50, 580, f"Método de pago: {metodo}{' - ' + banco if banco else ''}")
                cpdf.drawString(50, 550, f"Total venta: ${total_venta:,.0f}")
                cpdf.drawString(50, 520, f"Total abonado: ${abono_actual:,.0f}")
                cpdf.drawString(50, 490, f"Deuda restante: ${deuda_restante:,.0f}")
                cpdf.setFont("Helvetica-Bold", 18)
                cpdf.drawString(50, 460, "Detalle de productos:")
                y = 430
                cpdf.setFont("Helvetica-Bold", 16)
                cpdf.drawString(50, y, "Producto")
                cpdf.drawString(200, y, "Cantidad")
                cpdf.drawString(300, y, "Precio")
                cpdf.drawString(400, y, "Total")
                cpdf.setFont("Helvetica", 16)
                y -= 30
                for prod, cant, precio, total in productos:
                    cpdf.drawString(50, y, str(prod))
                    cpdf.drawString(200, y, str(cant))
                    try:
                        precio_float = float(str(precio).replace(",", "").replace(" ", ""))
                    except Exception:
                        precio_float = 0
                    try:
                        total_float = float(str(total).replace(",", "").replace(" ", ""))
                    except Exception:
                        total_float = 0
                    cpdf.drawString(300, y, f"${precio_float:,.0f}")
                    cpdf.drawString(400, y, f"${total_float:,.0f}")
                    y -= 25
                    if y < 100:
                        cpdf.showPage()
                        y = 700
                # Al final del detalle de productos, mostrar el total bruto y total a pagar
                if y < 100:
                    cpdf.showPage()
                    y = 700
                y -= 20
                cpdf.setFont("Helvetica-Bold", 14)
                cpdf.drawString(50, y, f"Total bruto: ${total_venta:,.0f}")
                y -= 25
                cpdf.save()
                time.sleep(0.2)  
            except Exception as e:
                messagebox.showerror("Error", f"Error generando la factura PDF: {e}")
                return
            # Preguntar si desea imprimir
            if os.path.exists(nombre_archivo):
                try:
                    respuesta = messagebox.askyesno("Imprimir", "¿Desea imprimir la factura ahora?")
                    if respuesta:
                        os.startfile(nombre_archivo, "print")
                    else:
                        os.startfile(nombre_archivo)
                    messagebox.showinfo("Éxito", f"La factura {factura} se ha generado correctamente\nRuta: {nombre_archivo}")
                except Exception as e:
                    messagebox.showwarning("Aviso", f"No se pudo imprimir automáticamente. Por favor imprima manualmente.\nError: {e}\nRuta: {nombre_archivo}")
                    try:
                        os.startfile(nombre_archivo)
                    except Exception as e2:
                        messagebox.showerror("Error", f"No se pudo abrir la factura generada.\nError: {e2}\nRuta: {nombre_archivo}")
            else:
                messagebox.showerror("Error", f"No se encontró el archivo: {nombre_archivo}")
        btn_ver_factura = tk.Button(ventana, text="Ver Factura", font="sans 14 bold", command=ver_factura_separado)
        btn_ver_factura.pack(pady=10, side=tk.RIGHT, anchor="e", padx=20)

    def abrir_historial_abonos(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Seleccione un separado para ver el historial o abonar.")
            return
        values = tree.item(selected[0], "values")
        factura = values[0]
        cliente = values[1]
        producto = values[2]
        deuda_restante = float(values[5])

        ventana = tk.Toplevel(self)
        ventana.title(f"Historial de abonos - Factura {factura}")
        ventana.geometry("600x400+300+120")
        ventana.config(bg="#c9dbe1")
        tk.Label(ventana, text=f"Historial de abonos para {cliente} - {producto}", font="sans 16 bold", bg="#c9dbe1").pack(pady=10)

        # Mostrar resumen del abono inicial (si existe)
        frame_resumen = tk.Frame(ventana, bg="#c9dbe1")
        frame_resumen.pack(pady=(0, 5), fill=X)
        lbl_abono_inicial = tk.Label(frame_resumen, text="", font="sans 12 bold", bg="#c9dbe1", fg="#1a73e8")
        lbl_abono_inicial.pack(side=LEFT, padx=10)

        columns = ("Fecha", "Monto", "Método", "Banco")
        tree_abonos = ttk.Treeview(ventana, columns=columns, show="headings", height=10)
        for col in columns:
            tree_abonos.heading(col, text=col)
            tree_abonos.column(col, anchor="center", width=100)
        tree_abonos.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Consultar abono inicial y abonos adicionales
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            # Abono inicial (registrado en separados)
            c.execute(
                """
                SELECT abono, metodo_pago, banco, fecha_separado
                FROM separados WHERE factura = ? LIMIT 1
                """,
                (factura,),
            )
            fila_inicial = c.fetchone()
            abono_inicial = 0
            metodo_inicial = ""
            banco_inicial = ""
            fecha_inicial = ""
            if fila_inicial:
                abono_inicial = fila_inicial[0] or 0
                metodo_inicial = fila_inicial[1] or ""
                banco_inicial = fila_inicial[2] or ""
                fecha_inicial = fila_inicial[3] or ""

            c.execute(
                """
                SELECT fecha, monto, metodo_pago, banco
                FROM abonos_separados WHERE factura = ? ORDER BY fecha ASC
                """,
                (factura,),
            )
            abonos = c.fetchall()

            # Insertar primero el abono inicial si es mayor a 0
            if abono_inicial and abono_inicial > 0:
                # Mostrar resumen arriba
                resumen_txt = f"Abono inicial: $ {abono_inicial:,.0f} - Método: {metodo_inicial or 'No especificado'}"
                if banco_inicial:
                    resumen_txt += f" - Banco: {banco_inicial}"
                if fecha_inicial:
                    resumen_txt += f" - Fecha: {fecha_inicial}"
                lbl_abono_inicial.config(text=resumen_txt)
                # Agregar fila al historial
                tree_abonos.insert(
                    "",
                    "end",
                    values=(fecha_inicial or "", abono_inicial, metodo_inicial or "", banco_inicial or ""),
                )

            # Luego los abonos adicionales
            for ab in abonos:
                tree_abonos.insert("", "end", values=ab)
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al cargar abonos: {e}")
        # Mostrar deuda actual
        lbl_deuda = tk.Label(ventana, text=f"Deuda restante: $ {deuda_restante:,.0f}", font="sans 14 bold", bg="#c9dbe1")
        lbl_deuda.pack(pady=5)
        
        if deuda_restante > 0:
            btn_abonar = tk.Button(ventana, text="Abonar", font="sans 14 bold", command=lambda: self.ventana_abonar_adicional(factura, deuda_restante, tree_abonos, lbl_deuda))
            btn_abonar.pack(pady=5)

    def ventana_abonar_adicional(self, factura, deuda_restante, tree_abonos, lbl_deuda):
        ventana = tk.Toplevel(self)
        ventana.title("Abonar a Separado Existente")
        ventana.geometry("400x320+400+200")
        ventana.config(bg="#c9dbe1")
        
        tk.Label(ventana, text=f"Deuda actual: $ {deuda_restante:,.0f}", font="sans 14 bold", bg="#c9dbe1").pack(pady=10)
        tk.Label(ventana, text="Monto a abonar:", font="sans 14 bold", bg="#c9dbe1").pack()
        
        entry_abono = ttk.Entry(ventana, font="sans 14 bold")
        entry_abono.pack(pady=5)
        
        metodo_pago = tk.StringVar(value="efectivo")
        
        banco_opcion = tk.StringVar(value="Bancolombia")
        
        frame_metodo = tk.LabelFrame(ventana, text="Método de Pago", font="sans 12 bold", bg="#c9dbe1")
        frame_metodo.pack(pady=10)
        
        tk.Radiobutton(frame_metodo, text="Efectivo", variable=metodo_pago, value="efectivo", bg="#c9dbe1").pack(side=LEFT, padx=10)
        tk.Radiobutton(frame_metodo, text="Transferencia", variable=metodo_pago, value="transferencia", bg="#c9dbe1").pack(side=LEFT, padx=10)
        
        frame_banco = tk.Frame(ventana, bg="#c9dbe1")
        
        def mostrar_bancos(*args):
            if metodo_pago.get() == "transferencia":
                frame_banco.pack(pady=5)
            else:
                frame_banco.pack_forget()
        
        metodo_pago.trace_add('write', mostrar_bancos)
        
        tk.Label(frame_banco, text="Banco:", font="sans 12", bg="#c9dbe1").pack(side=LEFT)
        
        tk.Radiobutton(frame_banco, text="Bancolombia", variable=banco_opcion, value="Bancolombia", bg="#c9dbe1").pack(side=LEFT)
        tk.Radiobutton(frame_banco, text="Daviplata", variable=banco_opcion, value="Daviplata", bg="#c9dbe1").pack(side=LEFT)
        
        label_error = tk.Label(ventana, text="", font="sans 12", fg="red", bg="#c9dbe1")
        label_error.pack()
        
        def confirmar():
            try:
                abono = float(entry_abono.get())
            except ValueError:
                label_error.config(text="Ingrese un monto válido")
                return
            if abono <= 0 or abono > deuda_restante:
                label_error.config(text="El abono debe ser mayor que 0 y menor o igual a la deuda.")
                return
            banco = banco_opcion.get() if metodo_pago.get() == "transferencia" else None
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")
            
            try:
                conn = sqlite3.connect(self.db_name)
                c = conn.cursor()
                c.execute("""
                    INSERT INTO abonos_separados (factura, fecha, monto, metodo_pago, banco, sucursal )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (factura, fecha, abono, metodo_pago.get(), banco, self.sucursal))
                # Actualizar deuda en separados
                c.execute("""
                    UPDATE separados SET abono = abono + ?, deuda_restante = deuda_restante - ?, estado_deuda = CASE WHEN deuda_restante - ? <= 0 THEN 'pagado' ELSE 'pendiente' END
                    WHERE factura = ?
                """, (abono, abono, abono, factura))
                conn.commit()
                conn.close()
                # Refrescar historial y deuda
                tree_abonos.insert("", "end", values=(fecha, abono, metodo_pago.get(), banco or ''))
                nueva_deuda = deuda_restante - abono
                lbl_deuda.config(text=f"Deuda restante: $ {nueva_deuda:,.0f}")
                if nueva_deuda <= 0:
                    self.mover_separado_a_venta(factura)
                messagebox.showinfo("Éxito", "Abono registrado correctamente.")
                ventana.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al registrar abono: {e}")
        tk.Button(ventana, text="Confirmar abono", font="sans 14 bold", command=confirmar).pack(pady=15)

    def convertir_a_venta(self, factura_separado):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()

            # Obtener los datos del separado, incluyendo sucursal
            c.execute("SELECT cliente, producto, precio, cantidad, total, metodo_pago, banco, sucursal FROM separados WHERE factura = ?", (factura_separado,))
            separados = c.fetchall()

            if not separados:
                messagebox.showerror("Error", "No se encontró el separado con la factura especificada.")
                return

            # Obtener un nuevo número de factura para la venta
            nueva_factura = self.obtener_numero_factura_actual()

            # Mover los datos a la tabla de ventas, incluyendo sucursal
            for separado in separados:
                cliente, producto, precio, cantidad, total, metodo_pago, banco, sucursal = separado
                c.execute("""
                    INSERT INTO ventas (factura, cliente, articulo, precio, cantidad, total, metodo_pago, banco, fecha, hora, sucursal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, DATE('now'), TIME('now'), ?)
                """, (nueva_factura, cliente, producto, precio, cantidad, total, metodo_pago, banco, sucursal))
            # Actualizar el estado del separado a "pagado"
            c.execute("UPDATE separados SET estado_deuda = 'pagado' WHERE factura = ?", (factura_separado,))

            # Eliminar el separado de la tabla separados
            c.execute("DELETE FROM separados WHERE factura = ?", (factura_separado,))

            conn.commit()
            conn.close()

            messagebox.showinfo("Éxito", f"El separado con factura {factura_separado} se ha convertido en una venta con factura {nueva_factura}.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al convertir el separado a venta: {e}")
            if conn:
                conn.close()

    def mover_separado_a_venta(self, factura_separado):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            # Obtener los productos del separado
            c.execute("SELECT cliente, producto, precio, cantidad, total, metodo_pago, banco, sucursal FROM separados WHERE factura = ?", (factura_separado,))
            productos = c.fetchall()
            if not productos:
                messagebox.showerror("Error", "No se encontraron productos para el separado.")
                conn.close()
                return
            cliente = productos[0][0]
            metodo_pago_inicial = productos[0][5]
            banco_inicial = productos[0][6]
            sucursal = productos[0][7]
            sucursal_final = self.sucursal if self.sucursal else sucursal
            # Permitir a admin (sin sucursal) convertir separados a venta usando la sucursal del separado o NULL
            if not sucursal_final or sucursal_final == "None":
                sucursal_final = sucursal if sucursal and sucursal != "None" else None
            # Si aún no hay sucursal, permitir como NULL para admin
            # (Quitar el error y permitir la conversión)
            # Obtener un nuevo número de factura para la venta
            
            nuevo_numero_factura = self.obtener_numero_factura_actual()
            # Determinar método de pago agregado y totales por método a partir del abono inicial y los abonos adicionales
            metodos = set()
            bancos_transfer = set()
            efectivo_total = 0.0
            transferencia_total = 0.0
            if metodo_pago_inicial:
                metodos.add(metodo_pago_inicial.strip().lower())
                if metodo_pago_inicial.strip().lower() == 'transferencia' and banco_inicial:
                    bancos_transfer.add(banco_inicial)
            # Leer el valor acumulado en 'abono' (que puede incluir abonos adicionales)
            try:
                c.execute("SELECT abono FROM separados WHERE factura = ? LIMIT 1", (factura_separado,))
                fila_ab_ini = c.fetchone()
                abono_total_col = float(fila_ab_ini[0]) if fila_ab_ini and fila_ab_ini[0] is not None else 0.0
            except Exception:
                abono_total_col = 0.0
            try:
                c.execute("SELECT metodo_pago, banco, monto FROM abonos_separados WHERE factura = ?", (factura_separado,))
                ab_rows = c.fetchall()
                suma_abonos_adic = 0.0
                for mtd, bco, monto in ab_rows:
                    if mtd:
                        mnorm = str(mtd).strip().lower()
                        if mnorm:
                            metodos.add(mnorm)
                        if mnorm == 'transferencia' and bco:
                            bancos_transfer.add(bco)
                        # Sumar totales por método
                        try:
                            monto_f = float(monto) if monto is not None else 0.0
                        except Exception:
                            monto_f = 0.0
                        if mnorm == 'efectivo':
                            efectivo_total += monto_f
                        elif mnorm == 'transferencia':
                            transferencia_total += monto_f
                        suma_abonos_adic += monto_f
            except Exception:
                pass
            # Calcular el abono inicial real como diferencia entre el valor total en 'separados.abono' y la suma de abonos adicionales
            abono_inicial_real = max(abono_total_col - suma_abonos_adic, 0.0)
            if abono_inicial_real > 0 and metodo_pago_inicial:
                if metodo_pago_inicial.strip().lower() == 'efectivo':
                    efectivo_total += abono_inicial_real
                elif metodo_pago_inicial.strip().lower() == 'transferencia':
                    transferencia_total += abono_inicial_real
            # Construir etiqueta final de método de pago
            if metodos == {'transferencia'}:
                metodo_pago_final = 'transferencia'
            elif metodos == {'efectivo'}:
                metodo_pago_final = 'efectivo'
            elif 'efectivo' in metodos and 'transferencia' in metodos:
                metodo_pago_final = 'efectivo y transferencia'
            elif len(metodos) == 0:
                metodo_pago_final = metodo_pago_inicial or 'No especificado'
            else:
                # Otros casos (p. ej. tarjeta), concatenar únicos en forma legible
                metodo_pago_final = ' y '.join(sorted(metodos))
            banco_final = ' / '.join(sorted({b for b in bancos_transfer if b})) if 'transferencia' in metodos else banco_inicial

            # Registrar (si no existe) el abono inicial también en abonos_separados para tener historial completo
            try:
                if abono_inicial_real and abono_inicial_real > 0:
                    # Usar la fecha del separado si está disponible
                    c.execute("SELECT fecha_separado FROM separados WHERE factura = ? LIMIT 1", (factura_separado,))
                    row_fecha = c.fetchone()
                    fecha_ini = row_fecha[0] if row_fecha and row_fecha[0] else datetime.datetime.now().strftime("%Y-%m-%d")
                    # Insertar un registro de abono inicial si aún no hay ninguno equivalente
                    c.execute(
                        """
                        INSERT INTO abonos_separados (factura, fecha, monto, metodo_pago, banco, sucursal)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (factura_separado, fecha_ini, abono_inicial_real, metodo_pago_inicial, banco_inicial, sucursal_final),
                    )
            except Exception:
                pass

            # Actualizar abonos para que queden asociados al nuevo número de factura de venta
            try:
                c.execute("UPDATE abonos_separados SET factura = ? WHERE factura = ?", (nuevo_numero_factura, factura_separado))
            except Exception:
                pass
            for prod in productos:
                _, producto, precio, cantidad, total, _, _, _ = prod
                c.execute("""
                    INSERT INTO ventas (factura, cliente, articulo, precio, cantidad, total, metodo_pago, banco, fecha, hora, sucursal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, DATE('now'), TIME('now'), ?)
                """, (nuevo_numero_factura, cliente, producto, precio, cantidad, total, metodo_pago_final, banco_final, sucursal_final))
            # Actualizar el estado del separado a "pagado"
            c.execute("UPDATE separados SET estado_deuda = 'pagado' WHERE factura = ?", (factura_separado,))
            # Eliminar el separado de la tabla separados para que no aparezca como 'pagado'
            c.execute("DELETE FROM separados WHERE factura = ?", (factura_separado,))
            conn.commit()
            conn.close()
            # Generar la factura de separado (para reclamar)
            self.generar_factura_separado(
                factura_separado,
                productos,
                cliente,
                sum(float(str(prod[4]).replace(",", "").replace(" ", "")) for prod in productos),
                metodo_pago_final,
                banco_final,
            )
            # Generar la factura de venta (comprobante de venta, diseño ventas)
            from Smart_data_syncro.ventas import Ventas
            ventas_temp = Ventas(self.master, self.username)
            ventas_temp.generar_factura_pdf(
                sum(float(str(prod[4]).replace(",", "").replace(" ", "")) for prod in productos),
                cliente,
                num_factura=nuevo_numero_factura,
                banco=banco_final,
                efectivo_pagado=efectivo_total if efectivo_total > 0 else None,
                transferencia_pagada=transferencia_total if transferencia_total > 0 else None,
            )
            messagebox.showinfo("Éxito", f"El separado con factura {factura_separado} se ha convertido en una venta con factura {nuevo_numero_factura}.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al convertir el separado a venta: {e}")
            if conn:
                conn.close()
    
    def borrar_separado(self, tree):
        """Borra un separado seleccionado y devuelve el stock"""
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Seleccione un separado para borrar.")
            return
        
        values = tree.item(selected[0], "values")
        factura = values[0]
        cliente = values[1]
        producto = values[2]
        
        # Confirmar la acción
        respuesta = messagebox.askyesno(
            "Confirmar borrado", 
            f"¿Está seguro de que desea borrar el separado?\n\n"
            f"Factura: {factura}\n"
            f"Cliente: {cliente}\n"
            f"Producto: {producto}\n\n"
            f"Esta acción devolverá el stock y no se puede deshacer."
        )
        
        if not respuesta:
            return
        
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            
            # Obtener todos los productos del separado para devolver el stock
            c.execute("SELECT producto, cantidad FROM separados WHERE factura = ?", (factura,))
            productos_separado = c.fetchall()
            
            # Devolver el stock de cada producto
            for producto_nombre, cantidad in productos_separado:
                try:
                    c.execute("SELECT id FROM articulos WHERE articulo = ? LIMIT 1", (producto_nombre,))
                    f_id = c.fetchone()
                    if f_id:
                        art_id = f_id[0]
                        c.execute("UPDATE articulos SET stock = stock + ? WHERE id = ?", (cantidad, art_id))
                    else:
                        c.execute("UPDATE articulos SET stock = stock + ? WHERE articulo = ?", (cantidad, producto_nombre))
                except Exception:
                    c.execute("UPDATE articulos SET stock = stock + ? WHERE articulo = ?", (cantidad, producto_nombre))
            
            # Eliminar el separado de la base de datos
            c.execute("DELETE FROM separados WHERE factura = ?", (factura,))
            
            # Eliminar también los abonos adicionales relacionados
            c.execute("DELETE FROM abonos_separados WHERE factura = ?", (factura,))
            
            conn.commit()
            conn.close()
            
            # Remover el item del treeview
            tree.delete(selected[0])
            
            messagebox.showinfo("Éxito", f"El separado con factura {factura} ha sido borrado correctamente.\nEl stock ha sido devuelto.")
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al borrar el separado: {e}")
            if conn:
                conn.close()
