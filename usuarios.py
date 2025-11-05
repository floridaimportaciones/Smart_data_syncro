import sqlite3
from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox,filedialog
from PIL import Image, ImageTk
import os
import sys
from Smart_data_syncro.utils import rutas


class Usuarios(tk.Frame):
    import os
    db_name = os.path.abspath('database.db')
    def __init__(self, padre):
        super().__init__(padre)
        self.widgets()
        self.cargar_usuarios()
        self.cargar_sucursales()
        
    def cargar_sucursales(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM sucursales")
            self.sucursales = [sucursal[0] for sucursal in cursor.fetchall()]
            conn.close()
        except sqlite3.Error as e:
            print("Error al cargar sucursales:", e)
            self.sucursales = []

    def widgets(self):
        canvas_usuarios = tk.LabelFrame(self, text="Administrar usuarios", bg="#c9dbe1", font="Arial 16 bold")
        canvas_usuarios.place(x=0, y=10, width=550, height=580)

        # Treeview como tabla
        self.tree = ttk.Treeview(canvas_usuarios, columns=("ID", "Usuario", "Contraseña", "Rol", "Sucursal"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Usuario", text="Usuario")
        self.tree.heading("Contraseña", text="Contraseña")
        self.tree.heading("Rol", text="Rol")
        self.tree.heading("Sucursal", text="Sucursal")
        
        self.tree.column("ID", width=50)
        self.tree.column("Usuario", width=120)
        self.tree.column("Contraseña", width=100)
        self.tree.column("Rol", width=100)
        self.tree.column("Sucursal", width=120)

        self.tree.pack(fill="both", expand=True)

        self.imagen_agregar_usuario = Image.open(rutas("imagenes/agregarUsuario.png"))
        imagen_agregar_usuario = self.imagen_agregar_usuario.resize((50,50))
        imagen_agregar_usuario = ImageTk.PhotoImage(imagen_agregar_usuario)

        self.imagen_actualizar_usuario = Image.open(rutas("imagenes/actualizarUsuario.png"))
        imagen_actualizar_usuario = self.imagen_actualizar_usuario.resize((50,50))
        imagen_actualizar_usuario = ImageTk.PhotoImage(imagen_actualizar_usuario)

        self.imagen_eliminar_usuario = Image.open(rutas("imagenes/eliminarUsuario.png"))
        imagen_eliminar_usuario = self.imagen_eliminar_usuario.resize((50,50))
        imagen_eliminar_usuario = ImageTk.PhotoImage(imagen_eliminar_usuario)


        self.btn_agregar_usuario = tk.Button(self, text="Agregar\nusuario", font="sans 14 bold",
                                        command=self.agregar_usuario)
        self.btn_agregar_usuario.config(image=imagen_agregar_usuario, compound="top")
        self.btn_agregar_usuario.image = imagen_agregar_usuario
        self.btn_agregar_usuario.place(x=600, y=150, height=125, width=125)
        
        self.btn_actualizar_usuario = tk.Button(self, text="Actualizar\nusuario", font="sans 14 bold",
                                              command=self.actualizar_usuario)
        self.btn_actualizar_usuario.config(image=imagen_actualizar_usuario, compound="top")
        self.btn_actualizar_usuario.image = imagen_actualizar_usuario
        self.btn_actualizar_usuario.place(x=750, y=150, height=125, width=125)
        
        self.btn_eliminar_usuario = tk.Button(self, text="Eliminar\nusuario", font="sans 14 bold",
                                            command=self.eliminar_usuario)
        self.btn_eliminar_usuario.config(image=imagen_eliminar_usuario, compound="top")
        self.btn_eliminar_usuario.image = imagen_eliminar_usuario
        self.btn_eliminar_usuario.place(x=900, y=150, height=125, width=125)
        
        

    def agregar_usuario(self):
        top = tk.Toplevel(self)
        top.title("Agregar usuario")
        top.geometry("400x600+200+100")
        top.config(bg="#c9dbe1")
        top.resizable(False, False)
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()

        frame1 = tk.LabelFrame(top, text="Agregar usuario", font="sans 16 bold", bg="#c9dbe1")
        frame1.place(x=20, y=20, width=360, height=550)

        # Usuario
        user = ttk.Label(frame1, text="Nombre de usuario", font= "Arial 16 bold", background="#c9dbe1")
        user.place(x=80, y=20)
        self.username = ttk.Entry(frame1, font= "Arial 16 bold")
        self.username.place(x=50, y=60, width=240, height=40)

        # Contraseña
        pas = ttk.Label(frame1, text="Contraseña", font= "Arial 16 bold", background="#c9dbe1")
        pas.place(x=100, y=110)
        self.password = ttk.Entry(frame1, font= "Arial 16 bold", show="*")
        self.password.place(x=50, y=140, width=240, height=40)

        # Rol
        rol_label = ttk.Label(frame1, text="Rol de usuario", font="Arial 16 bold", background="#c9dbe1")
        rol_label.place(x=100, y=190)
        self.combo_rol = ttk.Combobox(frame1, font="Arial 14")
        self.combo_rol['values'] = ("Administrador", "Cajero")
        self.combo_rol.place(x=50, y=230, width=240, height=35)

        # Sucursal
        sucursal_label = ttk.Label(frame1, text="Sucursal", font="Arial 16 bold", background="#c9dbe1")
        sucursal_label.place(x=100, y=270)
        self.combo_sucursal = ttk.Combobox(frame1, font="Arial 14")
        self.combo_sucursal['values'] = self.sucursales
        self.combo_sucursal.place(x=50, y=310, width=240, height=35)

        def guardar_usuario():
            username = self.username.get()
            password = self.password.get()
            rol = self.combo_rol.get()
            sucursal = self.combo_sucursal.get()

            if not username or not password or not rol or not sucursal:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return

            try:
                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO usuarios (username, password, rol, sucursal) VALUES (?, ?, ?, ?)",
                             (username, password, rol, sucursal))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Usuario agregado correctamente.")
                top.destroy()
                self.cargar_usuarios()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"No se pudo agregar el usuario: {e}")

        # Botones
        self.imagen_guardar = Image.open(rutas("imagenes/guardar.png"))
        imagen_guardar = self.imagen_guardar.resize((30, 30))
        imagen_guardar = ImageTk.PhotoImage(imagen_guardar)

        self.btn_guardar = tk.Button(frame1, text="Guardar", font="sans 10 bold", command=guardar_usuario)
        self.btn_guardar.config(image=imagen_guardar, compound="left")
        self.btn_guardar.image = imagen_guardar
        self.btn_guardar.place(x=50, y=400, width=100, height=40)

        self.imagen_cancelar = Image.open(rutas("imagenes/cancelar.png"))
        imagen_cancelar = self.imagen_cancelar.resize((30, 30))
        imagen_cancelar = ImageTk.PhotoImage(imagen_cancelar)

        self.btn_cancelar = tk.Button(frame1, text="Cancelar", font="sans 10 bold", command=top.destroy)
        self.btn_cancelar.config(image=imagen_cancelar, compound="left")
        self.btn_cancelar.image = imagen_cancelar
        self.btn_cancelar.place(x=190, y=400, width=100, height=40)
        

    def actualizar_usuario(self):
        seleccion = self.tree.focus()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para actualizar.")
            return

        datos = self.tree.item(seleccion, "values")
        id_usuario = datos[0]
        nombre_actual = datos[1]
        contraseña_actual = datos[2]
        rol_actual = datos[3]
        sucursal_actual = datos[4] if len(datos) > 4 else ""

        top = tk.Toplevel(self)
        top.title("Actualizar usuario")
        top.geometry("400x600+200+100")
        top.config(bg="#c9dbe1")
        top.resizable(False, False)
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()

        frame1 = tk.LabelFrame(top, text="Actualizar usuario", font="sans 16 bold", bg="#c9dbe1")
        frame1.place(x=20, y=20, width=360, height=550)

        # Usuario
        lbl_user = ttk.Label(frame1, text="Nombre de usuario", font="Arial 16 bold", background="#c9dbe1")
        lbl_user.place(x=80, y=20)
        entry_user = ttk.Entry(frame1, font="Arial 16 bold")
        entry_user.place(x=50, y=60, width=240, height=40)
        entry_user.insert(0, nombre_actual)

        # Contraseña
        lbl_pass = ttk.Label(frame1, text="Contraseña", font="Arial 16 bold", background="#c9dbe1")
        lbl_pass.place(x=100, y=110)
        entry_pass = ttk.Entry(frame1, font="Arial 16 bold", show="*")
        entry_pass.place(x=50, y=140, width=240, height=40)
        entry_pass.insert(0, contraseña_actual)

        # Rol
        lbl_rol = ttk.Label(frame1, text="Rol de usuario", font="Arial 16 bold", background="#c9dbe1")
        lbl_rol.place(x=100, y=190)
        combo_rol = ttk.Combobox(frame1, font="Arial 14")
        combo_rol['values'] = ("Administrador", "Cajero")
        combo_rol.place(x=50, y=230, width=240, height=35)
        combo_rol.set(rol_actual)

        # Sucursal
        lbl_sucursal = ttk.Label(frame1, text="Sucursal", font="Arial 16 bold", background="#c9dbe1")
        lbl_sucursal.place(x=100, y=270)
        combo_sucursal = ttk.Combobox(frame1, font="Arial 14")
        combo_sucursal['values'] = self.sucursales
        combo_sucursal.place(x=50, y=310, width=240, height=35)
        if sucursal_actual in self.sucursales:
            combo_sucursal.set(sucursal_actual)

        def guardar_actualizacion():
            nuevo_usuario = entry_user.get()
            nueva_contraseña = entry_pass.get()
            nuevo_rol = combo_rol.get()
            nueva_sucursal = combo_sucursal.get()

            if not nuevo_usuario or not nueva_contraseña or not nuevo_rol or not nueva_sucursal:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return

            try:
                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE usuarios
                    SET username = ?, password = ?, rol = ?, sucursal = ?
                    WHERE id = ?
                """, (nuevo_usuario, nueva_contraseña, nuevo_rol, nueva_sucursal, id_usuario))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")
                top.destroy()
                self.cargar_usuarios()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"No se pudo actualizar el usuario: {e}")

        # Botones
        btn_guardar = tk.Button(frame1, text="Guardar", command=guardar_actualizacion, font="sans 14 bold")
        btn_guardar.place(x=50, y=400, width=100, height=40)

        btn_cancelar = tk.Button(frame1, text="Cancelar", command=top.destroy, font="sans 14 bold")
        btn_cancelar.place(x=190, y=400, width=100, height=40)


    def eliminar_usuario(self):
        
        seleccion = self.tree.focus()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para eliminar.")
            return

        datos = self.tree.item(seleccion, "values")
        id_usuario = datos[0]
        nombre_usuario = datos[1]

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro que deseas eliminar al usuario '{nombre_usuario}'?"
        )

        if confirmar:
            try:
                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Éxito", f"Usuario '{nombre_usuario}' eliminado correctamente.")
                self.cargar_usuarios()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"No se pudo eliminar el usuario: {e}")


    def permisos_usuario(self):
        # Lógica para asignar permisos a un usuario
        pass    
    
    
    def cargar_usuarios(self):
        try:
            # Limpiar el Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Conectar a la base de datos y obtener usuarios
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password, rol, sucursal FROM usuarios")
            usuarios = cursor.fetchall()
            
            if not usuarios:
                messagebox.showinfo("Información", "No hay usuarios registrados.")
                return
            
            # Insertar usuarios en el Treeview
            for usuario in usuarios:
                # Asegurar que tenemos todos los campos
                id_usuario = usuario[0]
                username = usuario[1]
                password = usuario[2]
                rol = usuario[3]
                sucursal = usuario[4] if len(usuario) > 4 else "No asignada"
                
                usuario_mostrar = (id_usuario, username, password, rol, sucursal)
                self.tree.insert('', 'end', values=usuario_mostrar)
            
            conn.close()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos: {e}")
            return

