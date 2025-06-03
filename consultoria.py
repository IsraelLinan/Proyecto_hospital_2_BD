import tkinter as tk
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
        print("Iniciando módulo consultorio...")  # Diagnóstico
        self.consultorio_id = str(consultorio_id)
        self.datos = cargar_datos()
        print(f"Datos cargados: {len(self.datos.get('pacientes', []))} pacientes")  # Diagnóstico
        self.app = tb.Window(themename="flatly")
        self.app.title(f"Consultorio {self.consultorio_id} - Hospital de Apoyo Palpa")
        self.app.geometry("1000x700")

        self.setup_ui()
        print("Interfaz configurada")  # Diagnóstico
        self.setup_hotkeys()
        self.refresh_data_thread()
        print("Hilo de refresco iniciado")  # Diagnóstico

    def setup_ui(self):
        print("Configurando UI...")  # Diagnóstico
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
        print("UI configurada completamente")  # Diagnóstico

    def setup_hotkeys(self):
        print("Configurando hotkeys...")  # Diagnóstico
        self.app.bind('<F2>', lambda e: self.llamar_siguiente())
        self.app.bind('<F4>', lambda e: self.re_llamar_paciente())
        print("Hotkeys configuradas")  # Diagnóstico

    def llamar_siguiente(self):
        print("Intentando llamar siguiente paciente...")  # Diagnóstico
        try:
            paciente = llamar_siguiente_paciente(self.consultorio_id)
            if not paciente:
               messagebox.showinfo("Info", "No hay pacientes en espera para este consultorio", parent=self.app)
               self.status_label.config(text="LIBRE", bootstyle="success")
               self.paciente_label.config(text="")
               print("No hay pacientes en espera")  # Diagnóstico
               return

            self.status_label.config(text="OCUPADO", bootstyle="danger")
            nombre = paciente.get('nombre', '')
            consultorio = paciente.get('consultorio', f"Consultorio {self.consultorio_id}")
            self.paciente_label.config(text=f"Paciente: {nombre} ({consultorio})")
            mensaje = f"Paciente {nombre}, favor pasar al {consultorio}"
            guardar_ultimo_llamado(mensaje)

            # USAR paciente['paciente_id'] SIEMPRE
            marcar_paciente_atendido(paciente['paciente_id'], consultorio)

            self.datos = cargar_datos()
            self.actualizar_listas()
            print(f"Llamado a paciente {nombre}")  # Diagnóstico
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo llamar al paciente: {e}", parent=self.app)
            print(f"Error en llamar_siguiente: {e}")  # Diagnóstico

    def re_llamar_paciente(self):
        import datetime
        print("Intentando re-llamar paciente...")  # Diagnóstico
        try:
            selected = self.hist_tree.selection()
            if selected:
               item = self.hist_tree.item(selected[0])
               vals = item['values']
               paciente_nombre = vals[1]
               consultorio = self.consultorio_id
               # Puedes personalizar el mensaje aquí:
               ts = datetime.datetime.now().strftime("%H:%M:%S")
               mensaje = f"{ts} Paciente {paciente_nombre}, favor pasar al consultorio {consultorio}"
               messagebox.showinfo("Re-llamar Paciente", f"Paciente: {paciente_nombre}\nConsultorio: {consultorio}", parent=self.app)
               guardar_ultimo_llamado(mensaje)
               self.datos = cargar_datos()
               self.actualizar_listas()
               print(f"Re-llamado a paciente {paciente_nombre}")  # Diagnóstico
            else:
                # Si no hay selección, puedes seguir usando el último del historial como antes:
                hist = obtener_historial_atencion_consultorio(self.consultorio_id)
                if not hist:
                    messagebox.showinfo("Info", "No hay historial de atenciones para re-llamar", parent=self.app)
                    print("No hay historial para re-llamar")  # Diagnóstico
                    return
                ultimo = sorted(hist, key=lambda x: x.get('fecha_atencion', ''), reverse=True)[0]
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                mensaje = f"{ts} Paciente {ultimo['nombre']}, favor pasar al consultorio {self.consultorio_id}"
                messagebox.showinfo("Re-llamar Paciente", f"Paciente: {ultimo['nombre']}\nConsultorio: {self.consultorio_id}", parent=self.app)
                guardar_ultimo_llamado(mensaje)
                self.datos = cargar_datos()
                self.actualizar_listas()
                print(f"Re-llamado a paciente {ultimo['nombre']}")  # Diagnóstico
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo re-llamar al paciente: {e}", parent=self.app)
            print(f"Error en re_llamar_paciente: {e}")  # Diagnóstico

    def actualizar_listas(self):
        print("Actualizando listas...")  # Diagnóstico
        self.wait_tree.delete(*self.wait_tree.get_children())
        self.hist_tree.delete(*self.hist_tree.get_children())

        try:
            espera = obtener_pacientes_espera_consultorio(self.consultorio_id)
            if espera:
               for p in espera:
                   especialidad = p.get('especialidad', '')
                   consultorio = p.get('consultorio', '')
                   self.wait_tree.insert("", "end", values=(
                      p['paciente_id'], p['nombre'], f"{especialidad} - {consultorio}"
                ))
            else:
                self.wait_tree.insert("", "end", values=("", "Sin pacientes en espera", ""))

            hist = obtener_historial_atencion_consultorio(self.consultorio_id)
            if hist:
               print("Historial recibido ordenado por fecha_atencion DESC:")
               for p in hist:
                   print(f"{p['paciente_id']} - {p['nombre']} - {p['fecha_atencion']}")  # Debug

                # Insertar los pacientes tal cual vienen en la lista (debería ser descendente)
               for p in hist:
                   especialidad = p.get('especialidad', '')
                   consultorio = p.get('consultorio', '')
                   self.hist_tree.insert("", "end", values=(
                       p['paciente_id'], p['nombre'], f"{especialidad} - {consultorio}"
                ))
            else:
                self.hist_tree.insert("", "end", values=("", "Sin historial de hoy", ""))

            print("Listas actualizadas correctamente")  # Diagnóstico
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar listas: {e}", parent=self.app)
            print(f"Error en actualizar_listas: {e}")  # Diagnóstico


    def _formatear_hora(self, fecha):
        if not fecha:
            return ""
        if hasattr(fecha, 'strftime'):
            return fecha.strftime("%H:%M")
        if isinstance(fecha, str) and ' ' in fecha:
            return fecha.split(' ')[1][:5]
        return ""

    def refresh_data_thread(self):
        print("Iniciando hilo de refresco de datos...")  # Diagnóstico
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
        print("Ejecutando mainloop...")  # Diagnóstico
        self.app.protocol("WM_DELETE_WINDOW", self.app.destroy)
        self.app.mainloop()


class SelectorConsultorioDialog:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Seleccionar Consultorio")
        self.root.geometry("300x150")
        self.root.resizable(False, False)

        self.consultorio_var = tk.IntVar(value=1)

        tk.Label(self.root, text="Seleccione número de consultorio:", font=("Segoe UI", 12)).pack(pady=10)

        self.spin_consultorio = tk.Spinbox(self.root, from_=1, to=20, textvariable=self.consultorio_var, width=5, font=("Segoe UI", 12))
        self.spin_consultorio.pack(pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        btn_aceptar = tk.Button(btn_frame, text="Aceptar", command=self.aceptar)
        btn_aceptar.pack(side="left", padx=10)

        btn_cancelar = tk.Button(btn_frame, text="Cancelar", command=self.cancelar)
        btn_cancelar.pack(side="left", padx=10)

        self.result = None

        self.root.protocol("WM_DELETE_WINDOW", self.cancelar)

        self.root.mainloop()

    def aceptar(self):
        self.result = self.consultorio_var.get()
        self.root.destroy()

    def cancelar(self):
        self.result = None
        self.root.destroy()


if __name__ == "__main__":
    selector = SelectorConsultorioDialog()

    if selector.result is None:
        print("No se seleccionó consultorio. Saliendo...")
        exit()

    print(f"Consultorio seleccionado: {selector.result}")
    app = ModuloConsultorio(selector.result)
    app.run()















