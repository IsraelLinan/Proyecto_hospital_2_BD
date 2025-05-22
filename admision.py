import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog, ttk, Toplevel, StringVar, BooleanVar
from datetime import datetime
import threading
import time
import csv
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from hospital_lib import (
    cargar_datos,
    cargar_logo,
    guardar_paciente_multiple_especialidades,
    validar_nombre_paciente,
)

class ModuloAdmision:
    def __init__(self):
        self.datos = cargar_datos()
        self.app = tb.Window(themename="flatly")
        self.app.title("Sistema de Admisión - Hospital de Apoyo Palpa")
        self.app.geometry("900x700")
        self.app.minsize(700, 600)

        self.especialidades = [esp['nombre'] for esp in self.datos['especialidades']]
        self.consultorios = [f"Consultorio {i}" for i in range(1, 15)]

        self.seleccion_especialidades = []
        self.seleccion_consultorios = []

        self.setup_ui()
        threading.Thread(target=self.sincronizar_datos_periodicamente, daemon=True).start()

    def setup_ui(self):
        main_frame = tb.Frame(self.app, padding=20)
        main_frame.pack(fill="both", expand=True)

        logo_frame = tb.Frame(main_frame)
        logo_frame.pack(pady=(0,20))
        logo_label = cargar_logo(logo_frame)
        logo_label.pack()

        tb.Label(main_frame, text="Registro de Pacientes", 
                 font=("Segoe UI", 20, "bold")).pack(pady=(0,15))

        form_frame = tb.Frame(main_frame)
        form_frame.pack(fill="x", pady=10)

        tb.Label(form_frame, text="Nombre del Paciente:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", pady=8, padx=5)
        self.nombre_entry = tb.Entry(form_frame, width=45, bootstyle="info")
        self.nombre_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.nombre_entry.focus()

        # Especialidades: Entry readonly que abre popup al click
        tb.Label(form_frame, text="Especialidad Médica:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", pady=8, padx=5)
        self.especialidad_var = StringVar()
        self.especialidad_entry = tb.Entry(form_frame, textvariable=self.especialidad_var, state="readonly", bootstyle="secondary")
        self.especialidad_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.especialidad_entry.bind("<Button-1>", lambda e: self.abrir_popup_especialidades())

        # Consultorios: Entry readonly que abre popup al click
        tb.Label(form_frame, text="Consultorio:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", pady=8, padx=5)
        self.consultorio_var = StringVar()
        self.consultorio_entry = tb.Entry(form_frame, textvariable=self.consultorio_var, state="readonly", bootstyle="secondary")
        self.consultorio_entry.grid(row=2, column=1, sticky="ew", padx=5)
        self.consultorio_entry.bind("<Button-1>", lambda e: self.abrir_popup_consultorios())

        form_frame.columnconfigure(1, weight=1)

        self.info_label = tb.Label(main_frame, text="", font=("Segoe UI", 11), bootstyle="success")
        self.info_label.pack(pady=10)

        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(pady=20)

        self.btn_registrar = tb.Button(btn_frame, text="Registrar Paciente", bootstyle="success-outline", command=self.registrar_paciente)
        self.btn_registrar.pack(side="left", padx=10)

        self.btn_reporte = tb.Button(btn_frame, text="Ver Reporte", bootstyle="secondary-outline", command=self.mostrar_reporte)
        self.btn_reporte.pack(side="left", padx=10)

        self.app.bind("<Return>", lambda e: self.registrar_paciente())

    def abrir_popup_especialidades(self):
        popup = Toplevel(self.app)
        popup.title("Seleccionar Especialidades")
        popup.geometry("300x400")

        vars_check = []
        for esp in self.especialidades:
            var = BooleanVar(value=esp in self.seleccion_especialidades)
            chk = tb.Checkbutton(popup, text=esp, variable=var)
            chk.pack(anchor="w", pady=2, padx=5)
            vars_check.append((var, esp))

        def guardar_seleccion():
            self.seleccion_especialidades = [esp for var, esp in vars_check if var.get()]
            self.especialidad_var.set(", ".join(self.seleccion_especialidades) if self.seleccion_especialidades else "")
            popup.destroy()

        btn_guardar = tb.Button(popup, text="Guardar", bootstyle="success", command=guardar_seleccion)
        btn_guardar.pack(pady=10)

    def abrir_popup_consultorios(self):
        popup = Toplevel(self.app)
        popup.title("Seleccionar Consultorios")
        popup.geometry("300x400")

        vars_check = []
        for cons in self.consultorios:
            var = BooleanVar(value=cons in self.seleccion_consultorios)
            chk = tb.Checkbutton(popup, text=cons, variable=var)
            chk.pack(anchor="w", pady=2, padx=5)
            vars_check.append((var, cons))

        def guardar_seleccion():
            self.seleccion_consultorios = [cons for var, cons in vars_check if var.get()]
            self.consultorio_var.set(", ".join(self.seleccion_consultorios) if self.seleccion_consultorios else "")
            popup.destroy()

        btn_guardar = tb.Button(popup, text="Guardar", bootstyle="success", command=guardar_seleccion)
        btn_guardar.pack(pady=10)

    def sincronizar_datos_periodicamente(self):
        while True:
            try:
                nuevos_datos = cargar_datos()
                if nuevos_datos != self.datos:
                    self.datos = nuevos_datos
            except Exception as e:
                print(f"Error sincronizando datos: {e}")
            time.sleep(3)

    def registrar_paciente(self):
        nombre = self.nombre_entry.get().strip()
        valido, mensaje = validar_nombre_paciente(nombre)
        if not valido:
            messagebox.showerror("Error", mensaje, parent=self.app)
            return

        if not self.seleccion_especialidades:
            messagebox.showerror("Error", "Debe seleccionar al menos una especialidad", parent=self.app)
            return

        if not self.seleccion_consultorios:
            messagebox.showerror("Error", "Debe seleccionar al menos un consultorio", parent=self.app)
            return

        if len(self.seleccion_especialidades) != len(self.seleccion_consultorios):
            messagebox.showerror("Error", "La cantidad de especialidades y consultorios seleccionados debe coincidir", parent=self.app)
            return

        try:
            paciente_id = guardar_paciente_multiple_especialidades(
                nombre,
                self.seleccion_especialidades,
                self.seleccion_consultorios
            )
            self.datos = cargar_datos()
            self.info_label.config(text=f"Paciente registrado con éxito. Turnos: {len(self.seleccion_especialidades)}")
            self.nombre_entry.delete(0, "end")
            self.especialidad_var.set("")
            self.consultorio_var.set("")
            self.seleccion_especialidades.clear()
            self.seleccion_consultorios.clear()
            self.nombre_entry.focus()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el paciente: {e}", parent=self.app)

    def exportar_csv_func(self, pacientes):
        import csv
        from tkinter import filedialog, messagebox

        if not pacientes:
            messagebox.showwarning("Aviso", "No hay pacientes para exportar.", parent=self.app)
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            parent=self.app,
            title="Guardar reporte CSV"
        )
        if not filepath:
            return

        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Nombre", "Especialidad", "Consultorio", "Fecha Registro", "Atendido", "Fecha Atención"])
                for p in pacientes:
                    writer.writerow([
                        p.get("paciente_id", ""),
                        p.get("nombre", ""),
                        p.get("especialidad", ""),
                        p.get("consultorio", ""),
                        p.get("fecha_registro", ""),
                        "Sí" if p.get("atendido") else "No",
                        p.get("fecha_atencion", "")
                    ])
            messagebox.showinfo("Éxito", "Reporte CSV exportado correctamente.", parent=self.app)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar CSV: {e}", parent=self.app)

    def exportar_pdf_func(self, pacientes):
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from tkinter import filedialog, messagebox

        if not pacientes:
            messagebox.showwarning("Aviso", "No hay pacientes para exportar.", parent=self.app)
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
            parent=self.app,
            title="Guardar reporte PDF"
        )
        if not filepath:
            return

        try:
            doc = SimpleDocTemplate(filepath, pagesize=landscape(letter))
            data = [["ID", "Nombre", "Especialidad", "Consultorio", "Fecha Registro", "Atendido", "Fecha Atención"]]
            for p in pacientes:
                data.append([
                    p.get("paciente_id", ""),
                    p.get("nombre", ""),
                    p.get("especialidad", ""),
                    p.get("consultorio", ""),
                    p.get("fecha_registro", ""),
                    "Sí" if p.get("atendido") else "No",
                    p.get("fecha_atencion", "")
                ])

            table = Table(data)
            style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ])
            table.setStyle(style)

            elems = [table]
            doc.build(elems)

            messagebox.showinfo("Éxito", "Reporte PDF exportado correctamente.", parent=self.app)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar PDF: {e}", parent=self.app)

    def mostrar_reporte(self):
        reporte_win = tb.Toplevel(self.app)
        reporte_win.title("Reporte de Pacientes")
        reporte_win.geometry("950x700")

        frame = tb.Frame(reporte_win, padding=15)
        frame.pack(fill="both", expand=True)

        filtro_frame = tb.Frame(frame)
        filtro_frame.pack(fill="x", pady=(0,10))

        tb.Label(filtro_frame, text="Filtrar Nombre:", width=15).grid(row=0, column=0, padx=5)
        nombre_filtro_var = StringVar()
        nombre_filtro = tb.Entry(filtro_frame, textvariable=nombre_filtro_var, bootstyle="info")
        nombre_filtro.grid(row=0, column=1, padx=5)

        tb.Label(filtro_frame, text="Filtrar Especialidad:", width=18).grid(row=0, column=2, padx=5)
        esp_set = set()
        for p in self.datos.get('pacientes', []):
            esp_str = p.get('especialidad', '')
            if esp_str:
                esp_set.add(esp_str.strip())
        especialidades = sorted(esp_set)
        especialidad_filtro_var = StringVar()
        especialidad_filtro = tb.Combobox(filtro_frame, textvariable=especialidad_filtro_var, values=[""] + especialidades, state="readonly", bootstyle="secondary")
        especialidad_filtro.grid(row=0, column=3, padx=5)

        tb.Label(filtro_frame, text="Filtrar Consultorio:", width=15).grid(row=0, column=4, padx=5)
        cons_set = set()
        for p in self.datos.get('pacientes', []):
            cons_str = p.get('consultorio', '')
            if cons_str:
                cons_set.add(cons_str.strip())
        consultorios = sorted(cons_set)
        consultorio_filtro_var = StringVar()
        consultorio_filtro = tb.Combobox(filtro_frame, textvariable=consultorio_filtro_var, values=[""] + consultorios, state="readonly", bootstyle="secondary")
        consultorio_filtro.grid(row=0, column=5, padx=5)

        filtro_frame.columnconfigure(1, weight=1)
        filtro_frame.columnconfigure(3, weight=1)
        filtro_frame.columnconfigure(5, weight=1)

        btn_frame = tb.Frame(frame)
        btn_frame.pack(anchor="ne", pady=(0,10))

        btn_export_csv = tb.Button(btn_frame, text="Exportar CSV", bootstyle="success-outline", width=15,
                                   command=lambda: self.exportar_csv_func(filtrar_pacientes()))
        btn_export_csv.pack(side="left", padx=5)

        btn_export_pdf = tb.Button(btn_frame, text="Exportar PDF", bootstyle="primary-outline", width=15,
                                   command=lambda: self.exportar_pdf_func(filtrar_pacientes()))
        btn_export_pdf.pack(side="left", padx=5)

        columnas = ("ID", "Nombre", "Especialidad", "Consultorio", "Fecha Registro", "Atendido", "Fecha Atención")

        tree = ttk.Treeview(frame, columns=columnas, show="headings", selectmode="browse")
        tree.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=vsb.set)

        for col in columnas:
            tree.heading(col, text=col)
            tree.column(col, anchor="w", width=130)

        def llenar_tabla(pacientes):
            tree.delete(*tree.get_children())
            for p in pacientes:
                tree.insert("", "end", values=(
                    p.get("paciente_id", ""),
                    p.get("nombre", ""),
                    p.get("especialidad", ""),
                    p.get("consultorio", ""),
                    p.get("fecha_registro", ""),
                    "Sí" if p.get("atendido") else "No",
                    p.get("fecha_atencion", "")
                ))

        def filtrar_pacientes():
            nombre_f = nombre_filtro_var.get().lower()
            esp_f = especialidad_filtro_var.get()
            cons_f = consultorio_filtro_var.get()

            pacientes_filtrados = []
            for p in self.datos.get('pacientes', []):
                nombre_p = p.get('nombre', '').lower()
                if nombre_f and nombre_f not in nombre_p:
                    continue

                esp_p = p.get('especialidad', '')
                if esp_f and esp_f != esp_p:
                    continue

                cons_p = p.get('consultorio', '')
                if cons_f and cons_f != cons_p:
                    continue

                pacientes_filtrados.append(p)
            return pacientes_filtrados

        nombre_filtro_var.trace_add("write", lambda *args: llenar_tabla(filtrar_pacientes()))
        especialidad_filtro_var.trace_add("write", lambda *args: llenar_tabla(filtrar_pacientes()))
        consultorio_filtro_var.trace_add("write", lambda *args: llenar_tabla(filtrar_pacientes()))

        llenar_tabla(self.datos.get('pacientes', []))

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = ModuloAdmision()
    app.run()









