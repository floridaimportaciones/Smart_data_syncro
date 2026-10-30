from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox,filedialog
from PIL import Image, ImageTk
import os

from Smart_data_syncro.services.sucursal_service import SucursalService
from Smart_data_syncro.services.empresa_service import EmpresaService

from Smart_data_syncro.utils import rutas, imagen_segura, DB_PATH
import subprocess
from tkinter import filedialog




class Configuraciones(tk.Frame):
    db_name = DB_PATH
    def __init__(self, padre):
        super().__init__(padre)
        self.sucursal_service = SucursalService()
        self.empresa_service = EmpresaService()

        self.widgets()

    def widgets(self):
        frame = tk.LabelFrame(self, text="Configuración", bg="#c9dbe1", font="sans 30 bold", labelanchor="n")
        frame.place(x=0, y=0, width=1100, height=600)

        imagen_sucursal = imagen_segura(rutas("imagenes/sucursales.png")).resize((100, 100))
        imagen_tk = ImageTk.PhotoImage(imagen_sucursal)

        self.btn_sucursal = Button(frame, fg="black", text="Sucursal", font="sans 16 bold", command=self.crear_sucursal)
        self.btn_sucursal.config(image=imagen_tk, compound=TOP, padx=10)
        self.btn_sucursal.image = imagen_tk
        self.btn_sucursal.place(x=150, y=50, width=250, height=150)

        imagen_miEmpresa = imagen_segura(rutas("imagenes/empresa.png")).resize((100, 100))
        imagen_miEmpresa = ImageTk.PhotoImage(imagen_miEmpresa)

        self.btn_miEmpresa = Button(frame, fg="black", text="Mi empresa", font="sans 16 bold", command=self.ver_mi_empresa)
        self.btn_miEmpresa.config(image=imagen_miEmpresa, compound=TOP, padx=10)
        self.btn_miEmpresa.image = imagen_miEmpresa
        self.btn_miEmpresa.place(x=450, y=50, width=250, height=150)

        imagen_copiaSeguridad = imagen_segura(rutas("imagenes/guardardb.png")).resize((100, 100))
        imagen_copiaSeguridad = ImageTk.PhotoImage(imagen_copiaSeguridad)

        self.btn_copiaSeguridad = Button(frame, fg="black", text="Copia de seguridad DB", font="sans 16 bold", command=self.copia_seguridad_db)
        self.btn_copiaSeguridad.config(image=imagen_copiaSeguridad, compound=TOP, padx=10)
        self.btn_copiaSeguridad.image = imagen_copiaSeguridad
        self.btn_copiaSeguridad.place(x=750, y=50, width=250, height=150)

        imagen_RestaurarDB = imagen_segura(rutas("imagenes/cargardb.png")).resize((100, 100))
        imagen_RestaurarDB = ImageTk.PhotoImage(imagen_RestaurarDB)

        self.btn_RestaurarDB = Button(frame, fg="black", text="Restaurar DB", font="sans 16 bold",command=self.restaurar_db)
        self.btn_RestaurarDB.config(image=imagen_RestaurarDB, compound=TOP, padx=10)
        self.btn_RestaurarDB.image = imagen_RestaurarDB
        self.btn_RestaurarDB.place(x=150, y=250, width=250, height=150)

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

        imagen_guardar = imagen_segura(rutas("imagenes/guardar.png")).resize((30, 30))
        imagen_guardar = ImageTk.PhotoImage(imagen_guardar)

        imagen_eliminar = imagen_segura(rutas("imagenes/eliminar.png")).resize((30, 30))
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
            self.sucursal_service.crear(nombre)
            messagebox.showinfo("Éxito", "Sucursal creada exitosamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear la sucursal: {e}")

    def mostrar_sucursales(self):
        try:
            for sucursal in self.sucursal_service.listar():
                self.tre.insert("", "end", values=(sucursal.id, sucursal.nombre))
        except Exception as e:
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
            self.sucursal_service.eliminar(sucursal_id)
            messagebox.showinfo("Éxito", f"Sucursal '{nombre}' eliminada exitosamente.")
        except Exception as e:
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

        imagen_guardar = imagen_segura(rutas("imagenes/guardar.png")).resize((30,30))
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
                empresa = self.empresa_service.obtener()
                if empresa:
                    entry_nombre.delete(0, tk.END)
                    entry_direccion.delete(0, tk.END)
                    entry_telefono.delete(0, tk.END)
                    entry_email.delete(0, tk.END)
                    entry_nombre.insert(0, empresa.nombre)
                    entry_direccion.insert(0, empresa.direccion)
                    entry_telefono.insert(0, empresa.telefono)
                    entry_email.insert(0, empresa.email)
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar la información: {e}")

        def guardar_info_empresa_local():
            nombre = entry_nombre.get()
            direccion = entry_direccion.get()
            telefono = entry_telefono.get()
            email = entry_email.get()
            try:
                self.empresa_service.guardar(nombre, direccion, telefono, email)
                messagebox.showinfo("Éxito", "Información de la empresa guardada correctamente")
                top.destroy()
            except ValueError as e:
                messagebox.showwarning("Campos vacíos", str(e))
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar la información: {e}")

        btn_guardar = Button(frame, text="Guardar", font="sans 12 bold", command=guardar_info_empresa_local)
        btn_guardar.config(image=imagen_guardar, compound=LEFT, padx=10)
        btn_guardar.image = imagen_guardar
        btn_guardar.place(x=150, y=320, width=200, height=40)

        cargar_info_empresa_local()



    def obtener_info_empresa(self):
        try:
            empresa = self.empresa_service.obtener()
            if empresa:
                return {
                    "nombre": empresa.nombre,
                    "direccion": empresa.direccion,
                    "telefono": empresa.telefono,
                    "email": empresa.email
                }
            return None
        except Exception as e:
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
