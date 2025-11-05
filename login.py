import sqlite3
from tkinter import *
import tkinter as tk
from Smart_data_syncro.container import Container
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import Smart_data_syncro.permisos as permisos
import os
import sys
from Smart_data_syncro.utils import rutas

class Login(tk.Frame):
    db_name ="database.db"

    def __init__(self, padre,controlador):
        super().__init__(padre)
        self.pack()
        self.place(x=0, y=0, width= 1100, height= 650)
        self.controlador = controlador
        self.widgets()
        self.permisos_usuario = {}

    def validacion(self,user, pas ):
        return len(user) > 0 and len(pas) > 0
    
    def login(self):
        user = self.username.get()
        pas = self.password.get()

        if self.validacion(user, pas):
            # Solo consultar por usuario primero
            consulta = "SELECT username, password, rol FROM usuarios WHERE username = ?"
            parametros = (user,)

            try:
                with sqlite3.connect(self.db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute(consulta, parametros)
                    resultado = cursor.fetchone()

                    if resultado:
                        stored_user, stored_pass, rol_usuario = resultado
                        # Validate password (for now in plain text, should be hashed in production)
                        if pas == stored_pass:
                            # Normalize role names
                            if rol_usuario.lower() in ["admin", "administrador"]:
                                rol_usuario = "Administrador"
                            elif rol_usuario.lower() in ["cajero", "caja"]:
                                rol_usuario = "Cajero"
                                
                            # Get permissions for the role
                            self.permisos_usuario = permisos.obtener_permisos_por_rol(rol_usuario)
                            
                            if not self.permisos_usuario:
                                messagebox.showerror("Error", "El rol no tiene permisos definidos.")
                                return
                                
                            self.control1()
                            messagebox.showinfo("Bienvenido", f"¡Bienvenido {stored_user}! Has iniciado sesión correctamente.")
                        else:
                            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
                            self.password.delete(0, "end")
                    else:
                        self.username.delete(0, "end")
                        self.password.delete(0, "end")
                        messagebox.showerror("Error", "Usuario no encontrado.")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error de conexión a la base de datos: {e}")
        else:
            messagebox.showerror("Error", "Por favor, complete todos los campos.")

    def control1(self):
        # Pass permissions and username to Container frame and show it
        self.controlador.show_frame(Container, permisos=self.permisos_usuario, username=self.username.get())

    def control2(self):
        self.controlador.show_frame (Registro)

    def widgets(self):
        fondo = tk.Frame(self, bg="#c9dbe1")
        fondo.pack()
        fondo.place(x=0, y=0, width= 1100, height= 650)

        self.bg_image = Image.open(rutas("imagenes/fondo.png"))
        self.bg_image = self.bg_image.resize((1100, 650))
        self.bg_image = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = ttk.Label(fondo, image=self.bg_image)
        self.bg_label.place(x=0, y=0, width= 1100, height= 650)

        frame1 = tk.Frame(self, bg="white", highlightbackground="black", highlightthickness=1)
        frame1.place(x=350, y = 70, width= 400, height= 560)

        self.logo_imagen = Image.open(rutas("imagenes/logo.png"))
        self.logo_imagen = self.logo_imagen.resize((200, 200))
        self.logo_imagen = ImageTk.PhotoImage(self.logo_imagen)
        self.logo_label = ttk.Label(frame1, image=self.logo_imagen, background="white")
        self.logo_label.place(x=100, y= 20)
        
        
        user = ttk.Label(frame1, text="Nombre de usuario", font= "Arial 16 bold", background="white")
        user.place(x=100, y= 250)
        self.username = ttk.Entry(frame1, font= "Arial 16 bold")
        self.username.place(x=80, y= 290, width= 240, height= 40)

        pas = ttk.Label(frame1, text="Contraseña", font= "arial 16 bold", background="white")
        pas.place(x=100, y= 340)
        self.password = ttk.Entry(frame1, font= "Arial 16 bold", show="*")
        self.password.place(x=80, y= 380, width= 240, height= 40)

        btn1 = tk.Button(frame1, text="Iniciar Sesión", font="arial 16 bold" , command=self.login)
        btn1.place(x=80, y= 440, width= 240, height= 40)

        btn2 = tk.Button(frame1, text="Registrarse", font="arial 16 bold", command=self.control2)
        btn2.place(x=80, y= 490, width= 240, height= 40)

        



class Registro(tk.Frame):
    db_name ="database.db"


    def __init__(self, padre, controlador):
        super().__init__(padre)
        self.pack()
        self.place(x=0, y=0, width= 1100, height= 650)
        self.controlador = controlador
        self.widgets()

    def validacion(self,user, pas ):
        return len(user) > 0 and len(pas) > 0
    
    def eje_consulta(self, consulta, parametros=()):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(consulta, parametros)
                conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror(title="Error", message="Error al ejecutar la consulta: {} ".format(e))
    
    def registro(self):
        user = self.username.get()
        pas = self.password.get()
        key = self.key.get()
        if self.validacion(user, pas):
            if len(pas) < 6:
                messagebox.showerror(title="Error", message="La contraseña debe tener al menos 6 caracteres.")
                self.username.delete(0, "end")
                self.password.delete(0, "end")
            else:
                if key == "1234":
                    consulta = "INSERT INTO usuarios VALUES (?, ?, ?, ?, ?)"
                    rol = self.combo_rol.get()
                    # Puedes agregar aquí un campo para sucursal, o dejarlo vacío por defecto
                    sucursal = ""  # O podrías mostrar un combobox para elegir sucursal
                    parametros = (None, user, pas, rol, sucursal)
                    self.eje_consulta(consulta, parametros)
                    messagebox.showinfo(title="Registro exitoso", message="Usuario registrado correctamente.")
                    self.control1()
                else:
                    messagebox.showerror(title="Error", message="Código de registro incorrecto.")
        else:
            messagebox.showerror(title="Error", message="Por favor, complete todos los campos.")

    def control1(self):
        self.controlador.show_frame (Container)
    
    def control2(self):
        self.controlador.show_frame (Login)
        

    def widgets(self):
        fondo = tk.Frame(self, bg="gray")
        fondo.pack()
        fondo.place(x=0, y=0, width= 1100, height= 650)

        self.bg_image = Image.open(rutas("imagenes/fondo.png"))
        self.bg_image = self.bg_image.resize((1100, 650))
        self.bg_image = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = ttk.Label(fondo, image=self.bg_image)
        self.bg_label.place(x=0, y=0, width= 1100, height= 650)

        frame1 = tk.Frame(self, bg="white", highlightbackground="black", highlightthickness=1)
        frame1.place(x=350, y = 10, width= 400, height= 630)

        
        
        user = ttk.Label(frame1, text="Nombre de usuario", font= "Arial 16 bold", background="white")
        user.place(x=100, y= 120)
        self.username = ttk.Entry(frame1, font= "Arial 16 bold")
        self.username.place(x=80, y= 160, width= 240, height= 40)

        pas = ttk.Label(frame1, text="Contraseña", font= "arial 16 bold", background="white")
        pas.place(x=100, y=210 )
        self.password = ttk.Entry(frame1, font= "Arial 16 bold", show="*")
        self.password.place(x=80, y= 250, width= 240, height= 40)

        rol_label = ttk.Label(frame1, text="Rol de usuario", font="arial 16 bold", background="white")
        rol_label.place(x=100, y=290)

        self.combo_rol = ttk.Combobox(frame1, font="Arial 14")
        self.combo_rol['values'] = ("Administrador", "Cajero")  
        self.combo_rol.place(x=80, y=330, width=240, height=35)
  

        key = ttk.Label(frame1,text="Código de registro",font="arial 16 bold", background="white")
        key.place(x=100, y= 370)
        self.key = ttk.Entry(frame1, font= "Arial 16 bold", show="*")
        self.key.place(x=80, y= 410, width= 240, height= 40)

        btn3 = tk.Button(frame1, text="Registrarse", font="arial 16 bold", command=self.registro)
        btn3.place(x=80, y= 520, width= 240, height= 40)

        btn4 = tk.Button(frame1, text="Regresar", font="arial 16 bold", command=self.control2)
        btn4.place(x=80, y= 570, width= 240, height= 40)

