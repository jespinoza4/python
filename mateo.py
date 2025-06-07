import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Frame, Canvas
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from fpdf import FPDF
from datetime import datetime, timedelta
import os
import calendar
import random
import math
from PIL import Image, ImageTk
import threading
import time

class SolarSystemCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Seguimiento Solar Profesional v7.0")
        self.root.geometry("1400x950")
        
        # Variables de entrada
        self.load_power = tk.DoubleVar(value=100)  # Watts
        self.operating_hours = tk.DoubleVar(value=24)  # Horas
        self.sunlight_hours = tk.DoubleVar(value=5)  # Horas de sol pico
        self.autonomy_days = tk.DoubleVar(value=1)  # Días de autonomía
        self.panel_power = tk.DoubleVar(value=450)  # Watts por panel
        self.battery_capacity = tk.DoubleVar(value=100)  # Ah
        self.battery_voltage = tk.DoubleVar(value=12)  # Voltios
        self.dod_limit = tk.DoubleVar(value=50)  # Profundidad de descarga (%)
        self.location_lat = tk.DoubleVar(value=40.0)  # Latitud
        self.location_lon = tk.DoubleVar(value=-3.0)  # Longitud
        
        # Variables para control de seguimiento
        self.azimuth_angle = tk.DoubleVar(value=180)  # Ángulo azimutal (0-360)
        self.elevation_angle = tk.DoubleVar(value=45)  # Ángulo de elevación (0-90)
        self.tracking_speed = tk.DoubleVar(value=5)    # Velocidad de seguimiento
        self.motor_status = tk.StringVar(value="Detenido")  # Estado del motor
        
        # Datos de radiación solar (simulados)
        self.solar_radiation_data = {}
        self.battery_soc_data = {}
        
        # Datos para monitoreo de baterías
        self.battery_status = [
            {"id": 1, "soc": 85, "voltage": 12.8, "current": 5.2, "temp": 25, "connected": True},
            {"id": 2, "soc": 78, "voltage": 12.6, "current": 4.8, "temp": 26, "connected": True},
            {"id": 3, "soc": 92, "voltage": 13.1, "current": 5.5, "temp": 24, "connected": True},
            {"id": 4, "soc": 65, "voltage": 12.3, "current": 3.9, "temp": 27, "connected": True}
        ]
        self.monitoring_active = False
        
        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Crear pestañas
        self.calc_tab = ttk.Frame(self.notebook)
        self.sim_tab = ttk.Frame(self.notebook)
        self.calendar_tab = ttk.Frame(self.notebook)
        self.tracking_tab = ttk.Frame(self.notebook)
        self.battery_tab = ttk.Frame(self.notebook)  # Nueva pestaña
        
        self.notebook.add(self.calc_tab, text="Cálculo del Sistema")
        self.notebook.add(self.sim_tab, text="Simulación de Carga")
        self.notebook.add(self.calendar_tab, text="Calendario de Operación")
        self.notebook.add(self.tracking_tab, text="Control de Seguimiento")
        self.notebook.add(self.battery_tab, text="Monitoreo de Baterías")  # Nueva pestaña
        
        # Inicializar interfaces
        self.create_calculation_tab()
        self.create_simulation_tab()
        self.create_calendar_tab()
        self.create_tracking_tab()
        self.create_battery_monitor_tab()  # Nueva función
        
        # Cargar imágenes
        self.load_images()
        
        # Generar datos iniciales
        self.generate_initial_data()
    
    def generate_initial_data(self):
        """Genera datos simulados de radiación solar y estado de carga"""
        current_year = datetime.now().year
        for month in range(1, 13):
            days_in_month = calendar.monthrange(current_year, month)[1]
            month_key = f"{current_year}-{month:02d}"
            
            # Datos de radiación solar
            self.solar_radiation_data[month_key] = {}
            base_radiation = 4.0 + (month - 6) * 0.5  # Mayor radiación en verano
            
            # Datos de estado de carga de baterías
            self.battery_soc_data[month_key] = {}
            base_soc = 70.0
            
            for day in range(1, days_in_month + 1):
                # Radiación solar: base + variación aleatoria
                radiation = max(1.0, min(8.0, base_radiation + random.uniform(-1.5, 1.5)))
                self.solar_radiation_data[month_key][day] = round(radiation, 1)
                
                # Estado de carga: depende de la radiación solar
                soc = max(30, min(100, base_soc + (radiation - 4.0) * 5))
                self.battery_soc_data[month_key][day] = round(soc)
    
    def load_images(self):
        try:
            # Crear imágenes en tiempo real
            self.motor_img = self.create_motor_image()
            self.solar_panel_img = self.create_panel_image()
            self.piston_img = self.create_piston_image()
            self.battery_img = self.create_battery_image()
        except Exception as e:
            messagebox.showwarning("Imágenes", f"No se pudieron cargar imágenes: {str(e)}")
            self.motor_img = None
            self.solar_panel_img = None
            self.piston_img = None
            self.battery_img = None
    
    def create_motor_image(self):
        img = Image.new('RGBA', (60, 40), (0, 0, 0, 0))
        pixels = img.load()
        
        # Cuerpo del motor
        for i in range(10, 50):
            for j in range(10, 30):
                pixels[i, j] = (100, 100, 100, 255)
        
        # Eje del motor
        for i in range(50, 55):
            for j in range(15, 25):
                pixels[i, j] = (150, 150, 150, 255)
        
        # Terminales
        for i in range(15, 45):
            for j in range(5, 10):
                pixels[i, j] = (200, 0, 0, 255)
            for j in range(30, 35):
                pixels[i, j] = (0, 0, 200, 255)
        
        return ImageTk.PhotoImage(img)
    
    def create_panel_image(self):
        img = Image.new('RGBA', (100, 80), (0, 0, 0, 0))
        pixels = img.load()
        
        # Marco del panel
        for i in range(0, 100):
            for j in range(0, 10):
                pixels[i, j] = (50, 50, 50, 255)
            for j in range(70, 80):
                pixels[i, j] = (50, 50, 50, 255)
        for i in range(0, 10):
            for j in range(0, 80):
                pixels[i, j] = (50, 50, 50, 255)
        for i in range(90, 100):
            for j in range(0, 80):
                pixels[i, j] = (50, 50, 50, 255)
        
        # Celdas solares
        for cell_x in range(0, 9):
            for cell_y in range(0, 6):
                x_start = 15 + cell_x * 8
                y_start = 15 + cell_y * 10
                for i in range(x_start, x_start + 6):
                    for j in range(y_start, y_start + 8):
                        pixels[i, j] = (0, 100, 200, 255)
        
        return ImageTk.PhotoImage(img)
    
    def create_piston_image(self):
        img = Image.new('RGBA', (30, 100), (0, 0, 0, 0))
        pixels = img.load()
        
        # Cilindro
        for i in range(5, 25):
            for j in range(0, 100):
                pixels[i, j] = (120, 120, 120, 255)
        
        # Vástago
        for i in range(10, 20):
            for j in range(40, 100):
                pixels[i, j] = (200, 200, 200, 255)
        
        return ImageTk.PhotoImage(img)
    
    def create_battery_image(self):
        img = Image.new('RGBA', (80, 40), (0, 0, 0, 0))
        pixels = img.load()
        
        # Cuerpo de la batería
        for i in range(10, 70):
            for j in range(5, 35):
                pixels[i, j] = (100, 100, 100, 255)
        
        # Terminal positiva
        for i in range(35, 45):
            for j in range(0, 5):
                pixels[i, j] = (200, 200, 200, 255)
        
        # Terminal negativa
        for i in range(55, 65):
            for j in range(0, 5):
                pixels[i, j] = (200, 200, 200, 255)
        
        # Etiqueta
        for i in range(20, 60):
            for j in range(15, 25):
                pixels[i, j] = (50, 150, 50, 255)
        
        return ImageTk.PhotoImage(img)
    
    def create_calculation_tab(self):
        main_frame = ttk.Frame(self.calc_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        input_frame = ttk.LabelFrame(main_frame, text="Parámetros del Sistema", padding="10")
        input_frame.pack(fill='x', padx=5, pady=5)
        
        entries = [
            ("Potencia de Carga (W):", self.load_power),
            ("Horas de Operación/Día:", self.operating_hours),
            ("Horas de Sol Pico:", self.sunlight_hours),
            ("Días de Autonomía:", self.autonomy_days),
            ("Potencia por Panel (W):", self.panel_power),
            ("Capacidad Batería (Ah):", self.battery_capacity),
            ("Voltaje Batería (V):", self.battery_voltage),
            ("Profundidad de Descarga (%):", self.dod_limit)
        ]
        
        for i, (label, var) in enumerate(entries):
            row_frame = ttk.Frame(input_frame)
            row_frame.grid(row=i, column=0, sticky='ew', pady=2)
            ttk.Label(row_frame, text=label, width=25).pack(side='left')
            ttk.Entry(row_frame, textvariable=var, width=10).pack(side='right')
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=10)
        ttk.Button(btn_frame, text="Calcular Sistema", command=self.calculate_system).pack(side='left', padx=5)
        
        self.result_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        self.result_frame.pack(fill='x', padx=5, pady=5)
        
        graph_container = ttk.Frame(main_frame)
        graph_container.pack(fill='both', expand=True, pady=10)
        
        self.graph_frame = ttk.Frame(graph_container)
        self.graph_frame.pack(fill='both', expand=True)
        
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill='x', pady=10)
        
        ttk.Button(export_frame, text="Generar Reporte Excel", command=self.generate_excel).pack(side='left', padx=5)
        ttk.Button(export_frame, text="Generar Reporte PDF", command=self.generate_pdf).pack(side='left', padx=5)
    
    def create_simulation_tab(self):
        main_frame = ttk.Frame(self.sim_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        control_frame = ttk.LabelFrame(main_frame, text="Control de Simulación", padding="10")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        params_frame = ttk.Frame(control_frame)
        params_frame.pack(fill='x', pady=5)
        
        ttk.Label(params_frame, text="Latitud:").grid(row=0, column=0, padx=5)
        ttk.Entry(params_frame, textvariable=self.location_lat, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(params_frame, text="Longitud:").grid(row=0, column=2, padx=5)
        ttk.Entry(params_frame, textvariable=self.location_lon, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(params_frame, text="Duración (días):").grid(row=0, column=4, padx=5)
        self.sim_days = tk.IntVar(value=7)
        ttk.Entry(params_frame, textvariable=self.sim_days, width=5).grid(row=0, column=5, padx=5)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill='x', pady=10)
        ttk.Button(btn_frame, text="Simular Carga/Descarga", command=self.run_simulation).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Mostrar Curvas", command=self.show_curves).pack(side='left', padx=5)
        
        sim_graph_frame = ttk.Frame(main_frame)
        sim_graph_frame.pack(fill='both', expand=True, pady=10)
        
        left_frame = ttk.Frame(sim_graph_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        right_frame = ttk.Frame(sim_graph_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        self.solar_traj_frame = ttk.LabelFrame(left_frame, text="Trayectoria Solar")
        self.solar_traj_frame.pack(fill='both', expand=True, pady=5)
        
        self.charge_discharge_frame = ttk.LabelFrame(left_frame, text="Estado de Carga de Baterías")
        self.charge_discharge_frame.pack(fill='both', expand=True, pady=5)
        
        self.generation_consumption_frame = ttk.LabelFrame(right_frame, text="Generación y Consumo")
        self.generation_consumption_frame.pack(fill='both', expand=True, pady=5)
        
        self.operation_hours_frame = ttk.LabelFrame(right_frame, text="Horas de Operación")
        self.operation_hours_frame.pack(fill='both', expand=True, pady=5)
    
    def create_calendar_tab(self):
        main_frame = ttk.Frame(self.calendar_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        control_frame = ttk.LabelFrame(main_frame, text="Control del Calendario", padding="10")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(control_frame, text="Mes:").pack(side='left', padx=5)
        self.month_var = tk.StringVar()
        months = [calendar.month_name[i] for i in range(1, 13)]
        month_combo = ttk.Combobox(control_frame, textvariable=self.month_var, values=months, width=10)
        month_combo.current(datetime.now().month - 1)
        month_combo.pack(side='left', padx=5)
        
        ttk.Label(control_frame, text="Año:").pack(side='left', padx=5)
        self.year_var = tk.IntVar(value=datetime.now().year)
        year_spin = ttk.Spinbox(control_frame, from_=2020, to=2030, textvariable=self.year_var, width=8)
        year_spin.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Generar Calendario", command=self.generate_calendar).pack(side='left', padx=10)
        ttk.Button(control_frame, text="Exportar Datos", command=self.export_calendar_data).pack(side='left', padx=10)
        
        # Frame para estadísticas
        stats_frame = ttk.Frame(control_frame)
        stats_frame.pack(side='right', padx=10)
        
        self.avg_radiation_var = tk.StringVar(value="Radiación promedio: --")
        self.avg_soc_var = tk.StringVar(value="SOC promedio: --")
        self.min_radiation_var = tk.StringVar(value="Mínima radiación: --")
        self.max_radiation_var = tk.StringVar(value="Máxima radiación: --")
        
        ttk.Label(stats_frame, textvariable=self.avg_radiation_var).pack(anchor='e')
        ttk.Label(stats_frame, textvariable=self.avg_soc_var).pack(anchor='e')
        ttk.Label(stats_frame, textvariable=self.min_radiation_var).pack(anchor='e')
        ttk.Label(stats_frame, textvariable=self.max_radiation_var).pack(anchor='e')
        
        calendar_frame = ttk.LabelFrame(main_frame, text="Calendario de Operación", padding="10")
        calendar_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.canvas = Canvas(calendar_frame, bg='white')
        self.scrollbar = ttk.Scrollbar(calendar_frame, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        
        # Generar calendario inicial
        self.generate_calendar()
    
    def export_calendar_data(self):
        """Exporta los datos del calendario a un archivo CSV"""
        month_name = self.month_var.get()
        year = self.year_var.get()
        month_num = list(calendar.month_name).index(month_name)
        month_key = f"{year}-{month_num:02d}"
        
        if month_key not in self.solar_radiation_data:
            messagebox.showinfo("Información", "No hay datos para el mes seleccionado")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w') as f:
                f.write("Día,Radiación Solar (kWh/m²),Estado de Carga (%)\n")
                for day in sorted(self.solar_radiation_data[month_key].keys()):
                    radiation = self.solar_radiation_data[month_key][day]
                    soc = self.battery_soc_data[month_key][day]
                    f.write(f"{day},{radiation},{soc}\n")
            
            messagebox.showinfo("Éxito", f"Datos exportados a:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar los datos:\n{str(e)}")
    
    def create_tracking_tab(self):
        main_frame = ttk.Frame(self.tracking_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        control_frame = ttk.LabelFrame(main_frame, text="Control de Seguimiento Solar", padding="10")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        position_frame = ttk.Frame(control_frame)
        position_frame.pack(fill='x', pady=5)
        
        ttk.Label(position_frame, text="Ángulo Azimutal (0-360°):").grid(row=0, column=0, padx=5, sticky='w')
        self.azimuth_scale = ttk.Scale(position_frame, from_=0, to=360, 
                                      variable=self.azimuth_angle, 
                                      command=self.update_tracking,
                                      length=300)
        self.azimuth_scale.grid(row=0, column=1, padx=5)
        self.azimuth_label = ttk.Label(position_frame, text=f"{self.azimuth_angle.get():.1f}°", font=("Arial", 10, "bold"))
        self.azimuth_label.grid(row=0, column=2, padx=5)
        
        ttk.Label(position_frame, text="Ángulo de Elevación (0-90°):").grid(row=1, column=0, padx=5, sticky='w')
        self.elevation_scale = ttk.Scale(position_frame, from_=0, to=90, 
                                        variable=self.elevation_angle, 
                                        command=self.update_tracking,
                                        length=300)
        self.elevation_scale.grid(row=1, column=1, padx=5)
        self.elevation_label = ttk.Label(position_frame, text=f"{self.elevation_angle.get():.1f}°", font=("Arial", 10, "bold"))
        self.elevation_label.grid(row=1, column=2, padx=5)
        
        ttk.Label(position_frame, text="Velocidad de Seguimiento:").grid(row=2, column=0, padx=5, sticky='w')
        ttk.Scale(position_frame, from_=1, to=10, 
                 variable=self.tracking_speed, 
                 length=300).grid(row=2, column=1, padx=5)
        
        ttk.Label(position_frame, text="Estado del Motor:").grid(row=3, column=0, padx=5, sticky='w')
        motor_status_label = ttk.Label(position_frame, textvariable=self.motor_status, 
                                     font=("Arial", 10, "bold"), foreground="blue")
        motor_status_label.grid(row=3, column=1, padx=5, sticky='w')
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="Posición Inicial", 
                  command=lambda: self.set_tracking_position(180, 45)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Seguir Sol", 
                  command=self.track_sun).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Optimizar Ángulo", 
                  command=self.optimize_angle).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Detener Motores", 
                  command=lambda: self.motor_status.set("Detenido")).pack(side='left', padx=5)
        
        # Nuevo diseño con dos ventanas tipo radar
        radar_frame = ttk.Frame(main_frame)
        radar_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Frame para el radar de azimut
        self.azimuth_radar_frame = ttk.LabelFrame(radar_frame, text="Azimut (0-360°)")
        self.azimuth_radar_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        # Frame para el radar de elevación
        self.elevation_radar_frame = ttk.LabelFrame(radar_frame, text="Elevación (0-90°)")
        self.elevation_radar_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Inicializar los radares
        self.azimuth_fig = Figure(figsize=(4, 4), dpi=80)
        self.azimuth_ax = self.azimuth_fig.add_subplot(111, polar=True)
        self.azimuth_canvas = FigureCanvasTkAgg(self.azimuth_fig, master=self.azimuth_radar_frame)
        self.azimuth_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        self.elevation_fig = Figure(figsize=(4, 4), dpi=80)
        self.elevation_ax = self.elevation_fig.add_subplot(111, polar=True)
        self.elevation_canvas = FigureCanvasTkAgg(self.elevation_fig, master=self.elevation_radar_frame)
        self.elevation_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Dibujar radares iniciales
        self.draw_azimuth_radar()
        self.draw_elevation_radar()
    
    def create_battery_monitor_tab(self):
        main_frame = ttk.Frame(self.battery_tab, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Frame para controles
        control_frame = ttk.LabelFrame(main_frame, text="Control de Baterías", padding="10")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="Iniciar Monitoreo", 
                  command=self.start_monitoring).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Detener Monitoreo", 
                  command=self.stop_monitoring).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Forzar Carga", 
                  command=self.force_charging).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Forzar Descarga", 
                  command=self.force_discharging).pack(side='left', padx=5)
        
        # Frame para estado del sistema
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill='x', pady=5)
        
        self.system_status_var = tk.StringVar(value="Sistema: DESCONECTADO")
        ttk.Label(status_frame, textvariable=self.system_status_var, 
                 font=("Arial", 10, "bold"), foreground="red").pack(side='left', padx=5)
        
        self.charging_status_var = tk.StringVar(value="Estado carga: DETENIDO")
        ttk.Label(status_frame, textvariable=self.charging_status_var, 
                 font=("Arial", 10, "bold"), foreground="blue").pack(side='left', padx=5)
        
        # Frame para gráficos y datos
        data_frame = ttk.Frame(main_frame)
        data_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Frame para gráfico de carga
        chart_frame = ttk.LabelFrame(data_frame, text="Estado de Carga")
        chart_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        self.battery_fig = Figure(figsize=(6, 4), dpi=80)
        self.battery_ax = self.battery_fig.add_subplot(111)
        self.battery_canvas = FigureCanvasTkAgg(self.battery_fig, master=chart_frame)
        self.battery_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Frame para datos detallados
        details_frame = ttk.LabelFrame(data_frame, text="Datos de Baterías")
        details_frame.pack(side='right', fill='both', padx=5, pady=5)
        
        # Crear tabla para mostrar datos de baterías
        columns = ("ID", "SOC", "Voltaje", "Corriente", "Temp", "Estado", "Control")
        self.battery_tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=4)
        
        for col in columns:
            self.battery_tree.heading(col, text=col)
            self.battery_tree.column(col, width=80, anchor='center')
        
        self.battery_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Agregar barras de desplazamiento
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.battery_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.battery_tree.configure(yscrollcommand=scrollbar.set)
        
        # Actualizar datos iniciales
        self.update_battery_data()
        
        # Crear gráfico inicial
        self.plot_battery_status()
    
    def start_monitoring(self):
        if not self.monitoring_active:
            self.monitoring_active = True
            self.system_status_var.set("Sistema: CONECTADO")
            self.charging_status_var.set("Estado carga: MONITOREANDO")
            threading.Thread(target=self.monitoring_loop, daemon=True).start()
    
    def stop_monitoring(self):
        self.monitoring_active = False
        self.system_status_var.set("Sistema: DESCONECTADO")
        self.charging_status_var.set("Estado carga: DETENIDO")
    
    def force_charging(self):
        self.charging_status_var.set("Estado carga: CARGANDO FORZADO")
        for battery in self.battery_status:
            if battery['connected']:
                battery['soc'] = min(100, battery['soc'] + 5)
        self.update_battery_data()
        self.plot_battery_status()
    
    def force_discharging(self):
        self.charging_status_var.set("Estado carga: DESCARGANDO FORZADO")
        for battery in self.battery_status:
            if battery['connected']:
                battery['soc'] = max(0, battery['soc'] - 5)
        self.update_battery_data()
        self.plot_battery_status()
    
    def monitoring_loop(self):
        while self.monitoring_active:
            # Simular cambios en las baterías
            for battery in self.battery_status:
                if battery['connected']:
                    # Cambio aleatorio en el estado de carga
                    change = random.uniform(-1.5, 2.5)
                    battery['soc'] = max(0, min(100, battery['soc'] + change))
                    
                    # Actualizar otros parámetros
                    battery['voltage'] = 11.5 + (battery['soc'] / 100) * 2.5
                    battery['current'] = random.uniform(3.0, 6.0)
                    battery['temp'] = random.uniform(20, 30)
            
            # Actualizar interfaz
            self.root.after(0, self.update_battery_data)
            self.root.after(0, self.plot_battery_status)
            
            # Esperar 1 segundo
            time.sleep(1)
    
    def toggle_battery_connection(self, battery_id):
        for battery in self.battery_status:
            if battery['id'] == battery_id:
                battery['connected'] = not battery['connected']
                break
        self.update_battery_data()
    
    def update_battery_data(self):
        # Limpiar tabla
        for item in self.battery_tree.get_children():
            self.battery_tree.delete(item)
        
        # Agregar datos actualizados
        for battery in self.battery_status:
            status = "CONECTADA" if battery['connected'] else "DESCONECTADA"
            status_color = "green" if battery['connected'] else "red"
            
            # Crear botón para conectar/desconectar
            btn_text = "Desconectar" if battery['connected'] else "Conectar"
            btn_command = lambda bid=battery['id']: self.toggle_battery_connection(bid)
            
            # Insertar datos en la tabla
            self.battery_tree.insert("", "end", values=(
                battery['id'],
                f"{battery['soc']:.1f}%",
                f"{battery['voltage']:.2f}V",
                f"{battery['current']:.2f}A",
                f"{battery['temp']:.1f}°C",
                status,
                btn_text
            ))
            
            # Configurar botón en la última columna
            self.battery_tree.bind('<ButtonRelease-1>', self.handle_battery_btn_click)
    
    def handle_battery_btn_click(self, event):
        region = self.battery_tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.battery_tree.identify_column(event.x)
            if column == "#7":  # Última columna (Control)
                item = self.battery_tree.identify_row(event.y)
                values = self.battery_tree.item(item, "values")
                battery_id = int(values[0])
                self.toggle_battery_connection(battery_id)
    
    def plot_battery_status(self):
        self.battery_ax.clear()
        
        # Preparar datos para el gráfico
        battery_ids = [b['id'] for b in self.battery_status]
        soc_values = [b['soc'] for b in self.battery_status]
        colors = ['green' if b['connected'] else 'red' for b in self.battery_status]
        
        # Crear gráfico de barras
        bars = self.battery_ax.bar(battery_ids, soc_values, color=colors)
        
        # Agregar etiquetas
        for bar in bars:
            height = bar.get_height()
            self.battery_ax.annotate(f'{height:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom')
        
        # Configurar el gráfico
        self.battery_ax.set_title('Estado de Carga de Baterías')
        self.battery_ax.set_xlabel('ID de Batería')
        self.battery_ax.set_ylabel('Estado de Carga (%)')
        self.battery_ax.set_ylim(0, 100)
        self.battery_ax.set_xticks(battery_ids)
        self.battery_ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Actualizar canvas
        self.battery_canvas.draw()
    
    def draw_azimuth_radar(self):
        self.azimuth_ax.clear()
        
        # Configurar el radar de azimut
        self.azimuth_ax.set_theta_zero_location('N')
        self.azimuth_ax.set_theta_direction(-1)
        self.azimuth_ax.set_ylim(0, 1)
        self.azimuth_ax.set_yticks([])
        
        # Ángulos principales (N, E, S, O)
        angles = [0, 90, 180, 270]
        labels = ['N', 'E', 'S', 'O']
        for angle, label in zip(angles, labels):
            self.azimuth_ax.text(np.radians(angle), 1.1, label, 
                                ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Dibujar ángulo actual
        current_az = self.azimuth_angle.get()
        self.azimuth_ax.plot([0, np.radians(current_az)], [0, 1], 'r-', linewidth=2)
        self.azimuth_ax.fill_between([0, np.radians(current_az)], 0, 1, color='red', alpha=0.2)
        
        # Punto en la posición actual
        self.azimuth_ax.plot(np.radians(current_az), 1, 'ro', markersize=8)
        
        # Texto con el valor numérico
        self.azimuth_ax.text(np.radians(180), 0.5, f"{current_az:.1f}°", 
                           ha='center', va='center', fontsize=14, fontweight='bold', color='red')
        
        # Líneas de guía
        for angle in range(0, 360, 30):
            self.azimuth_ax.plot([np.radians(angle), np.radians(angle)], [0, 1], 
                               'gray', linewidth=0.5, alpha=0.5)
        
        self.azimuth_canvas.draw()
    
    def draw_elevation_radar(self):
        self.elevation_ax.clear()
        
        # Configurar el radar de elevación (solo semicírculo)
        self.elevation_ax.set_theta_zero_location('N')
        self.elevation_ax.set_theta_direction(-1)
        self.elevation_ax.set_thetamin(0)
        self.elevation_ax.set_thetamax(180)
        self.elevation_ax.set_ylim(0, 1)
        self.elevation_ax.set_yticks([])
        
        # Etiquetas para los ángulos principales
        angles = [0, 45, 90]
        labels = ['90°', '45°', '0°']
        for angle, label in zip(angles, labels):
            self.elevation_ax.text(np.radians(angle), 1.1, label, 
                                 ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Dibujar ángulo actual (convertir elevación a ángulo polar)
        current_el = self.elevation_angle.get()
        polar_el = 90 - current_el  # Convertir elevación a ángulo en el radar
        self.elevation_ax.plot([0, np.radians(polar_el)], [0, 1], 'b-', linewidth=2)
        self.elevation_ax.fill_between([0, np.radians(polar_el)], 0, 1, color='blue', alpha=0.2)
        
        # Punto en la posición actual
        self.elevation_ax.plot(np.radians(polar_el), 1, 'bo', markersize=8)
        
        # Texto con el valor numérico
        self.elevation_ax.text(np.radians(90), 0.5, f"{current_el:.1f}°", 
                             ha='center', va='center', fontsize=14, fontweight='bold', color='blue')
        
        # Líneas de guía
        for angle in range(0, 181, 15):
            self.elevation_ax.plot([np.radians(angle), np.radians(angle)], [0, 1], 
                                 'gray', linewidth=0.5, alpha=0.5)
        
        self.elevation_canvas.draw()
    
    def update_tracking(self, event=None):
        self.azimuth_label.config(text=f"{self.azimuth_angle.get():.1f}°")
        self.elevation_label.config(text=f"{self.elevation_angle.get():.1f}°")
        self.motor_status.set("Moviendo motores...")
        self.draw_azimuth_radar()
        self.draw_elevation_radar()
        self.root.after(500, lambda: self.motor_status.set("Motores en posición"))
    
    def set_tracking_position(self, az, el):
        self.azimuth_angle.set(az)
        self.elevation_angle.set(el)
        self.motor_status.set("Moviendo a posición inicial...")
        self.update_tracking()
    
    def track_sun(self):
        self.motor_status.set("Iniciando seguimiento solar...")
        self.root.update()
        
        hour = datetime.now().hour
        solar_az = 180 + (hour - 12) * 15
        solar_el = max(10, 90 - abs(hour - 12) * 10)
        
        current_az = self.azimuth_angle.get()
        current_el = self.elevation_angle.get()
        
        steps = 20
        speed = self.tracking_speed.get()
        
        for i in range(steps):
            new_az = current_az + (solar_az - current_az) * (i+1)/steps
            new_el = current_el + (solar_el - current_el) * (i+1)/steps
            self.azimuth_angle.set(new_az)
            self.elevation_angle.set(new_el)
            self.motor_status.set(f"Moviendo motores... {int((i+1)/steps*100)}%")
            self.update_tracking()
            self.root.update()
            self.root.after(int(100/speed))
        
        self.motor_status.set("Seguimiento solar completado")
    
    def optimize_angle(self):
        self.motor_status.set("Calculando ángulo óptimo...")
        self.root.update()
        
        hour = datetime.now().hour
        month = datetime.now().month
        
        optimal_az = 180 + (hour - 12) * 15
        optimal_el = max(15, 90 - abs(month - 6) * 5 - abs(hour - 12) * 8)
        
        self.set_tracking_position(optimal_az, optimal_el)
        self.motor_status.set(f"Ángulo optimizado: Az={optimal_az:.1f}°, El={optimal_el:.1f}°")
    
    def calculate_system(self):
        try:
            if any(var.get() <= 0 for var in [self.load_power, self.operating_hours, self.sunlight_hours, 
                                            self.panel_power, self.battery_capacity, self.battery_voltage]):
                raise ValueError("Todos los valores deben ser positivos")
            
            if not (0 < self.dod_limit.get() <= 100):
                raise ValueError("La profundidad de descarga debe estar entre 0% y 100%")
            
            daily_energy = self.load_power.get() * self.operating_hours.get()
            total_energy = daily_energy * self.autonomy_days.get()
            
            panel_energy = self.panel_power.get() * self.sunlight_hours.get()
            num_panels = np.ceil(daily_energy / panel_energy)
            
            usable_battery_energy = (self.battery_capacity.get() * self.battery_voltage.get()) * (self.dod_limit.get() / 100)
            num_batteries = np.ceil(total_energy / usable_battery_energy)
            
            for widget in self.result_frame.winfo_children():
                widget.destroy()
                
            ttk.Label(self.result_frame, text=f"Energía Diaria Requerida: {daily_energy:.2f} Wh").pack(anchor='w')
            ttk.Label(self.result_frame, text=f"Paneles Necesarios: {int(num_panels)}").pack(anchor='w')
            ttk.Label(self.result_frame, text=f"Baterías Necesarias: {int(num_batteries)}").pack(anchor='w')
            
            self.plot_graphs(daily_energy, num_panels, num_batteries)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en los cálculos: {str(e)}")
    
    def plot_graphs(self, daily_energy, num_panels, num_batteries):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        fig = Figure(figsize=(10, 4), dpi=100)
        
        ax1 = fig.add_subplot(121)
        ax1.bar(["Consumo", "Generación"], 
               [daily_energy, num_panels * self.panel_power.get() * self.sunlight_hours.get()],
               color=["red", "green"])
        ax1.set_title("Balance Energético Diario")
        ax1.set_ylabel("Wh")
        
        ax2 = fig.add_subplot(122)
        days = np.arange(1, int(self.autonomy_days.get()) + 1)
        required_energy = [daily_energy * d for d in days]
        available_energy = [num_batteries * (self.battery_capacity.get() * self.battery_voltage.get()) * (self.dod_limit.get() / 100)] * len(days)
        
        ax2.plot(days, required_energy, label="Energía Requerida")
        ax2.plot(days, available_energy, label="Energía Disponible", linestyle="--")
        ax2.set_title("Autonomía del Sistema")
        ax2.set_xlabel("Días")
        ax2.set_ylabel("Wh")
        ax2.legend()
        
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        self.current_figure = fig
    
    def run_simulation(self):
        try:
            days = self.sim_days.get()
            lat = self.location_lat.get()
            lon = self.location_lon.get()
            
            hours = np.arange(0, 24 * days, 0.25)
            
            solar_intensity = np.exp(-(hours % 24 - 12)**2 / 8) * (1 + 0.1 * np.sin(2 * np.pi * hours / (24 * 7)))
            
            consumption = self.load_power.get() * (0.7 + 0.3 * np.sin(2 * np.pi * hours / 24))
            
            battery_capacity = self.battery_capacity.get() * self.battery_voltage.get() * 2
            soc = np.zeros_like(hours)
            soc[0] = battery_capacity * 0.5
            
            generation = solar_intensity * self.panel_power.get() * 2
            
            for i in range(1, len(hours)):
                net_energy = generation[i] * 0.25 - consumption[i] * 0.25
                soc[i] = soc[i-1] + net_energy
                soc[i] = max(battery_capacity * 0.2, min(soc[i], battery_capacity))
            
            operation = np.where(soc > battery_capacity * 0.25, 1, 0)
            
            self.sim_data = {
                'hours': hours,
                'solar_intensity': solar_intensity,
                'generation': generation,
                'consumption': consumption,
                'soc': soc / battery_capacity * 100,
                'operation': operation
            }
            
            self.update_simulation_plots()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en la simulación: {str(e)}")
    
    def update_simulation_plots(self):
        for frame in [self.solar_traj_frame, self.charge_discharge_frame, 
                     self.generation_consumption_frame, self.operation_hours_frame]:
            for widget in frame.winfo_children():
                widget.destroy()
        
        data = self.sim_data
        days = self.sim_days.get()
        
        fig1 = Figure(figsize=(5, 3), dpi=80)
        ax1 = fig1.add_subplot(111)
        
        hours_day = np.linspace(0, 24, 96)
        solar_angle = 90 * np.sin(np.pi * (hours_day - 6) / 12)
        solar_angle = np.where(solar_angle < 0, 0, solar_angle)
        
        ax1.plot(hours_day, solar_angle, 'r-')
        ax1.fill_between(hours_day, solar_angle, 0, color='yellow', alpha=0.3)
        ax1.set_title("Trayectoria Solar")
        ax1.set_xlabel("Hora del Día")
        ax1.set_ylabel("Ángulo Solar (°)")
        ax1.set_xlim(0, 24)
        ax1.set_ylim(0, 100)
        ax1.grid(True)
        
        canvas1 = FigureCanvasTkAgg(fig1, master=self.solar_traj_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill='both', expand=True)
        
        fig2 = Figure(figsize=(5, 3), dpi=80)
        ax2 = fig2.add_subplot(111)
        
        ax2.plot(data['hours'], data['soc'], 'b-')
        ax2.set_title("Estado de Carga de Baterías")
        ax2.set_xlabel("Horas")
        ax2.set_ylabel("SOC (%)")
        ax2.set_xlim(0, 24 * days)
        ax2.set_ylim(0, 100)
        ax2.grid(True)
        ax2.axhline(y=self.dod_limit.get(), color='r', linestyle='--', label='Límite DoD')
        ax2.legend()
        
        canvas2 = FigureCanvasTkAgg(fig2, master=self.charge_discharge_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill='both', expand=True)
        
        fig3 = Figure(figsize=(5, 3), dpi=80)
        ax3 = fig3.add_subplot(111)
        
        ax3.plot(data['hours'], data['generation'], 'g-', label='Generación')
        ax3.plot(data['hours'], data['consumption'], 'r-', label='Consumo')
        ax3.set_title("Generación y Consumo")
        ax3.set_xlabel("Horas")
        ax3.set_ylabel("Potencia (W)")
        ax3.set_xlim(0, 24 * days)
        ax3.grid(True)
        ax3.legend()
        
        canvas3 = FigureCanvasTkAgg(fig3, master=self.generation_consumption_frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack(fill='both', expand=True)
        
        fig4 = Figure(figsize=(5, 3), dpi=80)
        ax4 = fig4.add_subplot(111)
        
        operation_hours = [np.sum(data['operation'][i*96:(i+1)*96]) * 0.25 for i in range(days)]
        
        ax4.bar(range(days), operation_hours, color='blue')
        ax4.set_title("Horas de Operación Diarias")
        ax4.set_xlabel("Día")
        ax4.set_ylabel("Horas")
        ax4.set_ylim(0, 24)
        ax4.grid(True)
        
        canvas4 = FigureCanvasTkAgg(fig4, master=self.operation_hours_frame)
        canvas4.draw()
        canvas4.get_tk_widget().pack(fill='both', expand=True)
    
    def show_curves(self):
        if not hasattr(self, 'sim_data'):
            messagebox.showinfo("Información", "Primero ejecute una simulación")
            return
        
        curve_window = tk.Toplevel(self.root)
        curve_window.title("Curvas Detalladas de Operación")
        curve_window.geometry("1000x800")
        
        fig = Figure(figsize=(10, 8), dpi=100)
        gs = fig.add_gridspec(3, 2)
        
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(self.sim_data['hours'], self.sim_data['generation'], 'g-')
        ax1.set_title("Generación Solar")
        ax1.set_xlabel("Horas")
        ax1.set_ylabel("Potencia (W)")
        ax1.grid(True)
        
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(self.sim_data['hours'], self.sim_data['consumption'], 'r-')
        ax2.set_title("Consumo de Energía")
        ax2.set_xlabel("Horas")
        ax2.set_ylabel("Potencia (W)")
        ax2.grid(True)
        
        ax3 = fig.add_subplot(gs[1, :])
        ax3.plot(self.sim_data['hours'], self.sim_data['soc'], 'b-')
        ax3.set_title("Estado de Carga de Baterías")
        ax3.set_xlabel("Horas")
        ax3.set_ylabel("SOC (%)")
        ax3.grid(True)
        
        ax4 = fig.add_subplot(gs[2, :])
        ax4.plot(self.sim_data['hours'], self.sim_data['operation'], 'k-')
        ax4.set_title("Estado de Operación del Sistema")
        ax4.set_xlabel("Horas")
        ax4.set_ylabel("Operando (1=Sí, 0=No)")
        ax4.grid(True)
        
        canvas = FigureCanvasTkAgg(fig, master=curve_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        btn_frame = ttk.Frame(curve_window)
        btn_frame.pack(fill='x', pady=10)
        ttk.Button(btn_frame, text="Exportar Gráfico", 
                  command=lambda: self.export_figure(fig)).pack(pady=5)
    
    def export_figure(self, fig):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if file_path:
            fig.savefig(file_path, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Éxito", f"Gráfico exportado a:\n{file_path}")
    
    def generate_calendar(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        month_name = self.month_var.get()
        year = self.year_var.get()
        
        month_num = list(calendar.month_name).index(month_name)
        month_key = f"{year}-{month_num:02d}"
        
        cal = calendar.monthcalendar(year, month_num)
        days_in_month = calendar.monthrange(year, month_num)[1]
        
        # Calcular estadísticas
        radiation_values = []
        soc_values = []
        
        if month_key in self.solar_radiation_data:
            for day in range(1, days_in_month + 1):
                radiation_values.append(self.solar_radiation_data[month_key][day])
                soc_values.append(self.battery_soc_data[month_key][day])
            
            avg_radiation = round(sum(radiation_values) / len(radiation_values), 1)
            min_radiation = round(min(radiation_values), 1)
            max_radiation = round(max(radiation_values), 1)
            avg_soc = round(sum(soc_values) / len(soc_values))
            
            self.avg_radiation_var.set(f"Radiación promedio: {avg_radiation} kWh/m²")
            self.min_radiation_var.set(f"Mínima radiación: {min_radiation} kWh/m²")
            self.max_radiation_var.set(f"Máxima radiación: {max_radiation} kWh/m²")
            self.avg_soc_var.set(f"SOC promedio: {avg_soc}%")
        
        # Encabezados de días de la semana
        days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, day in enumerate(days):
            label = ttk.Label(self.scrollable_frame, text=day, width=15, 
                            relief='ridge', background='#f0f0f0', font=('Arial', 9, 'bold'))
            label.grid(row=0, column=i, padx=1, pady=1, sticky='nsew')
        
        for week_num, week in enumerate(cal, 1):
            for day_num, day in enumerate(week):
                if day == 0:
                    # Día fuera del mes actual - CORRECCIÓN APLICADA AQUÍ
                    empty_frame = tk.Frame(
                        self.scrollable_frame, 
                        relief='ridge', 
                        borderwidth=1,
                        bg='#f5f5f5',  # Usar bg en lugar de background
                        width=100,
                        height=100
                    )
                    empty_frame.grid(row=week_num, column=day_num, padx=1, pady=1, sticky='nsew')
                    empty_frame.grid_propagate(False)
                    continue
                
                day_frame = ttk.Frame(self.scrollable_frame, relief='ridge', borderwidth=1)
                day_frame.grid(row=week_num, column=day_num, padx=1, pady=1, sticky='nsew')
                day_frame.grid_propagate(False)
                day_frame.config(width=100, height=100)
                
                # Número del día
                day_label = ttk.Label(day_frame, text=str(day), font=('Arial', 10, 'bold'))
                day_label.pack(anchor='nw', padx=5, pady=2)
                
                # Datos de radiación solar
                radiation_frame = ttk.Frame(day_frame)
                radiation_frame.pack(fill='x', padx=5, pady=2)
                
                ttk.Label(radiation_frame, text="Radiación:", font=('Arial', 8)).pack(side='left')
                
                if month_key in self.solar_radiation_data and day in self.solar_radiation_data[month_key]:
                    radiation = self.solar_radiation_data[month_key][day]
                    radiation_color = self.get_radiation_color(radiation)
                    radiation_text = f"{radiation} kWh/m²"
                    ttk.Label(radiation_frame, text=radiation_text, 
                             background=radiation_color, font=('Arial', 8, 'bold')).pack(side='right')
                else:
                    ttk.Label(radiation_frame, text="--", background='#eeeeee').pack(side='right')
                
                # Barra de progreso para radiación
                if month_key in self.solar_radiation_data and day in self.solar_radiation_data[month_key]:
                    radiation = self.solar_radiation_data[month_key][day]
                    radiation_percent = min(100, int((radiation / 8.0) * 100))
                    
                    radiation_bar_frame = ttk.Frame(day_frame, height=5)
                    radiation_bar_frame.pack(fill='x', padx=5, pady=1)
                    
                    radiation_bar = ttk.Frame(radiation_bar_frame, 
                                            height=5, 
                                            width=radiation_percent,
                                            style='Radiation.Horizontal.TProgressbar')
                    radiation_bar.pack(anchor='w')
                
                # Datos de estado de carga
                soc_frame = ttk.Frame(day_frame)
                soc_frame.pack(fill='x', padx=5, pady=2)
                
                ttk.Label(soc_frame, text="SOC:", font=('Arial', 8)).pack(side='left')
                
                if month_key in self.battery_soc_data and day in self.battery_soc_data[month_key]:
                    soc = self.battery_soc_data[month_key][day]
                    soc_color = "#4CAF50" if soc > 70 else "#FFC107" if soc > 40 else "#F44336"
                    soc_text = f"{soc}%"
                    ttk.Label(soc_frame, text=soc_text, 
                             background=soc_color, font=('Arial', 8, 'bold')).pack(side='right')
                else:
                    ttk.Label(soc_frame, text="--", background='#eeeeee').pack(side='right')
                
                # Barra de progreso para SOC
                if month_key in self.battery_soc_data and day in self.battery_soc_data[month_key]:
                    soc = self.battery_soc_data[month_key][day]
                    
                    soc_bar_frame = ttk.Frame(day_frame, height=5)
                    soc_bar_frame.pack(fill='x', padx=5, pady=1)
                    
                    soc_bar = ttk.Frame(soc_bar_frame, 
                                      height=5, 
                                      width=soc,
                                      style='SOC.Horizontal.TProgressbar')
                    soc_bar.pack(anchor='w')
    
    def get_radiation_color(self, radiation):
        """Devuelve un color según el nivel de radiación solar"""
        if radiation < 2.0:
            return "#FFCDD2"  # Muy baja
        elif radiation < 4.0:
            return "#FFF9C4"  # Baja
        elif radiation < 6.0:
            return "#C8E6C9"  # Moderada
        else:
            return "#A5D6A7"  # Alta
    
    def generate_excel(self):
        try:
            data = {
                "Parámetro": [
                    "Fecha", 
                    "Potencia de Carga (W)", 
                    "Horas de Operación", 
                    "Energía Diaria (Wh)", 
                    "Paneles Necesarios", 
                    "Baterías Necesarias",
                    "Días de Autonomía",
                    "Horas de Sol Pico",
                    "Profundidad de Descarga (%)"
                ],
                "Valor": [
                    datetime.now().strftime("%Y-%m-%d"),
                    self.load_power.get(),
                    self.operating_hours.get(),
                    self.load_power.get() * self.operating_hours.get(),
                    int(np.ceil((self.load_power.get() * self.operating_hours.get()) / (self.panel_power.get() * self.sunlight_hours.get()))),
                    int(np.ceil((self.load_power.get() * self.operating_hours.get() * self.autonomy_days.get()) / 
                              ((self.battery_capacity.get() * self.battery_voltage.get()) * (self.dod_limit.get() / 100)))),
                    self.autonomy_days.get(),
                    self.sunlight_hours.get(),
                    self.dod_limit.get()
                ]
            }
            
            df = pd.DataFrame(data)
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if file_path:
                df.to_excel(file_path, index=False, engine='openpyxl')
                messagebox.showinfo("Éxito", f"Reporte Excel guardado en:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el Excel:\n{str(e)}")
    
    def generate_pdf(self):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=14, style='B')
            
            pdf.cell(0, 10, "Reporte Completo de Sistema Solar", 0, 1, 'C')
            pdf.ln(10)
            
            pdf.set_font("Arial", size=10)
            
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(0, 8, "Información del Sistema", 0, 1, 'L', 1)
            pdf.ln(2)
            
            data = [
                ("Fecha", datetime.now().strftime("%Y-%m-%d %H:%M")),
                ("Potencia de Carga", f"{self.load_power.get()} W"),
                ("Horas de Operación", f"{self.operating_hours.get()} h/día"),
                ("Horas de Sol Pico", f"{self.sunlight_hours.get()} h"),
                ("Días de Autonomía", f"{self.autonomy_days.get()} días"),
                ("Profundidad de Descarga", f"{self.dod_limit.get()}%")
            ]
            
            for label, value in data:
                pdf.cell(90, 8, label + ":", 0, 0)
                pdf.cell(0, 8, value, 0, 1)
            
            pdf.ln(5)
            
            pdf.set_fill_color(220, 255, 220)
            pdf.cell(0, 8, "Resultados del Cálculo", 0, 1, 'L', 1)
            pdf.ln(2)
            
            daily_energy = self.load_power.get() * self.operating_hours.get()
            num_panels = int(np.ceil(daily_energy / (self.panel_power.get() * self.sunlight_hours.get())))
            num_batteries = int(np.ceil((daily_energy * self.autonomy_days.get()) / 
                              ((self.battery_capacity.get() * self.battery_voltage.get()) * (self.dod_limit.get() / 100))))
            
            results = [
                ("Energía Diaria Requerida", f"{daily_energy:.2f} Wh"),
                ("Paneles Necesarios", f"{num_panels} (de {self.panel_power.get()} W c/u)"),
                ("Baterías Necesarias", f"{num_batteries} (de {self.battery_capacity.get()} Ah, {self.battery_voltage.get()} V)")
            ]
            
            for label, value in results:
                pdf.cell(90, 8, label + ":", 0, 0)
                pdf.cell(0, 8, value, 0, 1)
            
            pdf.ln(10)
            
            if hasattr(self, 'current_figure'):
                temp_img = "temp_plot.png"
                self.current_figure.savefig(temp_img, dpi=150, bbox_inches='tight')
                pdf.image(temp_img, x=10, w=180)
                os.remove(temp_img)
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            
            if file_path:
                pdf.output(file_path)
                messagebox.showinfo("Éxito", f"Reporte PDF guardado en:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    
    # Configurar estilos para las barras de progreso
    style = ttk.Style()
    style.configure('Radiation.Horizontal.TProgressbar', background='#FFD54F')  # Amarillo para radiación
    style.configure('SOC.Horizontal.TProgressbar', background='#4CAF50')       # Verde para SOC
    
    app = SolarSystemCalculator(root)
    root.mainloop()
