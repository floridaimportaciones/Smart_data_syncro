import sqlite3
import shutil
from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
from tkcalendar import DateEntry
from datetime import date
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import locale
from openpyxl import Workbook
import os
import sys
from Smart_data_syncro.utils import rutas

# Configurar el formato de moneda para español
locale.setlocale(locale.LC_ALL, 'es_ES')


class Reportes(tk.Frame):

    db_name = 'database.db'

    def __init__(self, padre):
        super().__init__(padre)
        self.widgets()

    def widgets(self):

        self.imagen_reporte_ventas_totales = Image.open(rutas("imagenes/reporte.png"))
        imagen_resize = self.imagen_reporte_ventas_totales.resize((125, 125))
        imagen_tk = ImageTk.PhotoImage(imagen_resize)

        self.imagen_reportes_ganancias = Image.open(rutas("imagenes/reporte1.png"))
        imagen_resize_ganancias = self.imagen_reportes_ganancias.resize((125, 125))
        imagen_tk_ganancias = ImageTk.PhotoImage(imagen_resize_ganancias)

        self.imagen_reportes_ventas_por_mes = Image.open(rutas("imagenes/reporte2.png"))
        imagen_resize_ventas_por_mes = self.imagen_reportes_ventas_por_mes.resize((125, 125))
        imagen_tk_ventas_por_mes = ImageTk.PhotoImage(imagen_resize_ventas_por_mes)

        self.imagen_grafico_ganancias_por_mes = Image.open(rutas("imagenes/reporte3.png"))
        imagen_resize_grafico = self.imagen_grafico_ganancias_por_mes.resize((125, 125))
        imagen_tk_grafico = ImageTk.PhotoImage(imagen_resize_grafico)

        self.imagen_exportar_excel = Image.open(rutas("imagenes/excel.png"))
        imagen_resize_exportar_excel = self.imagen_exportar_excel.resize((125, 125))
        imagen_tk_exportar_excel = ImageTk.PhotoImage(imagen_resize_exportar_excel)


        frame = tk.LabelFrame(self, text="Reportes", bg="#c9dbe1", font="sans 30 bold", labelanchor="n")
        frame.place(x=0, y=0, width=1100, height=600)

        self.btn_reporte_ventas_totales = Button(frame, fg="black", text="Reporte ventas totales", font="sans 14",command=self.reporte_ventas_totales)
        self.btn_reporte_ventas_totales.config(image=imagen_tk, compound=TOP, padx=10)
        self.btn_reporte_ventas_totales.image = imagen_tk
        self.btn_reporte_ventas_totales.place(x=50, y=50, width=230, height=200)

        self.btn_reporte_ganancias = Button(frame, fg="black", text="Reporte de ganancias", font="sans 14", command=self.reporte_ganancias)
        self.btn_reporte_ganancias.config(image=imagen_tk_ganancias, compound=TOP, padx=10)
        self.btn_reporte_ganancias.image = imagen_tk_ganancias
        self.btn_reporte_ganancias.place(x=300, y=50, width=230, height=200)

        self.btn_reportes_ventas_por_mes = Button(frame, fg="black", text="Reporte ventas por mes", font="sans 14 ",command=self.reportes_ventas_por_mes)
        self.btn_reportes_ventas_por_mes.config(image=imagen_tk_ventas_por_mes, compound=TOP, padx=10)
        self.btn_reportes_ventas_por_mes.image = imagen_tk_ventas_por_mes
        self.btn_reportes_ventas_por_mes.place(x=550, y=50, width=230, height=200)

        self.btn_grafico_ganancias_por_mes= Button(frame, fg="black", text="Gráfico de ganancias por mes", font="sans 14 ", command=self.grafico_ganancias_por_mes)
        self.btn_grafico_ganancias_por_mes.config(image=imagen_tk_grafico, compound=TOP, padx=10)
        self.btn_grafico_ganancias_por_mes.image = imagen_tk_grafico
        self.btn_grafico_ganancias_por_mes.place(x=800, y=50, width=230, height=200)
          
        self.btn_exportar_excel = Button(frame, fg="black", text="Exportar Excel", font="sans 14 ", command=self.mostrar_ventana_exportar)
        self.btn_exportar_excel.config(image=imagen_tk_exportar_excel, compound=TOP, padx=10)
        self.btn_exportar_excel.image = imagen_tk_exportar_excel
        self.btn_exportar_excel.place(x=425, y=300, width=230, height=200)
        
    def reporte_ventas_totales(self):
        top = tk.Toplevel(self)
        top.title("Reporte de Ventas Totales")
        top.geometry("550x550+200+100")
        top.config(bg="#c9dbe1")
        top.resizable(False, False)
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()

        imagen_filtrar = Image.open(rutas("imagenes/filtrar.png")).resize((30, 30))
        imagen_filtrar = ImageTk.PhotoImage(imagen_filtrar)

        lbl_titulo = tk.Label(top, text="Reporte de ventas totales", font=("sans 26 bold"), bg="#c9dbe1")
        lbl_titulo.pack(pady=(15, 5))

        frame_filtro = tk.Frame(top, bg="#dbe7ed", bd=1, relief="solid")
        frame_filtro.pack(pady=5, padx=10, fill="x")

        lbl_desde = tk.Label(frame_filtro, text="Desde:", font=("sans 14 bold"), bg="#dbe7ed")
        lbl_desde.grid(row=0, column=0, padx=10, pady=10)

        fecha_desde = DateEntry(frame_filtro, width=12, background='darkblue', foreground='white',
                            borderwidth=2, date_pattern="yyyy-mm-dd")
        fecha_desde.set_date(date.today())
        fecha_desde.grid(row=0, column=1, padx=5)

        lbl_hasta = tk.Label(frame_filtro, text="Hasta:", font=("sans 14 bold"), bg="#dbe7ed")
        lbl_hasta.grid(row=0, column=2, padx=10)

        fecha_hasta = DateEntry(frame_filtro, width=12, background='darkblue', foreground='white',
                            borderwidth=2, date_pattern="yyyy-mm-dd")
        fecha_hasta.set_date(date.today())
        fecha_hasta.grid(row=0, column=3, padx=5)

        frame_tabla = tk.Frame(top, bg="#c9dbe1")
        frame_tabla.pack(padx=10, pady=(5, 10), fill="both", expand=True)

        self.tree = ttk.Treeview(frame_tabla, columns=("Cantidad de productos vendidos", "Total de ventas"), show="headings")

        self.tree.heading("Cantidad de productos vendidos", text="Cantidad de productos vendidos")
        self.tree.heading("Total de ventas", text="Total de ventas")

        self.tree.column("Cantidad de productos vendidos", anchor="center", width=200)
        self.tree.column("Total de ventas", anchor="center", width=200)
        self.tree.pack(fill="both", expand=True)

        def filtrar():
            try:
                fecha_ini = fecha_desde.get_date()
                fecha_fin = fecha_hasta.get_date()

                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("""
                SELECT SUM(cantidad), SUM(total)
                FROM ventas
                WHERE fecha BETWEEN ? AND ?
                """, (fecha_ini, fecha_fin))
                resultado = cursor.fetchone()
                conn.close()

                for fila in self.tree.get_children():
                    self.tree.delete(fila)

                if resultado and resultado[0] is not None:
                    self.tree.insert("", "end", values=(resultado[0], f"${resultado[1]:,.2f}"))
                else:
                    messagebox.showinfo("Sin datos", "No se encontraron ventas en ese rango de fechas.")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al consultar la base de datos: {e}")

        btn_filtrar = tk.Button(frame_filtro, text="  Filtrar", font="sans 14 bold", command=filtrar)
        btn_filtrar.config(image=imagen_filtrar, compound=LEFT, padx=5, bg="#dbe7ed", bd=0)
        btn_filtrar.image = imagen_filtrar
        btn_filtrar.place(x=400, y=5, width=100, height=40)

        lbl_explicacion = tk.Label(top,
            text="El reporte de ventas totales equivale al total de las ventas de los\nproductos incluyendo costo y ganancia",
            font=("Arial", 9, "bold"), bg="#c9dbe1", justify="center"
        )
        lbl_explicacion.pack(pady=(5, 10))

    def reporte_ganancias(self):
        top = tk.Toplevel(self)
        top.title("Reporte ventas totales")
        top.geometry("550x550+200+100")
        top.config(bg="#c9dbe1")
        top.resizable(False, False)
        top.transient(self.master)
        top.grab_set()
        top.focus_set()
        top.lift()

        imagen_filtrar = Image.open(rutas("imagenes/filtrar.png")).resize((30, 30))
        imagen_filtrar = ImageTk.PhotoImage(imagen_filtrar)

        lbl_titulo = tk.Label(top, text="Reporte de ganancias", font=("sans 26 bold"), bg="#c9dbe1")
        lbl_titulo.pack(pady=(15, 5))

        # Frame para los campos de fecha
        frame_filtro = tk.Frame(top, bg="#dbe7ed", bd=1, relief="solid")
        frame_filtro.pack(pady=5, padx=10, fill="x")

        # Campo Desde
        lbl_desde = tk.Label(frame_filtro, text="Desde:", font=("sans 14 bold"), bg="#dbe7ed")
        lbl_desde.grid(row=0, column=0, padx=10, pady=10)

        fecha_desde = DateEntry(frame_filtro, width=12, background='darkblue', foreground='white',
                            borderwidth=2, date_pattern="yyyy-mm-dd")
        fecha_desde.set_date(date.today())
        fecha_desde.grid(row=0, column=1, padx=5)

        # Campo Hasta
        lbl_hasta = tk.Label(frame_filtro, text="Hasta:", font=("sans 14 bold"), bg="#dbe7ed")
        lbl_hasta.grid(row=0, column=2, padx=10)

        fecha_hasta = DateEntry(frame_filtro, width=12, background='darkblue', foreground='white',
                            borderwidth=2, date_pattern="yyyy-mm-dd")
        fecha_hasta.set_date(date.today())
        fecha_hasta.grid(row=0, column=3, padx=5)

        # Botón Reporte
        btn_filtrar = tk.Button(frame_filtro, text="Filtrar", font="sans 14 bold", 
                            command=lambda: filtrar(), bg="#dbe7ed", fg="black")
        btn_filtrar.config(image=imagen_filtrar, compound=LEFT, padx=5, bd=0)
        btn_filtrar.image = imagen_filtrar
        btn_filtrar.place(x=400, y=5, width=100, height=40)

        # Frame para la tabla
        frame_tabla = tk.Frame(top, bg="#c9dbe1")
        frame_tabla.pack(padx=10, pady=(5, 10), fill="both", expand=True)

        # Tabla con encabezado "Ganancias Totales"
        self.tree = ttk.Treeview(frame_tabla, columns=("Ganancias Totales",), show="headings", height=10)
        self.tree.heading("Ganancias Totales", text="Ganancias Totales")
        self.tree.column("Ganancias Totales", anchor="center", width=200)
        self.tree.pack(fill="both", expand=True)

        def filtrar():
            try:
                fecha_ini = fecha_desde.get_date()
                fecha_fin = fecha_hasta.get_date()

                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()                
                cursor.execute("""
                SELECT SUM(total) - SUM(cantidad * costo) as ganancias_totales
                FROM ventas
                WHERE fecha BETWEEN ? AND ?
                """, (fecha_ini, fecha_fin))
                resultado = cursor.fetchone()
                conn.close()

                # Limpiar tabla
                for item in self.tree.get_children():
                    self.tree.delete(item)

                if resultado and resultado[0] is not None:
                    self.tree.insert("", "end", values=(f"${resultado[0]:,.2f}",))
                else:
                    messagebox.showinfo("Sin datos", "No se encontraron ganancias en ese rango de fechas.")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al consultar la base de datos: {e}")

        # Texto explicativo
        lbl_explicacion = tk.Label(top,
            text="El reporte de ganancias equivale a las ventas totales menos el costo\nde los productos",
            font=("Arial", 9, "bold"), bg="#c9dbe1", justify="center")
        lbl_explicacion.pack(pady=(5, 10))

    def reportes_ventas_por_mes(self):
        # Solicitar el año
        año = simpledialog.askstring("Año", "Ingrese el año para filtrar:", parent=self)
        if not año:
            return
        
        try:
            año = int(año)
            
            # Crear la ventana del gráfico
            top = tk.Toplevel(self)
            top.title(f"Ventas por Mes en {año}")
            top.geometry("800x600")
            top.config(bg="white")
            top.resizable(False, False)
            top.transient(self.master)
            top.grab_set()
            
            # Consultar datos de ventas por mes
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strftime('%m', fecha) as mes,
                       SUM(total) as total_ventas
                FROM ventas
                WHERE strftime('%Y', fecha) = ?
                GROUP BY strftime('%m', fecha)
                ORDER BY mes
            """, (str(año),))
            
            resultados = cursor.fetchall()
            conn.close()
            
            # Preparar datos para el gráfico
            meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            valores = [0] * 12  # Inicializar con ceros
            
            # Llenar los valores de ventas
            for mes, total in resultados:
                valores[int(mes)-1] = float(total)
            
            # Crear figura y gráfico
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Crear barras
            bars = ax.bar(range(12), valores, color='skyblue')
            
            # Configurar el gráfico
            ax.set_title(f'Ventas por Mes en {año}', pad=20, fontsize=14)
            ax.set_xlabel('Mes', labelpad=10)
            ax.set_ylabel('Total de Ventas')
            ax.set_xticks(range(12))
            ax.set_xticklabels(meses)
            
            # Agregar los valores sobre las barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:,.2f}',
                       ha='center', va='bottom')
            
            # Ajustar el diseño
            fig.set_facecolor('white')
            ax.set_facecolor('white')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Crear el canvas y agregar el gráfico
            canvas = FigureCanvasTkAgg(fig, master=top)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese un año válido")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al consultar la base de datos: {e}")
    
    def grafico_ganancias_por_mes(self):
        # Solicitar el año
        año = simpledialog.askstring("Año", "Ingrese el año para filtrar:", parent=self)
        if not año:
            return
        
        try:
            año = int(año)
            
            # Crear la ventana del gráfico
            top = tk.Toplevel(self)
            top.title(f" Ventas y Ganancias por Mes en {año}")
            top.geometry("800x600")
            top.config(bg="white")
            top.resizable(False, False)
            top.transient(self.master)
            top.grab_set()
            
            # Consultar datos por mes
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strftime('%m', fecha) as mes,
                       SUM(cantidad * costo) as total_costos,
                       SUM(total) as total_ventas,
                       SUM(total) - SUM(cantidad * costo) as ganancias
                FROM ventas
                WHERE strftime('%Y', fecha) = ?
                GROUP BY strftime('%m', fecha)
                ORDER BY mes
            """, (str(año),))
            
            resultados = cursor.fetchall()
            conn.close()
            
            # Preparar datos para el gráfico
            meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            ventas = [0] * 12
            ganancias = [0] * 12
            
            # Llenar los valores
            for mes, costo, venta, ganancia in resultados:
                index = int(mes)-1
                ventas[index] = float(venta if venta else 0)
                ganancias[index] = float(ganancia if ganancia else 0)
            
            # Crear figura y gráfico
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Posiciones de las barras
            x = range(12)
            width = 0.35
            
            # Crear solo las barras de ventas y ganancias
            bars1 = ax.bar([i - width/2 for i in x], ventas, width, label='Ventas', color='skyblue')
            bars2 = ax.bar([i + width/2 for i in x], ganancias, width, label='Ganancias', color='lightgreen')
            
            # Configurar el gráfico
            ax.set_title(f'Ventas y Ganancias por Mes en {año}', pad=20, fontsize=14)
            ax.set_xlabel('Mes')
            ax.set_ylabel('Total')
            ax.set_xticks(x)
            ax.set_xticklabels(meses)
            
            # Agregar los valores sobre las barras
            def autolabel(bars):
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:  # Solo mostrar valores mayores a 0
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'${height:,.2f}',
                               ha='center', va='bottom', rotation=0,
                               fontsize=8)
            
            autolabel(bars1)
            autolabel(bars2)
            
            # Ajustar el diseño
            ax.legend()
            fig.set_facecolor('white')
            ax.set_facecolor('white')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Crear el canvas y agregar el gráfico
            canvas = FigureCanvasTkAgg(fig, master=top)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese un año válido")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al consultar la base de datos: {e}")    
        
    def mostrar_ventana_exportar(self):
        ventana_exportar = tk.Toplevel(self)
        ventana_exportar.title("Exportar a Excel")
        ventana_exportar.geometry("300x200+200+100")
        ventana_exportar.config(bg="#c9dbe1")
        ventana_exportar.resizable(False, False)
        ventana_exportar.transient(self.master)
        ventana_exportar.grab_set()

        etiqueta = tk.Label(ventana_exportar, text="¿Qué deseas exportar?", font=("Arial", 12), bg="#c9dbe1")
        etiqueta.pack(pady=10)

        btn_inventario = tk.Button(ventana_exportar, text="Inventario", width=20, 
                                 command=lambda: self.exportar_excel("inventario", ventana_exportar))
        btn_inventario.pack(pady=5)

        btn_ventas = tk.Button(ventana_exportar, text="Ventas por mes", width=20, 
                              command=lambda: self.exportar_excel("ventas", ventana_exportar))
        btn_ventas.pack(pady=5)
    
    def exportar_excel(self, tipo, ventana,):
        archivo = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Archivos Excel", "*.xlsx")])
        if not archivo:
            return

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            libro = Workbook()
            hoja = libro.active

            if tipo =="inventario":
                hoja.title = "Inventario"
                cursor.execute("SELECT id, articulo, precio, costo, codigo,stock, stock_minimo, sucursal   FROM articulos")
                datos = cursor.fetchall()
                hoja.append(["ID", "Articulo", "Precio", "Costo", "Codigo","Stock", "Stock minimo", "Sucursal"])
            elif tipo=="ventas":
                hoja.title = "Ventas"
                cursor.execute("""
                    SELECT strftime('%Y-%m', fecha) as mes, SUM(total) as total_ventas
                    FROM ventas
                    GROUP BY mes
                """)
                datos = cursor.fetchall()
                hoja.append(["Mes", "Total Ventas"])

            for fila in datos:
                hoja.append(fila)
            
            libro.save(archivo)
            conn.close()
            ventana.destroy()
            messagebox.showinfo("Éxito", f"Datos exportados a {archivo} exitosamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}")

