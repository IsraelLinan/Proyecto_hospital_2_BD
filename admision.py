import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog, ttk, Toplevel, StringVar, BooleanVar, Entry, Button
import tkinter as tk  # Import tkinter for scrollbar
from datetime import datetime
import threading
import time
import csv
import pyttsx3
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from sala_espera import SalaEspera #importamos la clase de sala_espera
from hospital_lib import (
    cargar_datos,
    cargar_logo,
    guardar_paciente_multiple_especialidades,
    validar_nombre_paciente,
    obtener_conexion,
    liberar_conexion
)
    
class ModuloAdmision:
    def __init__(self):
        self.datos = cargar_datos()
        self.app = tb.Window(themename="flatly")
        self.app.title("Sistema de Admisión - Hospital de Apoyo Palpa")
        self.app.geometry("900x700")
        self.app.minsize(700, 600)
        
        # Inicializamos pyttsx3 para la síntesis de voz
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Establecer la velocidad de la voz
        self.voice_spanish = None

        # Buscar y seleccionar la voz en español
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "Spanish" in voice.name:
                self.voice_spanish = voice.id
                self.engine.setProperty('voice', self.voice_spanish)
                break

        self.especialidades = [esp['nombre'] for esp in self.datos['especialidades']]
        self.consultorios = [f"Consultorio {i}" for i in range(1, 15)]
        self.nombre_personal_llamar = None  # Variable para almacenar el nombre temporalmente

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

        tb.Label(form_frame, text="Especialidad Médica:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", pady=8, padx=5)
        self.especialidad_var = StringVar()
        self.especialidad_entry = tb.Entry(form_frame, textvariable=self.especialidad_var, state="readonly", bootstyle="secondary")
        self.especialidad_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.especialidad_entry.bind("<Button-1>", lambda e: self.abrir_popup_especialidades())

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
        
        # Botón "Atención Personal" centrado
        btn_atencion_personal_frame = tb.Frame(main_frame)
        btn_atencion_personal_frame.pack(pady=(10, 20), fill="x", anchor="center")
        self.btn_atencion_personal = tb.Button(btn_atencion_personal_frame, text="Perifoneo Personal", bootstyle="info-outline", command=self.abrir_popup_atencion)
        self.btn_atencion_personal.pack()
        
        self.app.bind("<Return>", lambda e: self.registrar_paciente())
        
        self.app.mainloop()

    def abrir_popup_atencion(self):
        popup = Toplevel(self.app)
        popup.title("Llamar al Personal")
        popup.geometry("300x250")  # Aumenta el tamaño de la ventana si es necesario

        nombre_label = tb.Label(popup, text="Nombre del Personal:", font=("Segoe UI", 12))
        nombre_label.pack(pady=10)
        nombre_entry = tb.Entry(popup, width=30)
        nombre_entry.pack(pady=5)
        
        mensaje_label = tb.Label(popup, text="Mensaje de Perifoneo:", font=("Segoe UI", 12))
        mensaje_label.pack(pady=10)
        mensaje_entry = tb.Entry(popup, width=30)
        mensaje_entry.pack(pady=5)

        def llamar_personal():
            
            nombre_personal = nombre_entry.get().strip()
            mensaje_perifoneo = mensaje_entry.get().strip()
            if nombre_personal and mensaje_perifoneo:
                self.nombre_personal_llamar = nombre_personal  # Guardar el nombre temporalmente
                popup.destroy() # Cerrar el popup sin abrir Sala de Espera
                mensaje = f"Atención al personal: {self.nombre_personal_llamar}. {mensaje_perifoneo}"
                self.reproducir_llamado(mensaje)  # Reproducir el mensaje en la misma ventana
                         
            else:
                tk.messagebox.showerror("Error", "El nombre no puede estar vacío", parent=popup)

        llamar_btn = tb.Button(popup, text="Llamar", bootstyle="success", command=llamar_personal)
        llamar_btn.pack(pady=10)   
    
    def reproducir_llamado(self, mensaje):
        try:
            print(f"Reproduciendo mensaje: {mensaje}")
            self.engine.say(mensaje)  # Usamos pyttsx3 para reproducir el mensaje
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error al reproducir mensaje: {e}") 

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

        btn_editar = tb.Button(btn_frame, text="Editar Paciente", bootstyle="warning-outline", width=15,
                               command=lambda: self.editar_paciente_popup(tree))
        btn_editar.pack(side="left", padx=5)

        btn_actualizar = tb.Button(btn_frame, text="Actualizar Lista", bootstyle="info-outline", width=15,
                                   command=lambda: llenar_tabla(filtrar_pacientes()))
        btn_actualizar.pack(side="left", padx=5)

        columnas = ("ID", "Nombre", "Especialidad", "Consultorio", "Fecha Registro", "Atendido", "Fecha Atención")

        # Contenedor para Treeview + scrollbar
        contenedor = tb.Frame(frame)
        contenedor.pack(fill="both", expand=True)

        tree = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse")
        tree.grid(row=0, column=0, sticky="nsew")

        vsb = tk.Scrollbar(contenedor, orient="vertical", command=tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")

        tree.configure(yscrollcommand=vsb.set)

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

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
            self.datos = cargar_datos()  # Recarga datos actualizados
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

    def editar_paciente_popup(self, tree):
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione un paciente para editar.", parent=self.app)
            return
        
        item = tree.item(seleccion[0])
        valores = item['values']
        paciente_id = valores[0]

        nombre_actual = valores[1]
        especialidad_actual = valores[2]
        consultorio_actual = valores[3]

        popup = tb.Toplevel(self.app)
        popup.title(f"Editar paciente ID {paciente_id}")
        popup.geometry("400x300")
        popup.grab_set()

        tb.Label(popup, text="Nombre:", font=("Segoe UI", 12)).pack(pady=5)
        nombre_var = tb.StringVar(value=nombre_actual)
        nombre_entry = tb.Entry(popup, textvariable=nombre_var, bootstyle="info")
        nombre_entry.pack(fill="x", padx=20)

        tb.Label(popup, text="Especialidad:", font=("Segoe UI", 12)).pack(pady=5)
        especialidad_var = tb.StringVar(value=especialidad_actual)
        especialidad_combo = tb.Combobox(popup, values=self.especialidades, textvariable=especialidad_var, state="readonly")
        especialidad_combo.pack(fill="x", padx=20)

        tb.Label(popup, text="Consultorio:", font=("Segoe UI", 12)).pack(pady=5)
        consultorios_list = [f"Consultorio {i}" for i in range(1, 15)]
        consultorio_var = tb.StringVar(value=consultorio_actual)
        consultorio_combo = tb.Combobox(popup, values=consultorios_list, textvariable=consultorio_var, state="readonly")
        consultorio_combo.pack(fill="x", padx=20)

        def guardar_cambios():
            nuevo_nombre = nombre_var.get().strip()
            nueva_esp = especialidad_var.get()
            nuevo_cons = consultorio_var.get()

            if not nuevo_nombre or len(nuevo_nombre) < 3:
                messagebox.showerror("Error", "El nombre debe tener al menos 3 caracteres.", parent=popup)
                return
            if not nueva_esp:
                messagebox.showerror("Error", "Debe seleccionar una especialidad.", parent=popup)
                return
            if not nuevo_cons:
                messagebox.showerror("Error", "Debe seleccionar un consultorio.", parent=popup)
                return

            try:
                self.actualizar_paciente(paciente_id, nuevo_nombre, nueva_esp, nuevo_cons)
                messagebox.showinfo("Éxito", "Paciente actualizado correctamente.", parent=popup)
                popup.destroy()
                self.datos = cargar_datos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el paciente: {e}", parent=popup)

        btn_guardar = tb.Button(popup, text="Guardar Cambios", bootstyle="success", command=guardar_cambios)
        btn_guardar.pack(pady=20)

    def actualizar_paciente(self, paciente_id, nuevo_nombre, nueva_especialidad, nuevo_consultorio):
        conexion = None
        try:
            conexion = obtener_conexion()
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE pacientes SET nombre = %s WHERE id = %s", (nuevo_nombre, paciente_id))

                cursor.execute("SELECT id FROM especialidades WHERE nombre = %s", (nueva_especialidad,))
                esp_id = cursor.fetchone()
                if not esp_id:
                    raise Exception("Especialidad no encontrada")
                esp_id = esp_id[0]

                cursor.execute("""
                    UPDATE pacientes_especialidades 
                    SET especialidad_id = %s, consultorio = %s 
                    WHERE paciente_id = %s
                """, (esp_id, nuevo_consultorio, paciente_id))

                conexion.commit()
        except Exception as e:
            if conexion:
                conexion.rollback()
            raise e
        finally:
            if conexion:
                liberar_conexion(conexion)

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    app = ModuloAdmision()
    app.run()














