import tkinter as tk
from tkinter import simpledialog, messagebox
import keyboard
from datetime import datetime
from hospital_lib import (
    cargar_datos,
    guardar_datos,
    cargar_logo,
    obtener_especialidad_consultorio,
    obtener_pacientes_espera_consultorio,
    obtener_historial_atencion_consultorio
)

class ModuloConsultorio:
    def __init__(self, consultorio_id):
        try:
            consultorio_id = int(consultorio_id)
            if not 1 <= consultorio_id <= 14:
                raise ValueError("Número de consultorio inválido (debe ser 1-14)")

            # Inicialización de datos
            self.consultorio_id = str(consultorio_id)
            self.archivo_datos = 'datos_hospital.json' #r'\\192.168.10.220\cita_medicas_hap\datos_hospital.json'
            self.datos = cargar_datos(self.archivo_datos)

            # Verificar configuración del consultorio
            especialidad = obtener_especialidad_consultorio(self.datos, self.consultorio_id)
            if not especialidad:
                raise ValueError(f"Consultorio {self.consultorio_id} no está configurado")

            # Interfaz
            self.setup_ui()
            # Atajos de teclado
            self.setup_hotkeys()
            # Listados iniciales
            self.actualizar_listas()
            # Refresco periódico
            self.refresh_data()

        except Exception as e:
            messagebox.showerror("Error de Inicialización", f"No se pudo iniciar el módulo: {e}")
            raise

    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title(f"Consultorio {self.consultorio_id} - Hospital de Apoyo Palpa")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')

        # Encabezado: logo + título
        header = tk.Frame(self.root, bg='#f0f0f0')
        header.pack(fill=tk.X, pady=(10,0))
        logo_lbl = cargar_logo(header)
        logo_lbl.pack(side=tk.LEFT, padx=10)
        tk.Label(header, text=f"Consultorio {self.consultorio_id}",
                 font=('Arial', 16, 'bold'), bg='#f0f0f0').pack(side=tk.LEFT)

        # Estado actual
        sf = tk.Frame(self.root, bd=2, relief=tk.GROOVE, padx=10, pady=10, bg='#ffffff')
        sf.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(sf, text="Estado actual:", font=('Arial', 12), bg='#ffffff').pack(side=tk.LEFT)
        self.status_label = tk.Label(sf, text="LIBRE", font=('Arial', 14, 'bold'),
                                     fg='green', bg='#ffffff')
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.paciente_label = tk.Label(sf, text="", font=('Arial', 12), bg='#ffffff')
        self.paciente_label.pack(side=tk.LEFT, expand=True)

        # Botones
        bf = tk.Frame(self.root, bg='#f0f0f0')
        bf.pack(pady=15)
        tk.Button(bf, text="Llamar Siguiente (F2)", command=self.llamar_siguiente,
                  width=20, bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="Re-llamar Actual (F4)", command=self.re_llamar_paciente,
                  width=20, bg='#2196F3', fg='white').pack(side=tk.LEFT, padx=5)

        # Listas: espera + historial
        lf = tk.Frame(self.root, bg='#f0f0f0')
        lf.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # Panel de Espera (sin scrollbar)
        wf = tk.Frame(lf, bd=2, relief=tk.GROOVE, bg='#ffffff')
        wf.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
        tk.Label(wf, text="Pacientes en Espera", font=('Arial',12,'bold'),
                 bg='#ffffff').pack(pady=5)
        self.wait_listbox = tk.Listbox(wf, font=('Arial',12), selectbackground='#e0e0e0',
                                      width=40, height=20)
        self.wait_listbox.pack(expand=True, fill='both', padx=5, pady=5)
        
        # Panel de Historial (con scrollbar)
        hf = tk.Frame(lf, bd=2, relief=tk.GROOVE, bg='#ffffff')
        hf.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
        tk.Label(hf, text="Historial de Hoy", font=('Arial',12,'bold'),
                 bg='#ffffff').pack(pady=5)
        
        # Frame para el listbox y scrollbar
        hf_inner = tk.Frame(hf, bg='#ffffff')
        hf_inner.pack(expand=True, fill='both', padx=5, pady=5)
        
        self.hist_listbox = tk.Listbox(hf_inner, font=('Arial',12), selectbackground='#e0e0e0',
                                      width=40, height=20)
        scrollbar = tk.Scrollbar(hf_inner, command=self.hist_listbox.yview)
        
        self.hist_listbox.pack(side=tk.LEFT, expand=True, fill='both')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.hist_listbox.config(yscrollcommand=scrollbar.set)

    def setup_hotkeys(self):
        keyboard.add_hotkey('F2', self.llamar_siguiente)
        keyboard.add_hotkey('F4', self.re_llamar_paciente)

    def obtener_pacientes_espera(self):
        return obtener_pacientes_espera_consultorio(self.datos, self.consultorio_id)

    def obtener_historial_atencion(self):
        return obtener_historial_atencion_consultorio(self.datos, self.consultorio_id)

    def llamar_siguiente(self):
        try:
            espera = self.obtener_pacientes_espera()
            if not espera:
                messagebox.showinfo("Info", "No hay pacientes en espera para este consultorio")
                return
            paciente = espera[0]
            for p in self.datos['pacientes']:
                if p['id'] == paciente['id']:
                    p['atendido'] = True
                    p['fecha_atencion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break
            guardar_datos(self.archivo_datos, self.datos)
            self.status_label.config(text="OCUPADO", fg='red')
            self.paciente_label.config(text=f"Paciente: {paciente['nombre']} (Turno {paciente['id']})")
            self.actualizar_listas()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo llamar al paciente: {e}")

    def re_llamar_paciente(self):
        try:
            hist = self.obtener_historial_atencion()
            if not hist:
                messagebox.showinfo("Info", "No hay historial de atenciones para re-llamar")
                return
            # Ordenar por fecha más reciente
            hist_sorted = sorted(
                hist,
                key=lambda x: x.get('fecha_atencion', ''),
                reverse=True
            )
            ultimo = hist_sorted[0]
            mensaje = f"RELLAMADO_Paciente {ultimo['nombre']}, favor pasar al consultorio {self.consultorio_id}"
            self.datos['ultimo_llamado'] = mensaje
            guardar_datos(self.archivo_datos, self.datos)
            messagebox.showinfo("Re-llamar Paciente", f"Paciente: {ultimo['nombre']}\nConsultorio: {self.consultorio_id}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo re-llamar al paciente: {e}")

    def actualizar_listas(self):
        self.wait_listbox.delete(0, tk.END)
        self.hist_listbox.delete(0, tk.END)
        espera = self.obtener_pacientes_espera()
        if espera:
            for p in espera:
                h = p['fecha_registro'].split(' ')[1][:5]
                self.wait_listbox.insert(tk.END, f"{p['id']}. {p['nombre']} ({h})")
        else:
            self.wait_listbox.insert(tk.END, "Sin pacientes en espera")
        hist = self.obtener_historial_atencion()
        if hist:
            for p in hist:
                f = p.get('fecha_atencion', '')
                t = f.split(' ')[1] if f else ''
                self.hist_listbox.insert(tk.END, f"{p['id']}. {p['nombre']} ({t})")
        else:
            self.hist_listbox.insert(tk.END, "Sin historial de hoy")

    def refresh_data(self):
        try:
            self.datos = cargar_datos(self.archivo_datos)
            self.actualizar_listas()
        except Exception as e:
            print(f"Error al refrescar datos: {e}")
        finally:
            self.root.after(3000, self.refresh_data)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        keyboard.unhook_all_hotkeys()
        self.root.destroy()

if __name__ == "__main__":
    consultorio_id = simpledialog.askstring("Consultorio", "Ingrese el número (1-14):")
    if consultorio_id:
        try:
            app = ModuloConsultorio(consultorio_id)
            app.run()
        except Exception as e:
            messagebox.showerror("Error de Inicialización", f"No se pudo iniciar la aplicación: {e}")
