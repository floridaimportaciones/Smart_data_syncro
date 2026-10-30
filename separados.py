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
from Smart_data_syncro.services.separado_service import SeparadoService
from Smart_data_syncro.services.empresa_service import EmpresaService

class Separados(tk.Frame):

    def __init__(self, padre,username=None):
        super().__init__(padre, bg="#c9dbe1")
        self.articulo_service = ArticuloService()
        self.cliente_service = ClienteService()
        self.usuario_service = UsuarioService()
        self.separado_service = SeparadoService()
        self.empresa_service = EmpresaService()
        self.username = username
        self.sucursal = None
        if self.username:
            self.sucursal = self.obtener_sucursal_usuario()
        self.numero_factura = self.separado_service.siguiente_numero_factura()
        self.widgets()
        self.cargar_productos()
        self.cargar_clientes()
        self.productos_seleccionados = []
        self.timer_producto = None
        self.timer_cliente = None
        self.bind("<<ClienteActualizado>>", lambda e: self.cargar_clientes())

    def cargar_clientes(self):
        try:
            self.clientes = [cliente.nombre for cliente in self.cliente_service.listar()]
            self.entry_cliente["values"] = self.clientes
        except Exception as e:
            print("Error al cargar los clientes en Separados: ", e)

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
            # Si self.sucursal tiene valor, solo mostrar productos de esa sucursal.
            # Si es admin (self.sucursal es None), mostrar todos los productos.
            articulos = self.articulo_service.listar()
            if self.sucursal:
                articulos = [a for a in articulos if a.sucursal_obj and a.sucursal_obj.nombre == self.sucursal]
            self.products = [{"nombre": a.articulo, "codigo": a.codigo} for a in articulos]
            self.entry_producto["values"] = [p["nombre"] for p in self.products]
        except Exception as e:
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
            art = (self.articulo_service.obtener_por_nombre(producto_seleccionado)
                   or self.articulo_service.obtener_por_codigo(producto_seleccionado))
            if art:
                self.label_stock.config(text=f"Stock: {art.stock}")
            else:
                self.label_stock.config(text="Stock: No encontrado")
        except Exception as e:
            print("Error al obtener el stock del producto", e)

    def agregar_articulo(self):
        self.numero_factura = self.separado_service.siguiente_numero_factura()

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
            art = self.articulo_service.obtener_por_nombre(producto)

            if art is None:
                messagebox.showerror("Error", "El producto no existe.")
                return

            precio, costo, stock = art.precio, art.costo, art.stock

            if cantidad > stock:
                messagebox.showerror("Error", f"No hay suficiente stock. Solo hay {stock} unidades disponibles.")
                return

            total = cantidad * precio
            total_cop = "{:,.0f}".format(total)

            self.tre.insert("", "end", values = (self.numero_factura, cliente, producto,"{:,.0f}".format(precio),cantidad,total_cop))
            self.productos_seleccionados.append((self.numero_factura, cliente,producto,precio,cantidad,total_cop,costo))

            self.calcular_precio_total()
            self.entry_producto.set('')
            self.entry_cantidad.delete(0,'end')

        except Exception as e:
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
                art = self.articulo_service.obtener_por_nombre(current_product)

                if art is None:
                    messagebox.showerror("Error", "Producto no encontrado.")
                    return

                precio, costo, stock = art.precio, art.costo, art.stock

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

                self.calcular_precio_total()
            except Exception as e:
                print("Error al editar el articulo: ", e)

    def obtener_sucursal_usuario(self):
        if not self.username:
            return None
        try:
            usuario = self.usuario_service.obtener_por_username(self.username)
            if usuario:
                if usuario.rol and usuario.rol.lower() in ["admin", "administrador"]:
                    return None  # Admin puede ver todas las sucursales
                return usuario.sucursal
            return None
        except Exception as e:
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
            cliente = self.entry_cliente.get()
            sucursal = self.sucursal if self.sucursal else None
            factura_real = self.separado_service.registrar_separado(
                self.productos_seleccionados, abono, metodo_pago, banco, sucursal,
            )
            self.generar_factura_separado(factura_real)
            messagebox.showinfo("Separado registrado", "El separado se ha registrado correctamente.")
            self.numero_factura = self.separado_service.siguiente_numero_factura()
            self.label_numero_factura.config(text=str(self.numero_factura))
            self.productos_seleccionados = []
            self.limpiar_lista()
            ventana_pago.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar el separado: {e}")
   
    def generar_factura_separado(self, num_factura, resumen=None):
        # Genera una factura PDF diferenciada para separados.
        # `resumen` se puede pasar ya calculado (p. ej. al convertir a venta,
        # donde el separado ya se borró de la base antes de generar este PDF de cierre).
        try:
            if resumen is None:
                resumen = self.separado_service.obtener_resumen_factura(num_factura)
            if resumen is None:
                print(f"No se encontró el separado {num_factura} para generar la factura")
                return
            cliente = resumen["cliente"]
            metodo_pago = resumen["metodo_pago"]
            banco = resumen["banco"]
            productos_factura = resumen["productos"]
            total_venta = resumen["total_venta"]
            total_abonado = resumen["total_abonado"]
            deuda_restante = resumen["deuda_restante"]

            nombre_archivo = rutas(f"facturas/factura_separado_{num_factura}.pdf")
            os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)

            # Obtener información de la empresa
            info_empresa = self.empresa_service.obtener()
            if info_empresa:
                empresa = {
                    "nombre": info_empresa.nombre, "direccion": info_empresa.direccion,
                    "telefono": info_empresa.telefono, "email": info_empresa.email,
                    "nit": info_empresa.nit,
                }
            else:
                empresa = {
                    "nombre": "Empresa no configurada", "direccion": "Dirección no configurada",
                    "telefono": "Teléfono no configurado", "email": "Email no configurado",
                }

            encabezado = [
                f"Factura: {num_factura}",
                f"Fecha: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
                f"Cliente: {cliente}",
                f"Método de pago: {metodo_pago}{' - ' + banco if banco else ''}",
            ]

            items_ticket = []
            for prod, cant, precio, total in productos_factura:
                try:
                    precio_float = float(str(precio).replace(",", "").replace(" ", ""))
                except Exception:
                    precio_float = 0
                try:
                    total_float = float(str(total).replace(",", "").replace(" ", ""))
                except Exception:
                    total_float = 0
                items_ticket.append((prod, cant, precio_float, total_float))

            resumen_ticket = [
                (f"Total venta: ${total_venta:,.0f}", False),
                (f"Total abonado: ${total_abonado:,.0f}", False),
                (f"Deuda restante: ${deuda_restante:,.0f}", True),
            ]
            pie = ["Conserve este ticket, es su comprobante de separado."]

            generar_ticket_pdf(nombre_archivo, empresa, "FACTURA DE SEPARADO", encabezado, items_ticket, resumen_ticket, pie)
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
            vencidos = self.separado_service.listar_vencidos()
            if vencidos:
                mensaje = "Separados vencidos (más de 60 días):\n\n"
                for v in vencidos:
                    mensaje += f"Factura: {v.factura} | Cliente: {v.cliente} | Fecha alerta: {v.fecha_alerta}\n"
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
                hoy = datetime.datetime.now().strftime("%Y-%m-%d")
                filas = self.separado_service.listar_pendientes(self.sucursal, factura_filtro, cliente_filtro)
                for s in filas:
                    values = (s.factura, s.cliente, s.producto, s.total, s.abono, s.deuda_restante,
                              s.metodo_pago, s.banco, s.estado_deuda, s.fecha_separado, s.fecha_alerta)
                    if s.fecha_alerta and s.fecha_alerta <= hoy:
                        tree.insert("", "end", values=values, tags=("vencido",))
                    else:
                        tree.insert("", "end", values=values)
                tree.tag_configure("vencido", background="#ffcccc")
            except Exception as e:
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
            nombre_archivo = rutas(f"facturas/factura_separado_{factura}.pdf")
            try:
                self.generar_factura_separado(factura)
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
            historial = self.separado_service.obtener_historial_abonos(factura)
            if historial:
                abono_inicial = historial["abono_inicial"]
                metodo_inicial = historial["metodo_inicial"] or ""
                banco_inicial = historial["banco_inicial"] or ""
                fecha_inicial = historial["fecha_inicial"] or ""

                # Insertar primero el abono inicial si es mayor a 0
                if abono_inicial and abono_inicial > 0:
                    resumen_txt = f"Abono inicial: $ {abono_inicial:,.0f} - Método: {metodo_inicial or 'No especificado'}"
                    if banco_inicial:
                        resumen_txt += f" - Banco: {banco_inicial}"
                    if fecha_inicial:
                        resumen_txt += f" - Fecha: {fecha_inicial}"
                    lbl_abono_inicial.config(text=resumen_txt)
                    tree_abonos.insert(
                        "", "end",
                        values=(fecha_inicial or "", abono_inicial, metodo_inicial or "", banco_inicial or ""),
                    )

                # Luego los abonos adicionales
                for ab in historial["abonos_adicionales"]:
                    tree_abonos.insert("", "end", values=ab)
        except Exception as e:
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
            banco = banco_opcion.get() if metodo_pago.get() == "transferencia" else None
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")

            try:
                nueva_deuda = self.separado_service.registrar_abono_adicional(
                    factura, abono, metodo_pago.get(), banco, self.sucursal,
                )
                # Refrescar historial y deuda
                tree_abonos.insert("", "end", values=(fecha, abono, metodo_pago.get(), banco or ''))
                lbl_deuda.config(text=f"Deuda restante: $ {nueva_deuda:,.0f}")
                if nueva_deuda <= 0:
                    self.mover_separado_a_venta(factura)
                messagebox.showinfo("Éxito", "Abono registrado correctamente.")
                ventana.destroy()
            except ValueError as e:
                label_error.config(text=str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Error al registrar abono: {e}")
        tk.Button(ventana, text="Confirmar abono", font="sans 14 bold", command=confirmar).pack(pady=15)

    def mover_separado_a_venta(self, factura_separado):
        try:
            resultado = self.separado_service.mover_a_venta(factura_separado, self.sucursal)

            # Factura de separado "pagado" (para reclamar): el separado ya se borró de
            # la base, así que generamos el PDF con los datos que ya tenemos en memoria.
            resumen_cierre = {
                "cliente": resultado["cliente"],
                "metodo_pago": resultado["metodo_pago_final"],
                "banco": resultado["banco_final"],
                "productos": resultado["productos"],
                "total_venta": resultado["total_venta"],
                "total_abonado": resultado["total_venta"],
                "deuda_restante": 0,
            }
            self.generar_factura_separado(factura_separado, resumen=resumen_cierre)

            # Factura de venta (comprobante de venta, diseño ventas)
            from Smart_data_syncro.ventas import Ventas
            ventas_temp = Ventas(self.master, self.username)
            ventas_temp.generar_factura_pdf(
                resultado["total_venta"],
                resultado["cliente"],
                num_factura=resultado["nuevo_numero_factura"],
                banco=resultado["banco_final"],
                efectivo_pagado=resultado["efectivo_total"] if resultado["efectivo_total"] > 0 else None,
                transferencia_pagada=resultado["transferencia_total"] if resultado["transferencia_total"] > 0 else None,
            )
            messagebox.showinfo("Éxito", f"El separado con factura {factura_separado} se ha convertido en una venta con factura {resultado['nuevo_numero_factura']}.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al convertir el separado a venta: {e}")
    
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
            self.separado_service.eliminar_separado(factura)

            # Remover el item del treeview
            tree.delete(selected[0])

            messagebox.showinfo("Éxito", f"El separado con factura {factura} ha sido borrado correctamente.\nEl stock ha sido devuelto.")

        except Exception as e:
            messagebox.showerror("Error", f"Error al borrar el separado: {e}")
