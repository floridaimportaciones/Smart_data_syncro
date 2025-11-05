from tkinter import *
from tkinter import ttk
from Smart_data_syncro.login import Login
from Smart_data_syncro.container import Container
from Smart_data_syncro.login import Login
from Smart_data_syncro.login import Registro
import sys
import os 

class Manager(Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("SmartDataSyncro")
        self.geometry("1100x650+120+20")
        self.resizable(False,False)

        ruta= self.rutas(r"icono.ico")
        self.iconbitmap(ruta)


        container = Frame(self)
        container.pack(side=TOP, fill=BOTH, expand=True)
        container.configure(bg = "gray")

        self.frames = {}
        self.permisos_usuario = {}

        
        for frame_class in (Login, Registro):
            frame = frame_class(container, self)
            self.frames[frame_class] = frame

        
        self.show_frame(Login)

        self.style = ttk.Style()
        self.style.theme_use("clam") 

    def rutas(self,ruta ):
        try: 
            rutabase=sys._MEIPASS
        except Exception:
            rutabase=os.path.abspath(".")
        return os.path.join(rutabase, ruta)

    def show_frame(self, container, permisos=None, username=None):
        if container == Container:
            if container not in self.frames or permisos is not None or username is not None:
                master = next(iter(self.frames.values())).master  # Get container Frame
                if container in self.frames:
                    self.frames[container].destroy()
                container_frame = Container(master, self, permisos=permisos, username=username)
                self.frames[Container] = container_frame
        if container in self.frames:
            frame = self.frames[container]
            frame.tkraise()

def main():
    app = Manager()
    app.mainloop()

if __name__== "__main__":
    main()

