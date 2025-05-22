import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, ttk
from datetime import datetime
import threading
import time
from hospital_lib import (
    cargar_datos,
    cargar_logo,
    llamar_siguiente_paciente,
    obtener_pacientes_espera_consultorio,
    obtener_historial_atencion_consultorio,
    guardar_ultimo_llamado,
    marcar_paciente_atendido,
)
class ModuloConsultorio:
    def __init__(self, consultorio_id):
        self.consultorio_id = str(consultorio_id)
        self.datos = cargar_datos()
        self.app = tb.Window(themename="flatly")
        self.app.title(f"Consultorio {self.consultorio_id} - Hospital de Apoyo Palpa")
        self.app.geometry("1000x700")

        self.setup_ui()
        self.setup_hotkeys()
        self.refresh_data_thread()


    def setup_ui(self):
        header = tb.Frame(self.app, padding=10)
        header.pack(fill="x")

        logo_lbl = cargar_logo(header)
        logo_lbl.pack(side="left", padx=10)

        tb.Label(header, text=f"Consultorio {self.consultorio_id}", font=('Segoe UI', 18, 'bold')).pack(side="left")

        status_frame = tb.Frame(self.app, padding=10, bootstyle="info")
        status_frame.pack(fill="x", padx=20, pady=10)

        tb.Label(status_frame, text="Estado actual:", font=('Segoe UI', 14)).pack(side="left")
        self.status_label = tb.Label(status_frame, text="LIBRE", font=('Segoe UI', 16, 'bold'), bootstyle="success")
        self.status_label.pack(side="left", padx=10)

        self.paciente_label = tb.Label(status_frame, text="", font=('Segoe UI', 14))
        self.paciente_label.pack(side="left", expand=True)

        btn_frame = tb.Frame(self.app, padding=10)
        btn_frame.pack()

        self.btn_llamar = tb.Button(btn_frame, text="Llamar Siguiente (F2)", bootstyle="success-outline", width=20, command=self.llamar_siguiente)
        self.btn_llamar.pack(side="left", padx=5)

        self.btn_rellamar = tb.Button(btn_frame, text="Re-llamar Actual (F4)", bootstyle="primary-outline", width=20, command=self.re_llamar_paciente)
        self.btn_rellamar.pack(side="left", padx=5)

        lists_frame = tb.Frame(self.app, padding=10)
        lists_frame.pack(fill="both", expand=True, padx=20, pady=10)

        espera_frame = tb.Labelframe(lists_frame, text="Pacientes en Espera", bootstyle="secondary")
        espera_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.wait_tree = ttk.Treeview(espera_frame, columns=("ID", "Nombre", "Especialidad - Consultorio"), show="headings", selectmode="browse")
        self.wait_tree.heading("ID", text="ID")
        self.wait_tree.heading("Nombre", text="Nombre")
        self.wait_tree.heading("Especialidad - Consultorio", text="Especialidad - Consultorio")
        self.wait_tree.column("ID", width=40, anchor="center")
        self.wait_tree.column("Nombre", width=200)
        self.wait_tree.column("Especialidad - Consultorio", width=250)
        self.wait_tree.pack(fill="both", expand=True, side="left")

        scrollbar_wait = tb.Scrollbar(espera_frame, command=self.wait_tree.yview, bootstyle="secondary")
        scrollbar_wait.pack(side="right", fill="y")
        self.wait_tree.configure(yscrollcommand=scrollbar_wait.set)

        hist_frame = tb.Labelframe(lists_frame, text="Historial de Hoy", bootstyle="secondary")
        hist_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.hist_tree = ttk.Treeview(hist_frame, columns=("ID", "Nombre", "Especialidad - Consultorio"), show="headings", selectmode="browse")
        self.hist_tree.heading("ID", text="ID")
        self.hist_tree.heading("Nombre", text="Nombre")
        self.hist_tree.heading("Especialidad - Consultorio", text="Especialidad - Consultorio")
        self.hist_tree.column("ID", width=40, anchor="center")
        self.hist_tree.column("Nombre", width=200)
        self.hist_tree.column("Especialidad - Consultorio", width=250)
        self.hist_tree.pack(fill="both", expand=True, side="left")

        scrollbar_hist = tb.Scrollbar(hist_frame, command=self.hist_tree.yview, bootstyle="secondary")
        scrollbar_hist.pack(side="right", fill="y")
        self.hist_tree.configure(yscrollcommand=scrollbar_hist.set)

    def setup_hotkeys(self):
        self.app.bind('<F2>', lambda e: self.llamar_siguiente())
        self.app.bind('<F4>', lambda e: self.re_llamar_paciente())

    def llamar_siguiente(self):
        try:
            paciente = llamar_siguiente_paciente(self.consultorio_id)
            if not paciente:
                messagebox.showinfo("Info", "No hay pacientes en espera para este consultorio", parent=self.app)
                self.status_label.config(text="LIBRE", bootstyle="success")
                self.paciente_label.config(text="")
                return

            self.status_label.config(text="OCUPADO", bootstyle="danger")
            nombre = paciente.get('nombre', '')
            consultorio = paciente.get('consultorio', f"Consultorio {self.consultorio_id}")
            self.paciente_label.config(text=f"Paciente: {nombre} ({consultorio})")

            mensaje = f"Paciente {nombre}, favor pasar al {consultorio}"
            guardar_ultimo_llamado(mensaje)

            marcar_paciente_atendido(paciente['id'], consultorio)

            self.datos = cargar_datos()
            self.actualizar_listas()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo llamar al paciente: {e}", parent=self.app)

    def re_llamar_paciente(self):
        import datetime
        try:
            hist = obtener_historial_atencion_consultorio(self.consultorio_id)
            if not hist:
                messagebox.showinfo("Info", "No hay historial de atenciones para re-llamar", parent=self.app)
                return
            ultimo = sorted(hist, key=lambda x: x.get('fecha_atencion', ''), reverse=True)[0]

            ts = datetime.datetime.now().strftime("%H:%M:%S")
            mensaje = f"{ts} Paciente {ultimo['nombre']}, favor pasar al consultorio {self.consultorio_id}"

            messagebox.showinfo("Re-llamar Paciente", f"Paciente: {ultimo['nombre']}\nConsultorio: {self.consultorio_id}", parent=self.app)

            guardar_ultimo_llamado(mensaje)

            self.datos = cargar_datos()
            self.actualizar_listas()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo re-llamar al paciente: {e}", parent=self.app)


    def actualizar_listas(self):
        self.wait_tree.delete(*self.wait_tree.get_children())
        self.hist_tree.delete(*self.hist_tree.get_children())

        try:
            espera = obtener_pacientes_espera_consultorio(self.consultorio_id)
            if espera:
                for p in espera:
                    hora = self._formatear_hora(p.get('fecha_registro'))
                    especialidad = p.get('especialidad', '')
                    consultorio = p.get('consultorio', '')
                    self.wait_tree.insert("", "end", values=(p['id'], p['nombre'], f"{especialidad} - {consultorio}"))
            else:
                self.wait_tree.insert("", "end", values=("", "Sin pacientes en espera", ""))

            hist = obtener_historial_atencion_consultorio(self.consultorio_id)
            if hist:
                for p in hist:
                    hora = self._formatear_hora(p.get('fecha_atencion'))
                    especialidad = p.get('especialidad', '')
                    consultorio = p.get('consultorio', '')
                    self.hist_tree.insert("", "end", values=(p['id'], p['nombre'], f"{especialidad} - {consultorio}"))
            else:
                self.hist_tree.insert("", "end", values=("", "Sin historial de hoy", ""))
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar listas: {e}", parent=self.app)

    def _formatear_hora(self, fecha):
        if not fecha:
            return ""
        if hasattr(fecha, 'strftime'):
            return fecha.strftime("%H:%M")
        if isinstance(fecha, str) and ' ' in fecha:
            return fecha.split(' ')[1][:5]
        return ""

    def refresh_data_thread(self):
        def refrescar():
            while True:
                try:
                    self.datos = cargar_datos()
                    self.actualizar_listas()
                except Exception as e:
                    print(f"Error al refrescar datos: {e}")
                time.sleep(3)
        threading.Thread(target=refrescar, daemon=True).start()

    def run(self):
        self.app.protocol("WM_DELETE_WINDOW", self.app.destroy)
        self.app.mainloop()

if __name__ == "__main__":
    import tkinter.simpledialog as simpledialog
    consultorio_id = simpledialog.askstring("Consultorio", "Ingrese el número (1-14):")
    if consultorio_id:
        try:
            app = ModuloConsultorio(consultorio_id)
            app.run()
        except Exception as e:
            messagebox.showerror("Error de Inicialización", f"No se pudo iniciar la aplicación: {e}")



