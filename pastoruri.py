import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import math
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import time
import serial
import serial.tools.list_ports
from threading import Thread
import cv2
from PIL import Image, ImageTk
import queue
import json

class LagunaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Integrado de Monitoreo de Laguna")
        self.root.geometry("1200x800")
        
        # Configuración inicial
        self.config = {
            'rtsp_url': 'rtsp://admin:password@192.168.1.64:554/stream1',
            'serial_port': 'COM3',
            'baudrate': 9600,
            'nivel_max': 25.0,
            'nivel_min': 5.0,
            'area_laguna': 50000
        }
        
        # Datos de la laguna
        self.nivel_actual = 15.2  # metros
        self.nivel_maximo = self.config['nivel_max']
        self.nivel_minimo = self.config['nivel_min']
        self.area = self.config['area_laguna']
        self.volumen = self.calcular_volumen()
        
        # Estado de las tuberías (11 tuberías)
        self.tuberias = [{
            'id': i+1,
            'caudal': 0.0,
            'activa': False,
            'ultima_falla': None,
            'alerta_mostrada': False
        } for i in range(11)]
        
        # Comunicación serial
        self.serial_connection = None
        self.serial_thread = None
        self.serial_running = False
        self.serial_queue = queue.Queue()
        
        # Video RTSP
        self.video_thread = None
        self.video_running = False
        self.current_frame = None
        self.video_queue = queue.Queue(maxsize=1)
        
        # Configurar interfaz
        self.setup_ui()
        self.configurar_estilos()
        
        # Iniciar actualización automática
        self.actualizar_datos()
    
    def configurar_estilos(self):
        """Configura los estilos visuales de la aplicación"""
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('Error.TFrame', background='#ffdddd')
        style.configure('TLabel', font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('TButton', font=('Arial', 10))
        style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
    
    def calcular_volumen(self):
        """Calcula el volumen basado en el nivel actual"""
        return self.area * self.nivel_actual * 0.8  # Factor de forma
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Barra de menú
        self.setup_menu()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior (cámara y datos)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        # Frame de cámara
        cam_frame = ttk.LabelFrame(top_frame, text="Cámara de Seguridad", padding="10")
        cam_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.video_label = ttk.Label(cam_frame)
        self.video_label.pack()
        
        # Frame de datos
        data_frame = ttk.Frame(top_frame)
        data_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Indicador de nivel (tanque)
        self.canvas_tanque = tk.Canvas(data_frame, width=150, height=300, bg='white')
        self.canvas_tanque.pack(pady=5)
        
        # Datos numéricos
        datos_frame = ttk.Frame(data_frame)
        datos_frame.pack(pady=10)
        
        self.lbl_nivel = ttk.Label(datos_frame, text="Nivel: -- m", style='Title.TLabel')
        self.lbl_nivel.pack(anchor=tk.W)
        
        self.lbl_volumen = ttk.Label(datos_frame, text="Volumen: -- m³", style='Title.TLabel')
        self.lbl_volumen.pack(anchor=tk.W, pady=5)
        
        self.lbl_area = ttk.Label(datos_frame, text=f"Área: {self.area:,} m²", style='Title.TLabel')
        self.lbl_area.pack(anchor=tk.W)
        
        # Frame de tuberías
        tuberias_frame = ttk.LabelFrame(main_frame, text="Tuberías de Extracción", padding="10")
        tuberias_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Crear widgets para cada tubería
        self.tuberia_widgets = []
        for i in range(11):
            frame = ttk.Frame(tuberias_frame, padding="5")
            frame.grid(row=0, column=i, padx=5, pady=5)
            
            lbl_id = ttk.Label(frame, text=f"Tubería {i+1}", style='TLabel')
            lbl_id.grid(row=0, column=0)
            
            canvas = tk.Canvas(frame, width=30, height=50, bg='white')
            canvas.grid(row=1, column=0, pady=5)
            
            lbl_caudal = ttk.Label(frame, text="0.0 m³/s", style='TLabel')
            lbl_caudal.grid(row=2, column=0)
            
            self.tuberia_widgets.append({
                'frame': frame,
                'canvas': canvas,
                'lbl_caudal': lbl_caudal
            })
        
        # Gráfico de nivel
        graph_frame = ttk.LabelFrame(main_frame, text="Histórico de Nivel", padding="10")
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.fig = Figure(figsize=(10, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.grafico_nivel = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.grafico_nivel.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.actualizar_status("Sistema iniciado. Conectando dispositivos...")
        
        # Iniciar dispositivos
        self.iniciar_serial()
        self.iniciar_video()
    
    def setup_menu(self):
        """Configura la barra de menú"""
        menubar = tk.Menu(self.root)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Guardar Configuración", command=self.guardar_configuracion)
        file_menu.add_command(label="Cargar Configuración", command=self.cargar_configuracion)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.salir)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        
        # Menú Configuración
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Configurar Cámara", command=self.configurar_camara)
        config_menu.add_command(label="Configurar Puerto Serial", command=self.configurar_serial)
        config_menu.add_command(label="Parámetros Laguna", command=self.configurar_laguna)
        menubar.add_cascade(label="Configuración", menu=config_menu)
        
        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Probar Sensores", command=self.probar_sensores)
        tools_menu.add_command(label="Calibrar Sistema", command=self.calibrar_sistema)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        
        self.root.config(menu=menubar)
    
    def guardar_configuracion(self):
        """Guarda la configuración actual en un archivo JSON"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
            title="Guardar configuración como"
        )
        
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    json.dump(self.config, f, indent=4)
                self.actualizar_status(f"Configuración guardada en {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{str(e)}")
    
    def cargar_configuracion(self):
        """Carga la configuración desde un archivo JSON"""
        filepath = filedialog.askopenfilename(
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
            title="Seleccionar archivo de configuración"
        )
        
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    nueva_config = json.load(f)
                
                # Actualizar solo las claves existentes
                for key in self.config:
                    if key in nueva_config:
                        self.config[key] = nueva_config[key]
                
                # Reiniciar componentes con nueva configuración
                self.nivel_maximo = self.config['nivel_max']
                self.nivel_minimo = self.config['nivel_min']
                self.area = self.config['area_laguna']
                self.volumen = self.calcular_volumen()
                
                self.reiniciar_serial()
                self.reiniciar_video()
                
                self.actualizar_status(f"Configuración cargada desde {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la configuración:\n{str(e)}")
    
    def configurar_camara(self):
        """Abre diálogo para configurar cámara RTSP"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configurar Cámara")
        
        ttk.Label(dialog, text="URL RTSP:").grid(row=0, column=0, padx=5, pady=5)
        url_entry = ttk.Entry(dialog, width=50)
        url_entry.grid(row=0, column=1, padx=5, pady=5)
        url_entry.insert(0, self.config['rtsp_url'])
        
        def guardar():
            self.config['rtsp_url'] = url_entry.get()
            self.reiniciar_video()
            dialog.destroy()
        
        ttk.Button(dialog, text="Guardar", command=guardar).grid(row=1, column=1, pady=10)
    
    def configurar_serial(self):
        """Abre diálogo para configurar puerto serial"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configurar Puerto Serial")
        
        # Listar puertos disponibles
        ports = [port.device for port in serial.tools.list_ports.comports()]
        
        ttk.Label(dialog, text="Puerto:").grid(row=0, column=0, padx=5, pady=5)
        port_combobox = ttk.Combobox(dialog, values=ports)
        port_combobox.grid(row=0, column=1, padx=5, pady=5)
        if self.config['serial_port'] in ports:
            port_combobox.set(self.config['serial_port'])
        
        ttk.Label(dialog, text="Baudrate:").grid(row=1, column=0, padx=5, pady=5)
        baud_entry = ttk.Entry(dialog)
        baud_entry.grid(row=1, column=1, padx=5, pady=5)
        baud_entry.insert(0, str(self.config['baudrate']))
        
        def guardar():
            self.config['serial_port'] = port_combobox.get()
            self.config['baudrate'] = int(baud_entry.get())
            self.reiniciar_serial()
            dialog.destroy()
        
        ttk.Button(dialog, text="Guardar", command=guardar).grid(row=2, column=1, pady=10)
    
    def configurar_laguna(self):
        """Diálogo para configurar parámetros de la laguna"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configurar Parámetros de la Laguna")
        
        ttk.Label(dialog, text="Nivel Máximo (m):").grid(row=0, column=0, padx=5, pady=5)
        max_entry = ttk.Entry(dialog)
        max_entry.grid(row=0, column=1, padx=5, pady=5)
        max_entry.insert(0, str(self.config['nivel_max']))
        
        ttk.Label(dialog, text="Nivel Mínimo (m):").grid(row=1, column=0, padx=5, pady=5)
        min_entry = ttk.Entry(dialog)
        min_entry.grid(row=1, column=1, padx=5, pady=5)
        min_entry.insert(0, str(self.config['nivel_min']))
        
        ttk.Label(dialog, text="Área (m²):").grid(row=2, column=0, padx=5, pady=5)
        area_entry = ttk.Entry(dialog)
        area_entry.grid(row=2, column=1, padx=5, pady=5)
        area_entry.insert(0, str(self.config['area_laguna']))
        
        def guardar():
            try:
                self.config['nivel_max'] = float(max_entry.get())
                self.config['nivel_min'] = float(min_entry.get())
                self.config['area_laguna'] = float(area_entry.get())
                
                # Actualizar variables internas
                self.nivel_maximo = self.config['nivel_max']
                self.nivel_minimo = self.config['nivel_min']
                self.area = self.config['area_laguna']
                self.volumen = self.calcular_volumen()
                
                dialog.destroy()
                self.actualizar_status("Parámetros de la laguna actualizados")
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos")
        
        ttk.Button(dialog, text="Guardar", command=guardar).grid(row=3, column=1, pady=10)
    
    def probar_sensores(self):
        """Prueba los sensores y muestra un resumen"""
        messagebox.showinfo(
            "Probar Sensores",
            "Realizando prueba de sensores...\n\n"
            f"Tuberías activas: {sum(1 for t in self.tuberias if t['activa'])}/11\n"
            f"Nivel actual: {self.nivel_actual:.2f} m\n"
            f"Volumen: {self.volumen:,.0f} m³"
        )
    
    def calibrar_sistema(self):
        """Muestra diálogo de calibración"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Calibrar Sistema")
        
        ttk.Label(dialog, text="Seleccione el tipo de calibración:").pack(pady=10)
        
        ttk.Button(dialog, text="Calibrar Sensores de Caudal", 
                  command=lambda: self.calibrar_caudal(dialog)).pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Button(dialog, text="Calibrar Sensor de Nivel", 
                  command=lambda: self.calibrar_nivel(dialog)).pack(fill=tk.X, padx=20, pady=5)
    
    def calibrar_caudal(self, parent):
        """Calibración de sensores de caudal"""
        cal_dialog = tk.Toplevel(parent)
        cal_dialog.title("Calibrar Sensores de Caudal")
        
        ttk.Label(cal_dialog, text="Seleccione tubería a calibrar:").pack(pady=10)
        
        tuberias_frame = ttk.Frame(cal_dialog)
        tuberias_frame.pack()
        
        for i in range(0, 11, 3):  # Mostrar 3 por fila
            row_frame = ttk.Frame(tuberias_frame)
            row_frame.pack()
            for j in range(3):
                if i + j < 11:
                    ttk.Button(
                        row_frame, 
                        text=f"Tubería {i+j+1}", 
                        width=10,
                        command=lambda n=i+j: self.calibrar_tuberia_individual(n+1, cal_dialog)
                    ).pack(side=tk.LEFT, padx=5, pady=5)
    
    def calibrar_tuberia_individual(self, num_tuberia, parent):
        """Calibración individual de una tubería"""
        cal_dialog = tk.Toplevel(parent)
        cal_dialog.title(f"Calibrar Tubería {num_tuberia}")
        
        ttk.Label(cal_dialog, text=f"Introduzca el valor real para Tubería {num_tuberia}:").pack(pady=10)
        
        valor_entry = ttk.Entry(cal_dialog)
        valor_entry.pack(pady=5)
        
        def aplicar_calibracion():
            try:
                valor_real = float(valor_entry.get())
                # Aquí iría la lógica real de calibración
                messagebox.showinfo(
                    "Calibración", 
                    f"Tubería {num_tuberia} calibrada con valor {valor_real:.2f}"
                )
                cal_dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un valor numérico válido")
        
        ttk.Button(cal_dialog, text="Aplicar", command=aplicar_calibracion).pack(pady=10)
    
    def calibrar_nivel(self, parent):
        """Calibración del sensor de nivel"""
        cal_dialog = tk.Toplevel(parent)
        cal_dialog.title("Calibrar Sensor de Nivel")
        
        ttk.Label(cal_dialog, text="Introduzca el nivel real medido manualmente:").pack(pady=10)
        
        nivel_entry = ttk.Entry(cal_dialog)
        nivel_entry.pack(pady=5)
        
        def aplicar_calibracion():
            try:
                nivel_real = float(nivel_entry.get())
                # Aquí iría la lógica real de calibración
                messagebox.showinfo(
                    "Calibración", 
                    f"Sensor de nivel calibrado con valor {nivel_real:.2f} m"
                )
                cal_dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un valor numérico válido")
        
        ttk.Button(cal_dialog, text="Aplicar", command=aplicar_calibracion).pack(pady=10)
    
    def iniciar_serial(self):
        """Inicia la conexión serial con Arduino"""
        try:
            self.serial_connection = serial.Serial(
                port=self.config['serial_port'],
                baudrate=self.config['baudrate'],
                timeout=1
            )
            self.serial_running = True
            self.serial_thread = Thread(target=self.leer_serial)
            self.serial_thread.daemon = True
            self.serial_thread.start()
            self.actualizar_status(f"Conectado a {self.config['serial_port']} a {self.config['baudrate']} baudios")
        except Exception as e:
            self.actualizar_status(f"Error serial: {str(e)}", error=True)
    
    def leer_serial(self):
        """Lee datos del puerto serial en un hilo separado"""
        while self.serial_running:
            if self.serial_connection and self.serial_connection.in_waiting:
                try:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    self.serial_queue.put(line)
                except Exception as e:
                    self.serial_queue.put(f"ERROR:{str(e)}")
            time.sleep(0.1)
    
    def procesar_datos_serial(self):
        """Procesa los datos recibidos por serial"""
        while not self.serial_queue.empty():
            data = self.serial_queue.get()
            
            if data.startswith("CAUDAL:"):
                # Formato esperado: CAUDAL:1,5.23;2,0.0;...;11,3.45
                try:
                    partes = data[7:].split(';')
                    for parte in partes:
                        if ',' in parte:
                            id_tuberia, caudal = parte.split(',')
                            id_tuberia = int(id_tuberia) - 1  # Convertir a índice 0-based
                            if 0 <= id_tuberia < 11:
                                self.tuberias[id_tuberia]['caudal'] = float(caudal)
                                self.tuberias[id_tuberia]['activa'] = float(caudal) > 0.1
                except Exception as e:
                    self.actualizar_status(f"Error procesando datos: {str(e)}", error=True)
            
            elif data.startswith("NIVEL:"):
                try:
                    self.nivel_actual = float(data[6:])
                    self.volumen = self.calcular_volumen()
                except Exception as e:
                    self.actualizar_status(f"Error nivel: {str(e)}", error=True)
    
    def iniciar_video(self):
        """Inicia la captura de video RTSP"""
        try:
            self.video_running = True
            self.video_thread = Thread(target=self.capturar_video)
            self.video_thread.daemon = True
            self.video_thread.start()
            self.actualizar_status(f"Conectando a cámara RTSP...")
        except Exception as e:
            self.actualizar_status(f"Error video: {str(e)}", error=True)
    
    def capturar_video(self):
        """Captura frames de video RTSP en un hilo separado"""
        cap = cv2.VideoCapture(self.config['rtsp_url'])
        
        while self.video_running and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if self.video_queue.empty():
                    try:
                        self.video_queue.put(frame, block=False)
                    except queue.Full:
                        pass
            else:
                self.actualizar_status("Error obteniendo frame de cámara", error=True)
                time.sleep(1)
        
        cap.release()
    
    def actualizar_video(self):
        """Actualiza el frame de video en la GUI"""
        try:
            if not self.video_queue.empty():
                frame = self.video_queue.get(block=False)
                img = Image.fromarray(frame)
                img = img.resize((640, 360), Image.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
        except queue.Empty:
            pass
        except Exception as e:
            self.actualizar_status(f"Error actualizando video: {str(e)}", error=True)
    
    def actualizar_indicador_nivel(self):
        """Dibuja el indicador de nivel del tanque"""
        self.canvas_tanque.delete("all")
        
        # Dibujar tanque
        self.canvas_tanque.create_rectangle(30, 20, 120, 280, outline="black", width=2)
        
        # Calcular nivel de agua (escala 20-280)
        altura_tanque = 260  # 280-20
        nivel_normalizado = ((self.nivel_actual - self.nivel_minimo) / 
                           (self.nivel_maximo - self.nivel_minimo)) * altura_tanque
        nivel_y = 280 - nivel_normalizado
        
        # Dibujar agua
        self.canvas_tanque.create_rectangle(31, nivel_y, 119, 279, 
                                          fill="blue", outline="")
        
        # Marcas de nivel
        for i in range(int(self.nivel_minimo), int(self.nivel_maximo)+1, 5):
            y = 280 - ((i - self.nivel_minimo) / (self.nivel_maximo - self.nivel_minimo)) * altura_tanque
            self.canvas_tanque.create_line(25, y, 30, y, width=1)
            self.canvas_tanque.create_text(20, y, text=str(i), anchor=tk.E)
        
        # Indicador de nivel actual
        self.canvas_tanque.create_text(75, 15, text=f"{self.nivel_actual:.1f} m", 
                                     font=('Arial', 10, 'bold'))
    
    def actualizar_grafico(self):
        """Actualiza el gráfico de variación de nivel"""
        self.ax.clear()
        
        # Generar datos históricos ficticios (24 horas)
        horas = np.arange(0, 24, 0.5)
        niveles = self.nivel_actual + np.sin(horas/2) * 2 + np.random.normal(0, 0.2, len(horas))
        
        self.ax.plot(horas, niveles, 'b-')
        self.ax.set_xlabel('Horas')
        self.ax.set_ylabel('Nivel (m)')
        self.ax.set_title('Variación de Nivel (últimas 24h)')
        self.ax.grid(True)
        
        self.grafico_nivel.draw()
    
    def actualizar_tuberias(self):
        """Actualiza el estado de las tuberías en la interfaz"""
        for i, widget in enumerate(self.tuberia_widgets):
            tuberia = self.tuberias[i]
            
            # Limpiar canvas
            widget['canvas'].delete("all")
            
            # Dibujar tubería
            color = "green" if tuberia['activa'] else "red"
            widget['canvas'].create_rectangle(5, 10, 25, 40, fill=color, outline="black")
            widget['canvas'].create_oval(10, 5, 20, 15, fill=color, outline="black")
            widget['canvas'].create_oval(10, 35, 20, 45, fill=color, outline="black")
            
            # Actualizar caudal
            widget['lbl_caudal'].config(text=f"{tuberia['caudal']:.1f} m³/s")
            
            # Resaltar si está inactiva
            if not tuberia['activa']:
                widget['frame'].config(style='Error.TFrame')
            else:
                widget['frame'].config(style='TFrame')
    
    def actualizar_datos_texto(self):
        """Actualiza los datos numéricos"""
        self.lbl_nivel.config(text=f"Nivel: {self.nivel_actual:.2f} m")
        self.lbl_volumen.config(text=f"Volumen: {self.volumen:,.0f} m³")
    
    def verificar_alertas(self):
        """Verifica si hay tuberías inactivas y muestra alertas"""
        for tuberia in self.tuberias:
            if not tuberia['activa'] and not tuberia['alerta_mostrada']:
                messagebox.showwarning(
                    "Alerta de Tubería",
                    f"Tubería {tuberia['id']} no está extrayendo agua!\n"
                    f"Última falla: {tuberia['ultima_falla']}"
                )
                tuberia['alerta_mostrada'] = True
    
    def actualizar_datos(self):
        """Actualiza los datos periódicamente"""
        # Procesar datos seriales si hay
        self.procesar_datos_serial()
        
        # Actualizar video si hay nuevos frames
        self.actualizar_video()
        
        # Actualizar gráficos y datos
        self.actualizar_indicador_nivel()
        self.actualizar_grafico()
        self.actualizar_tuberias()
        self.actualizar_datos_texto()
        
        # Verificar alertas
        self.verificar_alertas()
        
        # Programar próxima actualización
        self.root.after(100, self.actualizar_datos)
    
    def actualizar_status(self, mensaje, error=False):
        """Actualiza la barra de estado"""
        self.status_var.set(mensaje)
        if error:
            self.status_bar.config(background='#ffcccc')
        else:
            self.status_bar.config(background='#f0f0f0')
    
    def reiniciar_serial(self):
        """Reinicia la conexión serial"""
        if self.serial_connection:
            self.serial_running = False
            if self.serial_thread and self.serial_thread.is_alive():
                self.serial_thread.join()
            self.serial_connection.close()
        self.iniciar_serial()
    
    def reiniciar_video(self):
        """Reinicia la conexión de video"""
        self.video_running = False
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join()
        self.iniciar_video()
    
    def salir(self):
        """Cierra la aplicación correctamente"""
        self.serial_running = False
        self.video_running = False
        
        if self.serial_connection:
            self.serial_connection.close()
        
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LagunaApp(root)
    root.mainloop()
