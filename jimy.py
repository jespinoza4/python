import tkinter as tk
from tkinter import ttk, filedialog
import pygame
import threading
from PIL import Image, ImageTk
import os
import json

class SecurityDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Monitoreo - Pantalla Completa")
        self.root.state('zoomed')  # Pantalla completa
        
        # Configuración de tema
        self.bg_color = "#2e2e2e"
        self.frame_color = "#3e3e3e"
        self.text_color = "white"
        self.alarm_color = "#ff5555"
        
        # Inicializar pygame para sonido
        pygame.mixer.init()
        
        # Configuración de alarmas
        self.alarm_sounds = {
            'magnetico': "alarma_magnetico.mp3",
            'tilt': "alarma_tilt.mp3",
            'agua': "alarma_agua.mp3",
            'default': "alarma_general.mp3"
        }
        self.current_alarm_type = None
        self.alarma_activa = False
        
        # Cargar configuración
        self.load_config()
        
        # Configuración inicial
        self.setup_initial_values()
        
        # Crear interfaz
        self.create_main_panel()
        self.create_alarm_panel()
        self.create_sound_config_panel()
        
        # Asegurar archivos de sonido
        self.ensure_sound_files()
    
    def setup_initial_values(self):
        # Valores iniciales para todos los sensores
        self.current_values = {
            'agua': 0.0, 'viento': 0.0, 'temp': 0.0, 'radiacion': 0.0,
            'caudal': [0.0]*11, 'axial': 0.0, 'masa': 0.0,
            'magnetico': [0.0]*4, 'tilt': [0.0]*6
        }
        
        # Límites configurables
        self.limites = {
            'agua': 100.0, 'viento': 50.0, 'temp': 40.0, 'radiacion': 500.0,
            'caudal': 30.0, 'axial': 1000.0, 'masa': 50.0,
            'magnetico': [50.0]*4, 'tilt': [30.0]*6  # 30° para inclinación
        }
    
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.alarm_sounds = config.get('alarm_sounds', self.alarm_sounds)
                self.limites = config.get('limites', self.limites)
        except:
            pass
    
    def save_config(self):
        config = {
            'alarm_sounds': self.alarm_sounds,
            'limites': self.limites
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)
    
    def ensure_sound_files(self):
        for sound in self.alarm_sounds.values():
            if not os.path.exists(sound):
                open(sound, 'a').close()  # Crear archivo vacío si no existe
    
    def create_main_panel(self):
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Panel izquierdo (2/3 del espacio)
        left_frame = tk.Frame(main_frame, bg=self.bg_color)
        left_frame.pack(side='left', fill='both', expand=True)
        
        # Panel derecho (1/3 del espacio)
        right_frame = tk.Frame(main_frame, bg=self.bg_color, width=400)
        right_frame.pack(side='right', fill='y')
        
        # Crear componentes
        self.create_camera_grid(left_frame)
        self.create_sensor_controls(left_frame)
        self.create_status_panel(right_frame)
    
    def create_camera_grid(self, parent):
        cam_frame = tk.LabelFrame(parent, text="Vigilancia en Vivo", 
                                bg=self.frame_color, fg=self.text_color,
                                font=('Arial', 14, 'bold'))
        cam_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.cams = []
        for i in range(4):
            cam = tk.Label(cam_frame, 
                         text=f"Cámara {i+1}", 
                         bg='gray20',
                         fg='white',
                         font=('Arial', 16),
                         width=25,
                         height=10)
            cam.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='nsew')
            self.cams.append(cam)
        
        # Configurar grid
        for i in range(2):
            cam_frame.grid_rowconfigure(i, weight=1)
            cam_frame.grid_columnconfigure(i, weight=1)
    
    def create_sensor_controls(self, parent):
        sensor_frame = tk.LabelFrame(parent, text="Control de Sensores", 
                                   bg=self.frame_color, fg=self.text_color,
                                   font=('Arial', 14, 'bold'))
        sensor_frame.pack(fill='x', padx=10, pady=10)
        
        # Sensores principales
        main_sensor_frame = tk.Frame(sensor_frame, bg=self.frame_color)
        main_sensor_frame.pack(fill='x', pady=5)
        
        self.create_sensor_group(main_sensor_frame, "Ambientales", [
            ('agua', "Nivel Agua", "cm"),
            ('viento', "Velocidad Viento", "km/h"),
            ('temp', "Temperatura", "°C"),
            ('radiacion', "Radiación Solar", "W/m²")
        ], 0)
        
        # Sensores magnéticos
        mag_frame = tk.Frame(sensor_frame, bg=self.frame_color)
        mag_frame.pack(fill='x', pady=5)
        
        for i in range(4):
            self.create_manual_control(mag_frame, f'magnetico_{i}', f"Magnético {i+1}", "µT", 
                                     self.limites['magnetico'][i], i//2, i%2)
        
        # Sensores de inclinación
        tilt_frame = tk.Frame(sensor_frame, bg=self.frame_color)
        tilt_frame.pack(fill='x', pady=5)
        
        for i in range(6):
            self.create_manual_control(tilt_frame, f'tilt_{i}', f"Inclinación {i+1}", "°", 
                                     self.limites['tilt'][i], i//3, i%3)
    
    def create_status_panel(self, parent):
        status_frame = tk.LabelFrame(parent, text="Estado del Sistema", 
                                   bg=self.frame_color, fg=self.text_color,
                                   font=('Arial', 14, 'bold'))
        status_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Panel de alarmas
        self.alarm_display = tk.Label(status_frame, text="SISTEMA NORMAL", 
                                     font=('Arial', 18, 'bold'),
                                     bg=self.frame_color, fg='green')
        self.alarm_display.pack(pady=20)
        
        # Indicadores de sensores críticos
        self.critical_sensors = tk.Label(status_frame, text="", 
                                        font=('Arial', 12),
                                        bg=self.frame_color, fg=self.text_color,
                                        justify='left')
        self.critical_sensors.pack(fill='x', padx=20)
        
        # Historial de eventos
        event_frame = tk.LabelFrame(status_frame, text="Historial de Eventos", 
                                  bg=self.frame_color, fg=self.text_color)
        event_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.event_log = tk.Text(event_frame, height=10, bg="#1e1e1e", fg="white",
                               font=('Arial', 10))
        self.event_log.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(event_frame, orient="vertical", command=self.event_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.event_log.config(yscrollcommand=scrollbar.set)
    
    def create_alarm_panel(self):
        # Se crea automáticamente en create_status_panel
        pass
    
    def create_sound_config_panel(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuración de Sonidos")
        config_window.geometry("600x400")
        
        tk.Label(config_window, text="Configuración de Alarmas Sonoras", 
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Configuración por tipo de alarma
        sound_types = [
            ('Alarma Magnética', 'magnetico'),
            ('Alarma Inclinación', 'tilt'),
            ('Alarma Nivel Agua', 'agua'),
            ('Alarma General', 'default')
        ]
        
        for i, (label, key) in enumerate(sound_types):
            frame = tk.Frame(config_window)
            frame.pack(fill='x', padx=20, pady=5)
            
            tk.Label(frame, text=label, width=20, anchor='w').pack(side='left')
            
            entry = tk.Entry(frame, width=30)
            entry.insert(0, self.alarm_sounds.get(key, ""))
            entry.pack(side='left', padx=5)
            
            btn = tk.Button(frame, text="Examinar", 
                          command=lambda e=entry, k=key: self.select_sound_file(e, k))
            btn.pack(side='left')
        
        # Botón guardar
        tk.Button(config_window, text="Guardar Configuración", 
                command=self.save_sound_config, bg="#4CAF50", fg="white").pack(pady=20)
    
    def select_sound_file(self, entry, sound_type):
        filename = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3 *.wav")])
        if filename:
            entry.delete(0, tk.END)
            entry.insert(0, filename)
            self.alarm_sounds[sound_type] = filename
    
    def save_sound_config(self):
        self.save_config()
        tk.messagebox.showinfo("Configuración", "Configuración de sonidos guardada correctamente")
    
    def create_sensor_group(self, parent, title, sensors, row_pos):
        group_frame = tk.LabelFrame(parent, text=title, bg=self.frame_color, fg=self.text_color)
        group_frame.pack(fill='x', padx=5, pady=5)
        
        for i, (key, name, unit) in enumerate(sensors):
            self.create_manual_control(group_frame, key, name, unit, self.limites[key], i//2, i%2)
    
    def create_manual_control(self, parent, key, name, unit, limit, row, col):
        frame = tk.Frame(parent, bg=self.frame_color)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Nombre del sensor
        tk.Label(frame, text=name, bg=self.frame_color, fg=self.text_color).grid(row=0, column=0, sticky='w')
        
        # Barra de desplazamiento
        slider = tk.Scale(frame, from_=0, to=self.calculate_slider_max(unit), 
                         orient='horizontal', resolution=0.1,
                         command=lambda val, k=key: self.update_sensor_value(k, float(val)),
                         bg=self.frame_color, fg=self.text_color,
                         highlightbackground=self.frame_color)
        slider.grid(row=1, column=0, columnspan=2, sticky='ew')
        
        # Valor actual
        value_label = tk.Label(frame, text="0.00", width=6, 
                             bg=self.frame_color, fg=self.text_color)
        value_label.grid(row=2, column=0, sticky='w')
        
        # Unidad
        tk.Label(frame, text=unit, bg=self.frame_color, fg=self.text_color).grid(row=2, column=1, sticky='w')
        
        # Indicador
        indicator = tk.Label(frame, text="●", font=('Arial', 20), fg='green', bg=self.frame_color)
        indicator.grid(row=2, column=2, padx=10)
        
        # Control de límite
        limit_frame = tk.Frame(frame, bg=self.frame_color)
        limit_frame.grid(row=3, column=0, columnspan=3, sticky='ew')
        
        tk.Label(limit_frame, text="Límite:", bg=self.frame_color, fg=self.text_color).pack(side='left')
        limit_entry = tk.Entry(limit_frame, width=6)
        limit_entry.insert(0, str(limit))
        limit_entry.pack(side='left')
        limit_entry.bind('<Return>', lambda e, k=key: self.update_limit(k, e))
        
        # Guardar referencias
        if not hasattr(self, 'sensor_controls'):
            self.sensor_controls = {}
        
        self.sensor_controls[key] = {
            'slider': slider,
            'value_label': value_label,
            'indicator': indicator,
            'limit_entry': limit_entry,
            'unit': unit
        }
    
    def calculate_slider_max(self, unit):
        if unit == "°": return 90
        if unit == "µT": return 200
        if unit == "cm": return 200
        if unit == "km/h": return 150
        if unit == "W/m²": return 1000
        return 100
    
    def update_sensor_value(self, key, value):
        # Determinar el tipo de sensor
        if key.startswith('magnetico_'):
            idx = int(key.split('_')[1])
            self.current_values['magnetico'][idx] = value
            limit = self.limites['magnetico'][idx]
            alarm_type = 'magnetico'
        elif key.startswith('tilt_'):
            idx = int(key.split('_')[1])
            self.current_values['tilt'][idx] = value
            limit = self.limites['tilt'][idx]
            alarm_type = 'tilt'
        elif key == 'agua':
            self.current_values[key] = value
            limit = self.limites[key]
            alarm_type = 'agua'
        else:
            self.current_values[key] = value
            limit = self.limites[key]
            alarm_type = 'default'
        
        # Actualizar interfaz
        self.sensor_controls[key]['value_label'].config(text=f"{value:.2f}")
        
        # Verificar límites
        if value > limit:
            self.sensor_controls[key]['indicator'].config(fg='red')
            if not self.alarma_activa:
                self.current_alarm_type = alarm_type
                self.activate_alarm(alarm_type)
            self.update_critical_sensors(key, name=self.sensor_controls[key]['slider'].master.children['!label'].cget('text'))
        else:
            self.sensor_controls[key]['indicator'].config(fg='green')
            self.check_alarm_condition()
    
    def update_critical_sensors(self, sensor_key, name):
        current_text = self.critical_sensors.cget('text')
        new_entry = f"- {name} (CRÍTICO)\n"
        
        if new_entry not in current_text:
            self.critical_sensors.config(text=current_text + new_entry)
            self.log_event(f"Sensor {name} en estado crítico: {self.current_values[sensor_key]:.2f}")
    
    def log_event(self, message):
        self.event_log.insert(tk.END, f"{message}\n")
        self.event_log.see(tk.END)
    
    def update_limit(self, key, event):
        try:
            new_limit = float(event.widget.get())
            
            if key.startswith('magnetico_'):
                idx = int(key.split('_')[1])
                self.limites['magnetico'][idx] = new_limit
            elif key.startswith('tilt_'):
                idx = int(key.split('_')[1])
                self.limites['tilt'][idx] = new_limit
            elif key == 'caudal':
                self.limites['caudal'] = new_limit
            else:
                self.limites[key] = new_limit
            
            # Re-evaluar condición actual
            if key.startswith(('magnetico_', 'tilt_')):
                self.update_sensor_value(key, self.current_values[key.split('_')[0]][int(key.split('_')[1])])
            else:
                self.update_sensor_value(key, self.current_values[key])
                
        except ValueError:
            pass
    
    def check_alarm_condition(self):
        if self.alarma_activa:
            # Verificar si todos los sensores están bajo sus límites
            all_ok = True
            
            # Verificar sensores principales
            for key in ['agua', 'viento', 'temp', 'radiacion', 'axial', 'masa']:
                if self.current_values[key] > self.limites[key]:
                    all_ok = False
                    break
            
            # Verificar sensores de caudal
            if all_ok and any(v > self.limites['caudal'] for v in self.current_values['caudal']):
                all_ok = False
            
            # Verificar sensores magnéticos
            if all_ok and any(v > l for v, l in zip(self.current_values['magnetico'], self.limites['magnetico'])):
                all_ok = False
            
            # Verificar sensores de inclinación
            if all_ok and any(v > l for v, l in zip(self.current_values['tilt'], self.limites['tilt'])):
                all_ok = False
            
            if all_ok:
                self.deactivate_alarm()
                self.critical_sensors.config(text="")
                self.log_event("Todos los sensores en valores normales")
    
    def activate_alarm(self, alarm_type):
        self.alarma_activa = True
        self.alarm_display.config(text="ALARMA ACTIVADA", fg=self.alarm_color)
        
        # Reproducir sonido específico
        sound_file = self.alarm_sounds.get(alarm_type, self.alarm_sounds['default'])
        threading.Thread(target=self.play_alarm_sound, args=(sound_file,), daemon=True).start()
        
        # Cambiar fondo de las cámaras
        for cam in self.cams:
            cam.config(bg='#ffcccc')
        
        self.log_event(f"Alarma activada: {alarm_type.upper()}")
    
    def deactivate_alarm(self):
        self.alarma_activa = False
        self.alarm_display.config(text="SISTEMA NORMAL", fg='green')
        pygame.mixer.music.stop()
        
        for cam in self.cams:
            cam.config(bg='gray20')
        
        self.log_event("Alarma desactivada")
    
    def play_alarm_sound(self, sound_file):
        try:
            if os.path.exists(sound_file):
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play(-1)
            else:
                print(f"Archivo de sonido no encontrado: {sound_file}")
        except Exception as e:
            print(f"Error al reproducir sonido: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SecurityDashboard(root)
    root.mainloop()
