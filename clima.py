import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import requests
from io import BytesIO
import json
import pygame
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class IntegratedMonitoringSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Integrado de Monitoreo - Huaraz")
        self.root.state('zoomed')
        
        # Configuración inicial
        self.config = {}
        self.initialize_components()
        
    def initialize_components(self):
        """Inicializa todos los componentes del sistema"""
        self.setup_audio()
        self.load_config()
        self.setup_ui()
        self.initialize_weather_data()
        
    def setup_audio(self):
        """Configura el sistema de audio para alertas"""
        pygame.mixer.init()
    
    def load_config(self):
        """Carga la configuración desde archivo"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {
                'camera_urls': [''] * 4,
                'weather_api_key': '',
                'email_settings': {}
            }
    
    def save_config(self):
        """Guarda la configuración actual"""
        try:
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")
    
    def initialize_weather_data(self):
        """Inicializa datos meteorológicos con valores por defecto"""
        self.weather_data = {
            'temperature': 0,
            'humidity': 0,
            'wind_speed': 0,
            'conditions': "Desconocido",
            'pressure': 0,
            'forecast': []
        }
        self.update_weather_data()
    
    def setup_ui(self):
        """Configura la interfaz de usuario principal"""
        self.create_main_menu()
        self.setup_notebook()
    
    def create_main_menu(self):
        """Crea la barra de menú principal"""
        menubar = tk.Menu(self.root)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Guardar configuración", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        
        # Menú Visualización
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Cámaras", command=lambda: self.notebook.select(0))
        view_menu.add_command(label="Sensores", command=lambda: self.notebook.select(1))
        view_menu.add_command(label="Meteorología", command=lambda: self.notebook.select(2))
        menubar.add_cascade(label="Visualización", menu=view_menu)
        
        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Configuración", command=lambda: self.notebook.select(4))
        tools_menu.add_command(label="Actualizar datos", command=self.update_all_data)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        
        self.root.config(menu=menubar)
    
    def setup_notebook(self):
        """Configura el panel de pestañas principal"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)
        
        # Crear pestañas
        self.tabs = {
            'camera': self.create_camera_tab(),
            'sensors': self.create_sensors_tab(),
            'weather': self.create_weather_tab(),
            'alerts': self.create_alerts_tab(),
            'config': self.create_config_tab()
        }
        
        for name, tab in self.tabs.items():
            self.notebook.add(tab, text=name.capitalize())
    
    def create_camera_tab(self):
        """Crea la pestaña de visualización de cámaras"""
        tab = ttk.Frame(self.notebook)
        
        # Configurar grid para 4 cámaras (2x2)
        for i in range(2):
            tab.grid_rowconfigure(i, weight=1)
            tab.grid_columnconfigure(i, weight=1)
        
        self.camera_labels = []
        for i in range(4):
            frame = ttk.LabelFrame(tab, text=f"Cámara {i+1}")
            frame.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='nsew')
            
            label = tk.Label(frame, bg='black')
            label.pack(fill='both', expand=True)
            self.camera_labels.append(label)
        
        # Panel de control
        control_frame = ttk.Frame(tab)
        control_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(control_frame, text="Conectar todas", 
                  command=self.connect_all_cameras).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Desconectar todas", 
                  command=self.disconnect_all_cameras).pack(side='left', padx=5)
        
        return tab
    
    def create_sensors_tab(self):
        """Crea la pestaña de monitoreo de sensores"""
        tab = ttk.Frame(self.notebook)
        notebook = ttk.Notebook(tab)
        notebook.pack(fill='both', expand=True)
        
        # Sub-pestañas para tipos de sensores
        env_tab = ttk.Frame(notebook)
        sec_tab = ttk.Frame(notebook)
        
        notebook.add(env_tab, text="Ambientales")
        notebook.add(sec_tab, text="Seguridad")
        
        self.create_environmental_sensors(env_tab)
        self.create_security_sensors(sec_tab)
        
        return tab
    
    def create_environmental_sensors(self, parent):
        """Crea el panel de sensores ambientales"""
        # Ejemplo básico - implementar según necesidades
        ttk.Label(parent, text="Sensores Ambientales", font=('Arial', 12, 'bold')).pack(pady=10)
        
        sensors = [
            ("Temperatura", "°C"),
            ("Humedad", "%"),
            ("Presión Atmosférica", "hPa"),
            ("Calidad del Aire", "AQI")
        ]
        
        for name, unit in sensors:
            frame = ttk.Frame(parent)
            frame.pack(fill='x', padx=10, pady=5)
            
            ttk.Label(frame, text=f"{name}:", width=20, anchor='w').pack(side='left')
            ttk.Label(frame, text=f"0.00 {unit}", width=10).pack(side='left')
            ttk.Progressbar(frame, orient='horizontal', length=100).pack(side='left', padx=10)
    
    def create_security_sensors(self, parent):
        """Crea el panel de sensores de seguridad"""
        ttk.Label(parent, text="Sensores de Seguridad", font=('Arial', 12, 'bold')).pack(pady=10)
        
        sensors = [
            ("Movimiento", "Inactivo"),
            ("Puertas/Ventanas", "Cerrado"),
            ("Cámaras", "Activas"),
            ("Alarma", "Desactivada")
        ]
        
        for name, status in sensors:
            frame = ttk.Frame(parent)
            frame.pack(fill='x', padx=10, pady=5)
            
            ttk.Label(frame, text=f"{name}:", width=20, anchor='w').pack(side='left')
            ttk.Label(frame, text=status, width=15).pack(side='left')
            ttk.Button(frame, text="Detalles", width=10).pack(side='right')
    
    def create_weather_tab(self):
        """Crea la pestaña de información meteorológica"""
        tab = ttk.Frame(self.notebook)
        
        # Configurar scroll
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Secciones meteorológicas
        self.setup_current_weather_section(scroll_frame)
        self.setup_forecast_section(scroll_frame)
        self.setup_weather_graph_section(scroll_frame)
        
        ttk.Button(tab, text="Actualizar Datos", command=self.update_weather_data).pack(side='bottom', pady=10)
        
        return tab
    
    def setup_current_weather_section(self, parent):
        """Configura la sección de clima actual"""
        frame = ttk.LabelFrame(parent, text="Condiciones Actuales - Huaraz")
        frame.pack(fill='x', padx=10, pady=10)
        
        # Icono y temperatura
        top_frame = ttk.Frame(frame)
        top_frame.pack(fill='x')
        
        self.weather_icon = tk.Label(top_frame)
        self.weather_icon.pack(side='left', padx=10)
        
        self.temp_label = tk.Label(top_frame, font=('Arial', 24, 'bold'))
        self.temp_label.pack(side='left')
        
        self.conditions_label = tk.Label(top_frame, font=('Arial', 12))
        self.conditions_label.pack(side='left', padx=10)
        
        # Detalles adicionales
        details_frame = ttk.Frame(frame)
        details_frame.pack(fill='x', padx=10, pady=5)
        
        metrics = [
            ("Humedad:", "humidity_label", "%"),
            ("Viento:", "wind_label", "km/h"),
            ("Presión:", "pressure_label", "hPa")
        ]
        
        for i, (text, attr, unit) in enumerate(metrics):
            frame = ttk.Frame(details_frame)
            frame.grid(row=i//2, column=i%2, sticky='w', padx=10, pady=2)
            
            ttk.Label(frame, text=text).pack(side='left')
            label = ttk.Label(frame, width=10)
            label.pack(side='left')
            ttk.Label(frame, text=unit).pack(side='left')
            
            setattr(self, attr, label)
    
    def setup_forecast_section(self, parent):
        """Configura la sección de pronóstico extendido"""
        frame = ttk.LabelFrame(parent, text="Pronóstico Extendido (5 días)")
        frame.pack(fill='x', padx=10, pady=10)
        
        self.forecast_days = []
        for i in range(5):
            day_frame = ttk.Frame(frame)
            day_frame.pack(side='left', expand=True, fill='both', padx=5)
            
            day_label = ttk.Label(day_frame, font=('Arial', 10, 'bold'))
            day_label.pack()
            
            icon_label = ttk.Label(day_frame)
            icon_label.pack()
            
            temp_label = ttk.Label(day_frame)
            temp_label.pack()
            
            self.forecast_days.append((day_label, icon_label, temp_label))
    
    def setup_weather_graph_section(self, parent):
        """Configura el gráfico de temperaturas"""
        frame = ttk.LabelFrame(parent, text="Tendencias de Temperatura")
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.weather_fig, self.weather_ax = plt.subplots(figsize=(8, 4))
        self.weather_canvas = FigureCanvasTkAgg(self.weather_fig, master=frame)
        self.weather_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def update_weather_data(self):
        """Actualiza los datos meteorológicos"""
        try:
            # Datos de ejemplo (reemplazar con API real)
            self.weather_data = {
                'temperature': 18.5,
                'humidity': 65,
                'wind_speed': 12,
                'conditions': "Parcialmente nublado",
                'pressure': 1012,
                'forecast': [
                    {'day': 'Hoy', 'temp_max': 20, 'temp_min': 12, 'condition': 'Soleado'},
                    {'day': 'Mañana', 'temp_max': 19, 'temp_min': 11, 'condition': 'Parcialmente nublado'},
                    {'day': 'Viernes', 'temp_max': 17, 'temp_min': 10, 'condition': 'Lluvia ligera'},
                    {'day': 'Sábado', 'temp_max': 16, 'temp_min': 9, 'condition': 'Lluvia'},
                    {'day': 'Domingo', 'temp_max': 18, 'temp_min': 10, 'condition': 'Nublado'}
                ]
            }
            
            self.update_weather_ui()
            self.update_weather_chart()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar clima: {str(e)}")
    
    def update_weather_ui(self):
        """Actualiza la interfaz con los datos meteorológicos"""
        # Datos actuales
        self.temp_label.config(text=f"{self.weather_data['temperature']}°C")
        self.conditions_label.config(text=self.weather_data['conditions'])
        
        self.humidity_label.config(text=f"{self.weather_data['humidity']}")
        self.wind_label.config(text=f"{self.weather_data['wind_speed']}")
        self.pressure_label.config(text=f"{self.weather_data['pressure']}")
        
        # Pronóstico
        for i, forecast in enumerate(self.weather_data['forecast'][:5]):
            day_label, icon_label, temp_label = self.forecast_days[i]
            day_label.config(text=forecast['day'])
            temp_label.config(text=f"{forecast['temp_max']}° / {forecast['temp_min']}°")
    
    def update_weather_chart(self):
        """Actualiza el gráfico de temperaturas"""
        self.weather_ax.clear()
        
        days = [f['day'] for f in self.weather_data['forecast']]
        max_temps = [f['temp_max'] for f in self.weather_data['forecast']]
        min_temps = [f['temp_min'] for f in self.weather_data['forecast']]
        
        self.weather_ax.plot(days, max_temps, 'r-o', label='Máx')
        self.weather_ax.plot(days, min_temps, 'b-o', label='Mín')
        self.weather_ax.fill_between(days, max_temps, min_temps, color='gray', alpha=0.2)
        
        self.weather_ax.set_title('Pronóstico de Temperatura - Huaraz')
        self.weather_ax.set_ylabel('Temperatura (°C)')
        self.weather_ax.legend()
        self.weather_ax.grid(True)
        
        self.weather_canvas.draw()
    
    def create_alerts_tab(self):
        """Crea la pestaña de configuración de alertas"""
        tab = ttk.Frame(self.notebook)
        
        # Implementación básica
        ttk.Label(tab, text="Configuración de Alertas", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Aquí iría la implementación completa
        ttk.Label(tab, text="En desarrollo...").pack()
        
        return tab
    
    def create_config_tab(self):
        """Crea la pestaña de configuración del sistema"""
        tab = ttk.Frame(self.notebook)
        
        ttk.Label(tab, text="Configuración del Sistema", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Configuración de cámaras
        cam_frame = ttk.LabelFrame(tab, text="Configuración de Cámaras")
        cam_frame.pack(fill='x', padx=10, pady=5)
        
        self.cam_url_entries = []
        for i in range(4):
            frame = ttk.Frame(cam_frame)
            frame.pack(fill='x', padx=5, pady=2)
            
            ttk.Label(frame, text=f"Cámara {i+1}:").pack(side='left')
            entry = ttk.Entry(frame, width=50)
            entry.pack(side='left', expand=True, fill='x', padx=5)
            entry.insert(0, self.config.get('camera_urls', ['']*4)[i])
            self.cam_url_entries.append(entry)
        
        # Botón guardar
        ttk.Button(tab, text="Guardar Configuración", command=self.save_config).pack(pady=20)
        
        return tab
    
    def connect_all_cameras(self):
        """Conecta todas las cámaras configuradas"""
        for i, entry in enumerate(self.cam_url_entries):
            url = entry.get()
            if url:
                try:
                    # Aquí iría el código para conectar cada cámara
                    print(f"Conectando cámara {i+1} a {url}")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo conectar cámara {i+1}: {str(e)}")
    
    def disconnect_all_cameras(self):
        """Desconecta todas las cámaras"""
        print("Desconectando todas las cámaras")
        # Implementar lógica real de desconexión
    
    def update_all_data(self):
        """Actualiza todos los datos del sistema"""
        self.update_weather_data()
        # Aquí se agregarían otras actualizaciones

if __name__ == "__main__":
    root = tk.Tk()
    app = IntegratedMonitoringSystem(root)
    root.mainloop()
