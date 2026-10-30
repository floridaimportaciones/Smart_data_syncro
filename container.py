from tkinter import *
from tkinter import messagebox
import tkinter as tk
from Smart_data_syncro.ventas import Ventas
from Smart_data_syncro.inventario import Inventario
from Smart_data_syncro.clientes import Clientes
from Smart_data_syncro.reportes import Reportes
from Smart_data_syncro.configuracion import Configuraciones
from Smart_data_syncro.usuarios import Usuarios
from PIL import Image, ImageTk
import sys
import os

class Container(tk.Frame):
    def __init__(self, padre, controlador, permisos=None, username=None):
        super().__init__(padre)
        self.controlador = controlador
        self.permisos = permisos or {}
        self.username = username
        self.pack()
        self.place(x=0, y=0, width=1100, height=650)
        self.widgets()
        self.frames = {}
        self.button = []

    

        
        # Initialize all frames but don't show them yet
        for frame_class in (Ventas, Inventario, Clientes, Configuraciones, Reportes, Usuarios):
            if frame_class in (Ventas, Inventario):
                frame = frame_class(self, username=self.username)
            else:
                frame = frame_class(self)
            self.frames[frame_class] = frame
            self.button.append(frame)
            frame.pack()
            frame.config(bg="#c9dbe1", highlightbackground="#c9dbe1", highlightthickness=1)
            frame.place(x=0, y=40, width=1100, height=610)
            frame.place_forget()  # Hide initially
            
        # Bind events
        self.frames[Clientes].bind("<<ClienteActualizado>>", 
            lambda e: self.frames[Ventas].event_generate("<<ClienteActualizado>>"))

        # Show first accessible module
        if Ventas in self.frames:
            self.show_frame(Ventas)
        else:
            messagebox.showerror("Error", "No tiene acceso a ningún módulo")
            
    def rutas(self,ruta ):
        try:
            rutabase=sys._MEIPASS
        except Exception:
            rutabase=os.path.dirname(os.path.abspath(__file__))
        return os.path.join(rutabase, ruta)

    def cargar_imagen(self, ruta_absoluta):
        try:
            imagen = Image.open(ruta_absoluta)
            imagen = imagen.resize((30, 30))
            return ImageTk.PhotoImage(imagen)
        except Exception:
            return None

    def show_frame(self, container):
        # Hide all frames first
        for frame in self.frames.values():
            frame.place_forget()
            
        # Show selected frame if we have access
        if container in self.frames:
            frame = self.frames[container]
            frame.place(x=0, y=40, width=1100, height=610)
            frame.tkraise()

    def ventas(self):
        self.show_frame(Ventas)
    
    def inventario(self):
        self.show_frame(Inventario)
    
    def clientes(self):
        self.show_frame(Clientes)
    
    def reportes(self):
        self.show_frame(Reportes)
    
    def configuraciones(self):
        self.show_frame(Configuraciones)
    
    def usuarios(self):
        self.show_frame(Usuarios)

    def widgets(self):
        from Smart_data_syncro.login import Login

        frame2 = tk.Frame(self)
        frame2.place(x=0, y=0, width=1100, height=40)

        # Solo crear y mostrar los botones de los módulos permitidos
        imagenes = {
            "Ventas": (self.rutas("imagenes/btnventas.png"), "btn_ventas", self.ventas, 0),
            "Inventario": (self.rutas("imagenes/btninventario.png"), "btn_inventario", self.inventario, 170),
            "Clientes": (self.rutas("imagenes/btnclientes.png"), "btn_clientes", self.clientes, 340),
            "Reportes": (self.rutas("imagenes/btnreportes.png"), "btn_reportes", self.reportes, 510),
            "Configuracion": (self.rutas("imagenes/btnconfiguraciones.png"), "btn_configuraciones", self.configuraciones, 682),
            "Usuarios": (self.rutas("imagenes/btnusuarios.png"), "btn_usuarios", self.usuarios, 855)
        }

        self.buttons = []
        for modulo, (img_path, btn_attr, comando, x) in imagenes.items():
            if self.permisos.get(modulo, False):
                imagen_tk = self.cargar_imagen(img_path)
                btn = Button(frame2, fg="black", text=modulo, font="sans 14 bold", command=comando)
                if imagen_tk is not None:
                    btn.config(image=imagen_tk, compound=LEFT, padx=10)
                    btn.image = imagen_tk
                btn.place(x=x, y=0, width=170, height=40)
                setattr(self, btn_attr, btn)
                self.buttons.append(btn)

        self.imagen_tk_cerrar_sesion = self.cargar_imagen(self.rutas("imagenes/logout.png"))

        self.btn_cerrar_sesion = Button(frame2, text="Salir", font="sans 14 bold", command=lambda: self.controlador.show_frame(Login))
        if self.imagen_tk_cerrar_sesion is not None:
            self.btn_cerrar_sesion.config(image=self.imagen_tk_cerrar_sesion, compound=LEFT, padx=10)
            self.btn_cerrar_sesion.image = self.imagen_tk_cerrar_sesion
        self.btn_cerrar_sesion.place(x=1025, y=0, width=75, height=40)


