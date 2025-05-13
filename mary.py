import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from fpdf import FPDF
from mpl_toolkits.mplot3d import Axes3D
import io
from PIL import Image

def calcular_volumen(cotas, areas, nivel_agua):
    volumen_total = 0
    for i in range(len(cotas) - 1):
        cota1, cota2 = cotas[i], cotas[i + 1]
        area1, area2 = areas[i], areas[i + 1]

        if nivel_agua >= cota2:
            h = cota2 - cota1
            V = (h / 3) * (area1 + area2 + np.sqrt(area1 * area2))
            volumen_total += V

        elif nivel_agua > cota1:
            h_parcial = nivel_agua - cota1
            area_parcial = area1 + (area2 - area1) * ((nivel_agua - cota1) / (cota2 - cota1))
            V = (h_parcial / 3) * (area1 + area_parcial + np.sqrt(area1 * area_parcial))
            volumen_total += V
            break

        else:
            break

    return volumen_total

def graficar_volumen_vs_nivel(cotas, areas, frame, save_path=None):
    niveles = np.linspace(min(cotas), max(cotas), 100)
    volumenes = [calcular_volumen(cotas, areas, nivel) for nivel in niveles]

    fig, ax = plt.subplots(figsize=(6,4))
    ax.plot(niveles, volumenes, 'b-', lw=2)
    ax.set_title('Curva Volumen vs Nivel del agua')
    ax.set_xlabel('Nivel del agua (m)')
    ax.set_ylabel('Volumen (m³)')
    ax.grid(True)

    if save_path:
        fig.savefig(save_path)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

def exportar_excel(cotas, areas, img3d_path=None):
    df = pd.DataFrame({"Cota (m)": cotas, "Área (m²)": areas})
    df = df.sort_values("Cota (m)")
    with pd.ExcelWriter("datos_laguna.xlsx") as writer:
        df.to_excel(writer, sheet_name='Datos Laguna', index=False)
        if img3d_path:
            worksheet = writer.book.add_worksheet('Modelo 3D')
            worksheet.insert_image('B2', img3d_path)
    messagebox.showinfo("Exportación exitosa", "Datos exportados a 'datos_laguna.xlsx'")

def exportar_pdf(cotas, areas, img3d_path=None):
    niveles = np.linspace(min(cotas), max(cotas), 100)
    volumenes = [calcular_volumen(cotas, areas, nivel) for nivel in niveles]

    plt.figure(figsize=(6,4))
    plt.plot(niveles, volumenes, 'b-', lw=2)
    plt.title('Curva Volumen vs Nivel del agua')
    plt.xlabel('Nivel del agua (m)')
    plt.ylabel('Volumen (m³)')
    plt.grid(True)
    plt.savefig("grafico_volumen.png")
    plt.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Datos Batimetría Laguna", ln=True, align='C')

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Cotas y Áreas:", ln=True)
    for cota, area in sorted(zip(cotas, areas)):
        pdf.cell(0, 8, f"Cota: {cota} m - Área: {area} m²", ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, "Curva Volumen vs Nivel:", ln=True)
    pdf.image("grafico_volumen.png", w=170)

    if img3d_path:
        pdf.add_page()
        pdf.cell(0, 10, "Modelo 3D de la Laguna:", ln=True)
        pdf.image(img3d_path, w=170)

    pdf.output("reporte_laguna.pdf")
    messagebox.showinfo("Exportación exitosa", "Reporte exportado a 'reporte_laguna.pdf'")

def graficar_3d_laguna(cotas, areas, save_path=None):
    cotas_sorted, areas_sorted = zip(*sorted(zip(cotas, areas)))
    radii = np.sqrt(np.array(areas_sorted) / np.pi)

    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(111, projection='3d')

    theta = np.linspace(0, 2*np.pi, 50)
    Theta, Z = np.meshgrid(theta, cotas_sorted)
    R = np.tile(radii, (50,1)).T

    X = R * np.cos(Theta)
    Y = R * np.sin(Theta)

    ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
    ax.set_title('Modelo 3D de la Laguna (batimetría)')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Cota (m)')

    if save_path:
        plt.savefig(save_path)
    plt.show()

def ejecutar_calculo(entry_nivel, cotas, areas, frame_grafico):
    try:
        nivel_agua = float(entry_nivel.get())
        volumen = calcular_volumen(cotas, areas, nivel_agua)
        messagebox.showinfo("Resultado", f"El volumen hasta el nivel {nivel_agua} m es: {volumen:.2f} m³")

        for widget in frame_grafico.winfo_children():
            widget.destroy()
        graficar_volumen_vs_nivel(cotas, areas, frame_grafico)

    except ValueError:
        messagebox.showerror("Error", "Ingrese un valor numérico válido para el nivel de agua.")

def agregar_dato(tree, cotas, areas, entry_cota, entry_area):
    try:
        cota = float(entry_cota.get())
        area = float(entry_area.get())
        cotas.append(cota)
        areas.append(area)
        tree.insert("", "end", values=(cota, area))
        entry_cota.delete(0, tk.END)
        entry_area.delete(0, tk.END)
    except ValueError:
        messagebox.showerror("Error", "Ingrese valores numéricos válidos para cota y área.")

def importar_excel(tree, cotas, areas):
    file_path = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx")])
    if not file_path:
        return

    df = pd.read_excel(file_path)
    if "Cota (m)" not in df.columns or "Área (m²)" not in df.columns:
        messagebox.showerror("Error", "El archivo debe tener las columnas 'Cota (m)' y 'Área (m²)'")
        return

    cotas.clear()
    areas.clear()
    tree.delete(*tree.get_children())

    for _, row in df.iterrows():
        cotas.append(row["Cota (m)"])
        areas.append(row["Área (m²)"])
        tree.insert("", "end", values=(row["Cota (m)"], row["Área (m²)"]))

def main():
    root = tk.Tk()
    root.title("Calculadora de volumen de laguna por batimetría")

    cotas = [2700, 2702, 2705, 2710, 2715]
    areas = [1000, 2500, 4000, 6000, 9000]

    frame_input = tk.Frame(root)
    frame_input.pack(pady=10)

    tk.Label(frame_input, text="Cota (m):").grid(row=0, column=0, padx=5)
    entry_cota = tk.Entry(frame_input, width=10)
    entry_cota.grid(row=0, column=1, padx=5)

    tk.Label(frame_input, text="Área (m²):").grid(row=0, column=2, padx=5)
    entry_area = tk.Entry(frame_input, width=10)
    entry_area.grid(row=0, column=3, padx=5)

    tree = ttk.Treeview(root, columns=("Cota", "Área"), show='headings', height=5)
    tree.heading("Cota", text="Cota (m)")
    tree.heading("Área", text="Área (m²)")
    tree.pack(pady=10)

    for c, a in zip(cotas, areas):
        tree.insert("", "end", values=(c, a))

    btn_agregar = tk.Button(frame_input, text="Agregar", command=lambda: agregar_dato(tree, cotas, areas, entry_cota, entry_area))
    btn_agregar.grid(row=0, column=4, padx=5)

    btn_importar = tk.Button(frame_input, text="Importar desde Excel", command=lambda: importar_excel(tree, cotas, areas))
    btn_importar.grid(row=0, column=5, padx=5)

    frame_nivel = tk.Frame(root)
    frame_nivel.pack(pady=10)

    tk.Label(frame_nivel, text="Nivel actual del agua (m):").pack(side=tk.LEFT)
    entry_nivel = tk.Entry(frame_nivel, width=10)
    entry_nivel.pack(side=tk.LEFT, padx=5)

    frame_grafico = tk.Frame(root)
    frame_grafico.pack(pady=10)

    btn_calcular = tk.Button(root, text="Calcular Volumen y Graficar", command=lambda: ejecutar_calculo(entry_nivel, cotas, areas, frame_grafico))
    btn_calcular.pack(pady=5)

    frame_export = tk.Frame(root)
    frame_export.pack(pady=5)

    btn_3d = tk.Button(root, text="Visualizar Modelo 3D", command=lambda: graficar_3d_laguna(cotas, areas))
    btn_3d.pack(pady=5)

    img3d_path = "modelo_3d_laguna.png"

    btn_export_excel = tk.Button(frame_export, text="Exportar a Excel", command=lambda: [graficar_3d_laguna(cotas, areas, img3d_path), exportar_excel(cotas, areas, img3d_path)])
    btn_export_excel.pack(side=tk.LEFT, padx=5)

    btn_export_pdf = tk.Button(frame_export, text="Exportar a PDF", command=lambda: [graficar_3d_laguna(cotas, areas, img3d_path), exportar_pdf(cotas, areas, img3d_path)])
    btn_export_pdf.pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    main()
