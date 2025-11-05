import sqlite3
from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox,filedialog
from PIL import Image, ImageTk
import os
import sys

# Funciones para rutas robustas (soporta ejecutable y desarrollo)
def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_log_dir():
    return os.path.join(get_app_dir(), "logs_factura_electronica")

def get_xml_dir():
    return os.path.join(get_app_dir(), "xml_facturas")
from Smart_data_syncro.utils import rutas
import subprocess
from tkinter import filedialog
import base64




class Configuraciones(tk.Frame):
    db_name = "database.db"
    def __init__(self, padre):
        super().__init__(padre)

        self.widgets()
        # Actualizar folios cada vez que la ventana de configuración recibe el foco
        self.bind("<FocusIn>", lambda e: self.actualizar_folios_disponibles())

    def widgets(self):
        frame = tk.LabelFrame(self, text="Configuración", bg="#c9dbe1", font="sans 30 bold", labelanchor="n")
        frame.place(x=0, y=0, width=1100, height=600)

        # Mostrar folios disponibles
        self.folio_inicial = 1  # Ajusta según tu rango real
        self.folio_final = 99999  # Ajusta según tu rango real
        self.label_folios = tk.Label(frame, text="", font="sans 14 bold", bg="#c9dbe1", fg="blue")
        self.label_folios.place(x=850, y=10)
        self.actualizar_folios_disponibles()

        imagen_sucursal = Image.open(rutas("imagenes/sucursales.png")).resize((100, 100))
        imagen_tk = ImageTk.PhotoImage(imagen_sucursal)

        self.btn_sucursal = Button(frame, fg="black", text="Sucursal", font="sans 16 bold", command=self.crear_sucursal)
        self.btn_sucursal.config(image=imagen_tk, compound=TOP, padx=10)
        self.btn_sucursal.image = imagen_tk
        self.btn_sucursal.place(x=150, y=50, width=250, height=150)

        imagen_miEmpresa = Image.open(rutas("imagenes/empresa.png")).resize((100, 100))
        imagen_miEmpresa = ImageTk.PhotoImage(imagen_miEmpresa)        
        
        self.btn_miEmpresa = Button(frame, fg="black", text="Mi empresa", font="sans 16 bold", command=self.ver_mi_empresa)
        self.btn_miEmpresa.config(image=imagen_miEmpresa, compound=TOP, padx=10)
        self.btn_miEmpresa.image = imagen_miEmpresa
        self.btn_miEmpresa.place(x=450, y=50, width=250, height=150)

        imagen_copiaSeguridad = Image.open(rutas("imagenes/guardardb.png")).resize((100, 100))
        imagen_copiaSeguridad = ImageTk.PhotoImage(imagen_copiaSeguridad)

        self.btn_copiaSeguridad = Button(frame, fg="black", text="Copia de seguridad DB", font="sans 16 bold", command=self.copia_seguridad_db)
        self.btn_copiaSeguridad.config(image=imagen_copiaSeguridad, compound=TOP, padx=10)
        self.btn_copiaSeguridad.image = imagen_copiaSeguridad
        self.btn_copiaSeguridad.place(x=750, y=50, width=250, height=150)

        imagen_RestaurarDB = Image.open(rutas("imagenes/cargardb.png")).resize((100, 100))
        imagen_RestaurarDB = ImageTk.PhotoImage(imagen_RestaurarDB)

        self.btn_RestaurarDB = Button(frame, fg="black", text="Restaurar DB", font="sans 16 bold",command=self.restaurar_db)
        self.btn_RestaurarDB.config(image=imagen_RestaurarDB, compound=TOP, padx=10)
        self.btn_RestaurarDB.image = imagen_RestaurarDB
        self.btn_RestaurarDB.place(x=150, y=250, width=250, height=150)
        
        imagen_facturaElectronicaPdf = Image.open(rutas("imagenes/factura.png")).resize((100, 100))
        imagen_facturaElectronicaPdf = ImageTk.PhotoImage(imagen_facturaElectronicaPdf)

        self.btn_facturaElectronicaPdf = Button(frame, fg="black", text="Factura Electrónica PDF", font="sans 16 bold",command=self.descargar_factura_pdf)
        self.btn_facturaElectronicaPdf.config(image=imagen_facturaElectronicaPdf, compound=TOP, padx=10)
        self.btn_facturaElectronicaPdf.image = imagen_facturaElectronicaPdf
        self.btn_facturaElectronicaPdf.place(x=450, y=250, width=250, height=150)
        

    def actualizar_folios_disponibles(self):
        # Cuenta los logs de facturas electrónicas como folios usados
        log_dir = get_log_dir()
        usados = 0
        if os.path.exists(log_dir):
            usados = len([f for f in os.listdir(log_dir) if f.endswith('.log')])
        folios_restantes = max(self.folio_final - self.folio_inicial - usados + 1, 0)
        self.label_folios.config(text=f"Folios disponibles: {folios_restantes}")

    def crear_sucursal(self):
        top = tk.Toplevel(self)
        top.title("Sucursales")
        top.geometry("400x500+200+100")
        top.config(bg="#c9dbe1")
        top.resizable(False, False)
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()

        imagen_guardar = Image.open(rutas("imagenes/guardar.png")).resize((30, 30))
        imagen_guardar = ImageTk.PhotoImage(imagen_guardar)

        imagen_eliminar = Image.open(rutas("imagenes/eliminar.png")).resize((30, 30))
        imagen_eliminar = ImageTk.PhotoImage(imagen_eliminar)

        labelframe = tk.LabelFrame(top, text="Crear sucursales", font="sans 16 bold", bg="#c9dbe1", bd=2,
                                   relief="groove", labelanchor="n")
        labelframe.place(x=20, y=20, width=360, height=450)

        lbl_nombre = tk.Label(labelframe, text="Nombre:", font="sans 12 bold", bg="#c9dbe1")
        lbl_nombre.place(x=20, y=40)

        self.entry_nombre = tk.Entry(labelframe, font="sans 12", width=25)
        self.entry_nombre.place(x=100, y=40, height=30)

        btn_guardar = tk.Button(labelframe, text="Guardar", compound=tk.LEFT, padx=10, font="sans 10 bold",
                                bg="white", command=lambda: self.guardar_y_actualizar(self.entry_nombre.get()))
        btn_guardar.config(image=imagen_guardar)
        btn_guardar.image = imagen_guardar
        btn_guardar.place(x=30, y=90, width=130, height=40)

        btn_eliminar = tk.Button(labelframe, text="Eliminar", compound=tk.LEFT, padx=10, font="sans 10 bold",
                                 bg="white", relief="raised", command= self.eliminar_sucursal_seleccionada)
        btn_eliminar.config(image=imagen_eliminar)
        btn_eliminar.image = imagen_eliminar
        btn_eliminar.place(x=200, y=90, width=130, height=40)

        scrol_y = ttk.Scrollbar(labelframe, orient=VERTICAL)
        scrol_y.place(x=315, y=150, height=240)

        self.tre = ttk.Treeview(labelframe, yscrollcommand=scrol_y.set,
                                columns=("ID", "Nombre"), show="headings", height=10)
        self.tre.place(x=20, y=150, width=300, height=240)

        scrol_y.config(command=self.tre.yview)

        self.tre.heading("ID", text="ID")
        self.tre.heading("Nombre", text="Nombre")

        self.tre.column("ID", width=50, anchor="center")
        self.tre.column("Nombre", width=250, anchor="center")

        self.actualizar_treeview()

    def agregar_sucursal(self, nombre):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS sucursales (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT)")
            cursor.execute("INSERT INTO sucursales (nombre) VALUES (?)", (nombre,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Sucursal creada exitosamente.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al crear la sucursal: {e}")

    def mostrar_sucursales(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS sucursales (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT)")
            cursor.execute("SELECT * FROM sucursales")
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                self.tre.insert("", "end", values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al mostrar las sucursales: {e}")

    def actualizar_treeview(self):
        for item in self.tre.get_children():
            self.tre.delete(item)
        self.mostrar_sucursales()

    def guardar_y_actualizar(self, nombre):
        if not nombre.strip():
            messagebox.showwarning("Campo vacío", "El nombre de la sucursal no puede estar vacío.")
            return
        self.agregar_sucursal(nombre)
        self.entry_nombre.delete(0, END)
        self.actualizar_treeview()

    def eliminar_sucursal(self, sucursal_id, nombre):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sucursales WHERE id = ?", (sucursal_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", f"Sucursal '{nombre}' eliminada exitosamente.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al eliminar la sucursal: {e}")
            return
        self.actualizar_treeview()

    def eliminar_sucursal_seleccionada(self):
        seleccion = self.tre.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una sucursal para eliminar.")
            return

        item = self.tre.item(seleccion[0])
        sucursal_id = item['values'][0]
        nombre = item['values'][1]

        confirmar = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la sucursal '{nombre}'?")
        if confirmar:
            self.eliminar_sucursal(sucursal_id, nombre)

    def copia_seguridad_db(self):
        backup_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")],
            title="Guardar copia de seguridad de la base de datos"
        )
        if not backup_path:
            return
        try:
            # Copiar el archivo de la base de datos
            import shutil
            shutil.copyfile(self.db_name, backup_path)
            messagebox.showinfo("Éxito", f"Copia de seguridad realizada correctamente en {backup_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al realizar la copia de seguridad: {e}")

    def restaurar_db(self):
        backup_path = filedialog.askopenfilename(
            filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")],
            title="Seleccionar archivo de copia de seguridad para restaurar"
        )
        if not backup_path:
            return
        try:
            import shutil
            shutil.copyfile(backup_path, self.db_name)
            messagebox.showinfo("Éxito", f"Base de datos restaurada correctamente desde {backup_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al restaurar la base de datos: {e}")

    def ver_mi_empresa(self):
        top = tk.Toplevel(self)
        top.title("Actualizar Información de la Empresa")
        top.geometry("450x500+200+100")
        top.config(bg="#c9dbe1")
        top.resizable(False, False)
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()

        imagen_guardar = Image.open(rutas("imagenes/guardar.png")).resize((30,30))
        imagen_guardar = ImageTk.PhotoImage(imagen_guardar)

        frame = tk.LabelFrame(top, text="Información empresa", font="sans 30 bold", bg="#c9dbe1")
        frame.place(x=20, y=20, width=410, height=450)

        label_nombre = tk.Label(frame, text="Nombre de la Empresa:", font="sans 14 bold", bg="#c9dbe1")
        label_nombre.place(x=10, y = 5)
        entry_nombre = ttk.Entry(frame, font="sans 14 bold")
        entry_nombre.place(x=10, y=30,width=300,height=40)
        
        label_direccion = tk.Label(frame, text="Dirección:", font="sans 14 bold", bg="#c9dbe1")
        label_direccion.place(x=10, y = 70 )
        entry_direccion = ttk.Entry(frame, font="sans 14 bold")
        entry_direccion.place(x=10, y=100,width=300,height=40)
        
        label_telefono = tk.Label(frame, text="Teléfono", font="sans 14 bold", bg="#c9dbe1")
        label_telefono.place(x=10, y = 150)
        entry_telefono = ttk.Entry(frame, font="sans 14 bold")
        entry_telefono.place(x=10, y=180,width=300,height=40)
        
        label_email = tk.Label(frame, text="Correo", font="sans 14 bold", bg="#c9dbe1")
        label_email.place(x=10, y = 230)
        entry_email = ttk.Entry(frame, font="sans 14 bold")
        entry_email.place(x=10, y=260,width=300,height=40)

        def cargar_info_empresa_local():
            try:
                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, direccion TEXT, telefono TEXT, email TEXT)")
                cursor.execute("SELECT nombre, direccion, telefono, email FROM empresa WHERE id = 1")
                resultado = cursor.fetchone()
                conn.close()
                if resultado:
                    entry_nombre.delete(0, tk.END)
                    entry_direccion.delete(0, tk.END)
                    entry_telefono.delete(0, tk.END)
                    entry_email.delete(0, tk.END)
                    entry_nombre.insert(0, resultado[0])
                    entry_direccion.insert(0, resultado[1])
                    entry_telefono.insert(0, resultado[2])
                    entry_email.insert(0, resultado[3])
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al cargar la información: {e}")

        def guardar_info_empresa_local():
            nombre = entry_nombre.get()
            direccion = entry_direccion.get()
            telefono = entry_telefono.get()
            email = entry_email.get()
            if not nombre or not direccion or not telefono or not email:
                messagebox.showwarning("Campos vacíos", "Por favor complete todos los campos.")
                return
            try:
                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, direccion TEXT, telefono TEXT, email TEXT)")
                cursor.execute("SELECT COUNT(*) FROM empresa")
                count = cursor.fetchone()[0]
                if count > 0:
                    cursor.execute("""
                        UPDATE empresa SET 
                        nombre = ?, 
                        direccion = ?, 
                        telefono = ?, 
                        email = ?
                        WHERE id = 1
                    """, (nombre, direccion, telefono, email))
                else:
                    cursor.execute("""
                        INSERT INTO empresa (nombre, direccion, telefono, email)
                        VALUES (?, ?, ?, ?)
                    """, (nombre, direccion, telefono, email))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Información de la empresa guardada correctamente")
                top.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al guardar la información: {e}")

        btn_guardar = Button(frame, text="Guardar", font="sans 12 bold", command=guardar_info_empresa_local)
        btn_guardar.config(image=imagen_guardar, compound=LEFT, padx=10)
        btn_guardar.image = imagen_guardar
        btn_guardar.place(x=150, y=320, width=200, height=40)

        cargar_info_empresa_local()



    def obtener_info_empresa(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS empresa (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, direccion TEXT, telefono TEXT, email TEXT)")
            cursor.execute("SELECT nombre, direccion, telefono, email FROM empresa WHERE id = 1")
            resultado = cursor.fetchone()
            conn.close()
            if resultado:
                return {
                    "nombre": resultado[0],
                    "direccion": resultado[1],
                    "telefono": resultado[2],
                    "email": resultado[3]
                }
            return None
        except sqlite3.Error as e:
            print(f"Error al obtener la información de la empresa: {e}")
            return None

   

    def backup_postgres(self):
        backup_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("SQL files", "*.sql")],
            title="Guardar backup de la base de datos"
        )
        if not backup_path:
            return
        try:
            cmd = [
                "pg_dump",
                "-h", self.db_config["host"],
                "-p", str(self.db_config["port"]),
                "-U", self.db_config["user"],
                "-d", self.db_config["database"],
                "-F", "c",
                "-b",
                "-v",
                "-f", backup_path
            ]
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_config["password"]
            subprocess.run(cmd, env=env, check=True)
            messagebox.showinfo("Éxito", f"Backup realizado correctamente en {backup_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al realizar el backup: {e}")

    def descargar_factura_pdf(self):
        try:
            # Obtener lista de facturas con transaccionID
            facturas_disponibles = self.obtener_facturas_con_transaccion()
            
            if not facturas_disponibles:
                messagebox.showwarning("Sin facturas", "No se encontraron facturas electrónicas para descargar.")
                return
            
            # Crear ventana para seleccionar factura
            self.mostrar_ventana_seleccion_factura(facturas_disponibles)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener las facturas: {e}")

    def obtener_facturas_con_transaccion(self):
        """Obtiene las facturas que tienen transaccionID de los logs"""
        facturas = []
        log_dir = get_log_dir()
        if not os.path.exists(log_dir):
            return facturas

        for archivo in os.listdir(log_dir):
            if archivo.endswith('.log'):
                try:
                    numero_factura = archivo.split('_')[1]
                    ruta_log = os.path.join(log_dir, archivo)
                    with open(ruta_log, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    import re
                    match_transaccion = re.search(r"['\"]transaccionID['\"]\s*:\s*['\"]([^'\"]+)['\"]", contenido)
                    match_prefijo = re.search(r"<ICC_9>([^<]+)</ICC_9>", contenido)
                    match_folio = re.search(r"<ICC_1>([^<]+)</ICC_1>", contenido)
                    match_numero_real = re.search(r"<ENC_6>([^<]+)</ENC_6>", contenido)
                    if match_transaccion and match_prefijo and match_folio:
                        transaccion_id = match_transaccion.group(1)
                        prefijo = match_prefijo.group(1)
                        folio = match_folio.group(1)
                        numero_real = match_numero_real.group(1) if match_numero_real else f"{prefijo}{folio}"
                        facturas.append({
                            'numero': numero_factura,
                            'transaccionID': transaccion_id,
                            'prefijo': prefijo,
                            'folio': folio,
                            'numero_real': numero_real,
                            'archivo_log': archivo
                        })
                except Exception as e:
                    print(f"Error al procesar {archivo}: {e}")
                    continue
        facturas.sort(key=lambda x: int(x['numero']), reverse=True)
        return facturas

    def mostrar_ventana_seleccion_factura(self, facturas):
        """Muestra una ventana para seleccionar qué factura descargar"""
        top = tk.Toplevel(self)
        top.title("Seleccionar Factura para Descargar PDF")
        top.geometry("500x400+200+100")
        top.config(bg="#c9dbe1")
        top.resizable(False, False)
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()

        frame = tk.LabelFrame(top, text="Facturas Electrónicas Disponibles", font="sans 16 bold", bg="#c9dbe1")
        frame.place(x=20, y=20, width=460, height=320)

        # Crear Treeview para mostrar las facturas
        columns = ("Número", "Núm. Real", "Prefijo", "Folio", "Transacción ID")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        
        tree.heading("Número", text="Núm.")
        tree.heading("Núm. Real", text="Núm. Real")
        tree.heading("Prefijo", text="Prefijo")
        tree.heading("Folio", text="Folio")
        tree.heading("Transacción ID", text="ID Trans.")
        
        tree.column("Número", width=60, anchor="center")
        tree.column("Núm. Real", width=100, anchor="center")
        tree.column("Prefijo", width=60, anchor="center")
        tree.column("Folio", width=60, anchor="center")
        tree.column("Transacción ID", width=140, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.place(x=10, y=30, width=420, height=240)
        scrollbar.place(x=430, y=30, height=240)
        
        # Llenar el treeview con las facturas
        for factura in facturas:
            tree.insert("", "end", values=(factura['numero'], factura['numero_real'], factura['prefijo'], factura['folio'], factura['transaccionID']))
        
        # Botones
        frame_botones = tk.Frame(top, bg="#c9dbe1")
        frame_botones.place(x=50, y=350, width=400, height=40)
        
        btn_descargar = tk.Button(frame_botones, text="Descargar PDF", font="sans 10 bold", bg="#4CAF50", fg="white",
                                 command=lambda: self.descargar_pdf_seleccionado(tree, top))
        btn_descargar.place(x=0, y=0, width=120, height=35)
        
        btn_cerrar = tk.Button(frame_botones, text="Cerrar", font="sans 10 bold", bg="#f44336", fg="white",
                              command=top.destroy)
        btn_cerrar.place(x=130, y=0, width=120, height=35)

    def descargar_pdf_seleccionado(self, tree, ventana):
        """Descarga el PDF de la factura seleccionada"""
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Por favor seleccione una factura.")
            return
        item = tree.item(seleccion[0])
        numero_factura = item['values'][0]
        numero_real = item['values'][1]
        transaccion_id = item['values'][4]
        try:
            from Smart_data_syncro.facturatech_api import FacturaTechClient
            ft_client = FacturaTechClient()
            # Verificar el estado del documento
            estado = ft_client.get_status(transaccion_id)
            if hasattr(estado, 'status'):
                status_value = getattr(estado, 'status', '')
                if status_value != 'SIGNED_XML':
                    messagebox.showwarning("Documento no listo", f"El documento aún no está listo para descarga.\nEstado actual: {status_value}")
                    return
            # Descargar PDF usando el número real (prefijo+folio)
            resultado = ft_client.download_pdf(numero_real)
            code = getattr(resultado, 'code', None) if resultado else None
            success = getattr(resultado, 'success', None) if resultado else None
            if code == '201' or success:
                pdf_base64 = getattr(resultado, 'resourceData', None)
                if pdf_base64:
                    pdf_data = base64.b64decode(pdf_base64)
                    ruta_guardar = filedialog.asksaveasfilename(
                        defaultextension=".pdf",
                        filetypes=[("PDF files", "*.pdf")],
                        title="Guardar factura PDF",
                        initialfile=f"factura_{numero_factura}.pdf"
                    )
                    if ruta_guardar:
                        with open(ruta_guardar, 'wb') as f:
                            f.write(pdf_data)
                        messagebox.showinfo("Éxito", f"Factura PDF guardada en:\n{ruta_guardar}")
                        if messagebox.askyesno("Abrir PDF", "¿Desea abrir el archivo PDF?"):
                            if sys.platform.startswith('win'):
                                os.startfile(ruta_guardar)
                            elif sys.platform.startswith('darwin'):
                                os.system(f'open "{ruta_guardar}"')
                            else:
                                os.system(f'xdg-open "{ruta_guardar}"')
                        ventana.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo obtener los datos del PDF.")
            else:
                # Intentar con prefijo/folio explícitos como respaldo si tenemos esos datos
                prefijo = item['values'][2] if len(item['values']) > 2 else ''
                folio = item['values'][3] if len(item['values']) > 3 else ''
                resultado2 = None
                if prefijo or folio:
                    try:
                        resultado2 = ft_client.download_pdf_by_parts(prefijo, folio)
                    except Exception:
                        resultado2 = None
                final_res = resultado2 or resultado
                code2 = getattr(final_res, 'code', None) if final_res else None
                err_text = []
                if final_res is not None:
                    for key in ('code','error','message','success'):
                        val = getattr(final_res, key, None)
                        if val is not None:
                            err_text.append(f"{key}: {val}")
                else:
                    err_text.append('Sin respuesta del servidor')
                detalle = "\n".join(err_text) if err_text else 'Error desconocido'
                messagebox.showerror("Error", f"Error al descargar PDF (código {code2 or code or 'N/A'}).\n\n{detalle}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al descargar la factura: {e}")

