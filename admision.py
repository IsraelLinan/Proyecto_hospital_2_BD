import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from datetime import datetime
import csv
import threading
import time
from hospital_lib import (
    cargar_datos, 
    guardar_datos, 
    cargar_logo,
    validar_nombre_paciente,
    obtener_consultorio_especialidad,
    obtener_especialidad_consultorio
)

class ModuloAdmision:
    def __init__(self):
        self.archivo_datos = 'datos_hospital.json' #r'\\192.168.10.220\cita_medicas_hap\datos_hospital.json'  
        try:
            # Leer los datos una sola vez al inicio
            self.datos = cargar_datos(self.archivo_datos)  
            self.setup_ui()

            # Iniciar la sincronización periódica en un hilo separado
            threading.Thread(target=self.sincronizar_datos_periodicamente, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el módulo: {str(e)}")
            raise

    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Admisión - Hospital de Apoyo Palpa")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.configure(bg='#f0f8ff')

        # Frame para el logo
        logo_frame = tk.Frame(self.root, bg='#f0f8ff')
        logo_frame.pack(pady=20)
        logo_label = cargar_logo(logo_frame)
        logo_label.pack()

        # Frame principal
        main_frame = tk.Frame(self.root, padx=40, pady=40, bg='#f0f8ff')
        main_frame.pack(expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Título
        tk.Label(main_frame,
                text="REGISTRO DE PACIENTES",
                font=('Arial', 16, 'bold'),
                bg='#f0f8ff',
                fg='#0066cc').grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Campos de registro
        self.dibujar_campos_registro(main_frame)

        # Información
        self.info_label = tk.Label(main_frame, text="", font=('Arial', 12), fg='#009688', bg='#f0f8ff')
        self.info_label.grid(row=5, column=0, columnspan=2, pady=10)

        # Botones
        self.dibujar_botones(main_frame)

        # Atajo de teclado
        self.root.bind('<Return>', lambda event: self.registrar_paciente())

    def dibujar_campos_registro(self, main_frame):
        estilo_label = {'font': ('Arial', 12), 'padx': 5, 'pady': 5, 'bg': '#f0f8ff'}
        estilo_entry = {'font': ('Arial', 12), 'width': 40, 'bd': 2, 'relief': tk.SOLID}

        # Nombre
        tk.Label(main_frame, text="Nombre del Paciente:", **estilo_label).grid(row=1, column=0, sticky='w')
        self.nombre_entry = tk.Entry(main_frame, **estilo_entry)
        self.nombre_entry.grid(row=1, column=1, pady=5, sticky='ew')
        self.nombre_entry.focus_set()

        # Especialidad
        tk.Label(main_frame, text="Especialidad Médica:", **estilo_label).grid(row=2, column=0, sticky='w')
        self.especialidad_var = tk.StringVar(self.root)
        self.especialidades = [esp['nombre'] for esp in self.datos['especialidades']]
        self.especialidad_menu = ttk.Combobox(main_frame, textvariable=self.especialidad_var,
                                            values=self.especialidades, state='readonly')
        self.especialidad_menu.config(font=('Arial', 12), width=38)
        self.especialidad_menu.grid(row=2, column=1, pady=5, sticky='ew')
        self.especialidad_menu.bind('<<ComboboxSelected>>', self.actualizar_consultorios_disponibles)

        # Consultorio (ahora es seleccionable)
        tk.Label(main_frame, text="Consultorio:", **estilo_label).grid(row=3, column=0, sticky='w')
        self.consultorio_var = tk.StringVar(self.root)
        self.consultorio_menu = ttk.Combobox(main_frame, textvariable=self.consultorio_var, state='readonly')
        self.consultorio_menu.config(font=('Arial', 12), width=38)
        self.consultorio_menu.grid(row=3, column=1, pady=5, sticky='ew')

        # Inicializar lista de consultorios
        self.actualizar_consultorios_disponibles()

    def actualizar_consultorios_disponibles(self, event=None):
        """Actualiza la lista de consultorios disponibles basado en la especialidad seleccionada"""
        especialidad = self.especialidad_var.get()
        
        # Obtener todos los consultorios disponibles
        todos_consultorios = [f"Consultorio {i}" for i in range(1, 15)]

        if especialidad:
            # Consultorio sugerido para la especialidad
            consultorio_sugerido = obtener_consultorio_especialidad(self.datos, especialidad)
            
            # Configurar los valores del menú de consultorios
            if consultorio_sugerido:
                consultorios_ordenados = [consultorio_sugerido] + \
                                       [c for c in todos_consultorios if c != consultorio_sugerido]
            else:
                consultorios_ordenados = todos_consultorios
        else:
            consultorios_ordenados = todos_consultorios
        
        self.consultorio_menu['values'] = consultorios_ordenados
        
        if especialidad and consultorio_sugerido:
            self.consultorio_var.set(consultorio_sugerido)
        else:
            self.consultorio_var.set('')

    def dibujar_botones(self, main_frame):
        btn_frame = tk.Frame(main_frame, bg='#f0f8ff')
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        estilo_boton = {
            'font': ('Arial', 12), 
            'bd': 2, 
            'relief': tk.RAISED, 
            'padx': 10, 
            'pady': 5, 
            'width': 20
        }

        tk.Button(btn_frame, text="Registrar Paciente", command=self.registrar_paciente,
                bg='#4CAF50', fg='white', **estilo_boton).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Ver Reporte", command=self.mostrar_reporte,
                bg='#607D8B', fg='white', **estilo_boton).pack(side=tk.LEFT, padx=10)

    def sincronizar_datos_periodicamente(self):
        """Sincroniza los datos de manera periódica, actualizando la copia local de los datos."""
        while True:
            try:
                # Cargar los datos más recientes del archivo JSON
                nuevos_datos = cargar_datos(self.archivo_datos)

                # Comparar si los datos han cambiado
                if nuevos_datos != self.datos:  # Si los datos han cambiado
                    self.datos = nuevos_datos  # Actualizar la copia local en memoria

                    # Actualizar la UI o cualquier otra parte relevante del programa
                    self.actualizar_interfaz_usuario()

            except Exception as e:
                print(f"Error al sincronizar datos: {e}")

            # Esperar 3 segundos antes de hacer la próxima sincronización
            time.sleep(3)

    def actualizar_interfaz_usuario(self):
        """Actualizar la interfaz de usuario para reflejar los nuevos datos"""
        self.actualizar_listas()

    def actualizar_listas(self):
       """Actualiza las listas de pacientes en espera y atendidos"""
       # Asegurémonos de que las listas existan
       if not hasattr(self, 'wait_listbox'):
           self.wait_listbox = tk.Listbox(self.root, font=('Arial', 12), selectbackground='#e0e0e0', width=40, height=20)
           self.wait_listbox.pack(padx=5, pady=5, fill='both', expand=True)

       if not hasattr(self, 'hist_listbox'):
           self.hist_listbox = tk.Listbox(self.root, font=('Arial', 12), selectbackground='#e0e0e0', width=40, height=20)
           self.hist_listbox.pack(padx=5, pady=5, fill='both', expand=True)
    
       self.wait_listbox.delete(0, tk.END)
       self.hist_listbox.delete(0, tk.END)

        # Agrupar pacientes por consultorio
       pacientes_por_consultorio = {}
       hoy = datetime.now().strftime("%Y-%m-%d")
    
       for p in self.datos['pacientes']:
            if p['fecha_registro'].startswith(hoy):
               consultorio = p.get('consultorio', None) #Asignar valor del consultorio
               if consultorio is None:
                   continue #Si no tiene un consultorio asignado, lo omitimos
               if consultorio not in pacientes_por_consultorio:
                   pacientes_por_consultorio[consultorio] = {'espera': [], 'atendidos': []}
        
            if p.get('atendido'):
                pacientes_por_consultorio[consultorio]['atendidos'].append(p)
            else:
                pacientes_por_consultorio[consultorio]['espera'].append(p)

        # Mostrar en espera agrupados por consultorio
       for consultorio in sorted(pacientes_por_consultorio.keys()):
            pacientes = sorted(pacientes_por_consultorio[consultorio]['espera'], 
                         key=lambda x: x['fecha_registro'])
        
            self.wait_listbox.insert(tk.END, f"--- {consultorio} ---")
            for p in pacientes:
               h = p['fecha_registro'].split(' ')[1][:5]
               self.wait_listbox.insert(tk.END, f"  {p['id']}. {p['nombre']} ({h})")

        # Mostrar atendidos ordenados por tiempo de atención
       todos_atendidos = []
       for consultorio in pacientes_por_consultorio:
           todos_atendidos.extend(pacientes_por_consultorio[consultorio]['atendidos'])
    
       todos_atendidos.sort(key=lambda x: x.get('fecha_atencion', ''), reverse=True)
    
       for p in todos_atendidos[:20]:  # Mostrar solo los últimos 20
           h_reg = p['fecha_registro'].split(' ')[1][:5]
           h_aten = p.get('fecha_atencion', '').split(' ')[1][:5] if 'fecha_atencion' in p else ''
           self.hist_listbox.insert(tk.END, 
                               f"{p['id']}. {p['nombre']} ({p['consultorio']}) - Reg: {h_reg}, At: {h_aten}")


    def registrar_paciente(self):
        nombre = self.nombre_entry.get()
        valido, mensaje = validar_nombre_paciente(nombre)
        if not valido:
            messagebox.showerror("Error", mensaje, parent=self.root)
            return

        especialidad = self.especialidad_var.get()
        if not especialidad:
            messagebox.showerror("Error", "Debe seleccionar una especialidad", parent=self.root)
            return

        consultorio = self.consultorio_var.get()
        if not consultorio:
            messagebox.showerror("Error", "Debe seleccionar un consultorio", parent=self.root)
            return

        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            existe_paciente = any(
                p['nombre'].lower() == nombre.lower() and
                p['fecha_registro'].startswith(hoy) and
                not p['atendido']
                for p in self.datos['pacientes']
            )

            if existe_paciente:
                messagebox.showwarning("Advertencia", 
                                    "Este paciente ya tiene un turno pendiente para hoy", 
                                    parent=self.root)
                return

            nuevo_id = max([p['id'] for p in self.datos['pacientes']], default=0) + 1
            nuevo_paciente = {
                'id': nuevo_id,
                'nombre': nombre,
                'especialidad': especialidad,
                'consultorio': consultorio,
                'fecha_registro': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'atendido': False
            }

            # Actualizar los datos en memoria
            self.datos['pacientes'].append(nuevo_paciente)

            # Solo guardar los datos cuando sea necesario (al cerrar o después de una operación importante)
            if guardar_datos(self.archivo_datos, self.datos):
                self.info_label.config(text=f"Paciente registrado con éxito. Turno: {nuevo_paciente['id']}")
                self.nombre_entry.delete(0, tk.END)
                self.mostrar_dialogo_ticket(nuevo_paciente)

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}", parent=self.root)

    def mostrar_dialogo_ticket(self, paciente):
        """Muestra un diálogo con la información del paciente y un botón para imprimir el ticket."""
        dialogo = tk.Toplevel(self.root)
        dialogo.title("Ticket de Registro")
        dialogo.geometry("500x400")
        dialogo.resizable(False, False)
        dialogo.transient(self.root)
        dialogo.grab_set()

        # Frame principal
        frame = tk.Frame(dialogo, padx=20, pady=20)
        frame.pack(expand=True, fill=tk.BOTH)

        # Logo en ticket
        try:
            logo_label = cargar_logo(frame, tamaño=(90, 90))
            logo_label.pack(pady=10)
        except:
            tk.Label(frame, text="HOSPITAL DE APOYO PALPA", font=('Arial', 14, 'italic')).pack()

        # Información del ticket
        info_frame = tk.Frame(frame)
        info_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(info_frame, text=f"Turno: {paciente['id']}", font=('Arial', 12, 'bold')).pack(anchor='w')
        tk.Label(info_frame, text=f"Paciente: {paciente['nombre']}", font=('Arial', 12)).pack(anchor='w', pady=5)
        tk.Label(info_frame, text=f"Especialidad: {paciente['especialidad']}", font=('Arial', 12)).pack(anchor='w')
        tk.Label(info_frame, text=f"Consultorio: {paciente['consultorio']}", font=('Arial', 12)).pack(anchor='w', pady=5)
        tk.Label(info_frame, text=f"Fecha: {paciente['fecha_registro']}", font=('Arial', 10)).pack(anchor='w')

        # Botones
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Imprimir Ticket", command=lambda: self.imprimir_ticket(paciente, dialogo),
                 bg='#2196F3', fg='white', font=('Arial', 12)).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cerrar", command=dialogo.destroy,
                 bg='#f44336', fg='white', font=('Arial', 12)).pack(side=tk.RIGHT, padx=10)

    def imprimir_ticket(self, paciente, ventana):
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
                title="Guardar ticket como",
                parent=ventana
            )

            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("=== HOSPITAL DE APOYO PALPA ===\n")
                    f.write("       TICKET DE REGISTRO\n\n")
                    f.write(f"Turno: {paciente['id']}\n")
                    f.write(f"Paciente: {paciente['nombre']}\n")
                    f.write(f"Especialidad: {paciente['especialidad']}\n")
                    f.write(f"Consultorio: {paciente['consultorio']}\n")
                    f.write(f"Fecha: {paciente['fecha_registro']}\n\n")
                    f.write("Presente este ticket en recepción\n")
                    f.write("=== Gracias por su visita ===\n")

                messagebox.showinfo("Éxito", f"Ticket guardado en:\n{filepath}", parent=ventana)
                ventana.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el ticket: {str(e)}", parent=ventana)

    def mostrar_reporte(self):
        # Ventana emergente para el reporte
        reporte = tk.Toplevel(self.root)
        reporte.title("Reporte de Pacientes")
        reporte.geometry("800x600")
        reporte.configure(bg='#f0f8ff')

        # Botón para exportar CSV
        btn_export = tk.Button(
            reporte,
            text="Exportar CSV",
            command=lambda: self.exportar_csv(self.datos.get('pacientes', [])),
            font=('Arial', 12),
            bg='#4CAF50',
            fg='white',
            padx=10,
            pady=5
        )
        btn_export.pack(pady=(10, 0))

        # Treeview con encabezados
        columnas = ("ID", "Nombre", "Especialidad", "Consultorio", "Fecha Registro", "Atendido", "Fecha Atención")
        tree = ttk.Treeview(reporte, columns=columnas, show="headings")
        for col in columnas:
            tree.heading(col, text=col)
            tree.column(col, anchor='w', width=120)
        tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Scrollbar vertical
        vsb = ttk.Scrollbar(reporte, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')

        # Carga de datos
        for p in self.datos.get('pacientes', []):
            tree.insert(
                "",
                tk.END,
                values=(
                    p.get("id", ""),
                    p.get("nombre", ""),
                    p.get("especialidad", ""),
                    p.get("consultorio", ""),
                    p.get("fecha_registro", ""),
                    "Sí" if p.get("atendido") else "No",
                    p.get("fecha_atencion", "")
                )
            )

        # Botón para editar paciente
        def editar_paciente():
            # Obtén el ID seleccionado
            seleccionado = tree.selection()
            if not seleccionado:
                messagebox.showwarning("Seleccionar Paciente", "Debe seleccionar un paciente para editar.")
                return

            item = tree.item(seleccionado)
            paciente_id = item['values'][0]  # Obtén el ID del paciente seleccionado
            paciente = next((p for p in self.datos['pacientes'] if p['id'] == paciente_id), None)

            if paciente:
                # Crear una ventana de edición
                self.editar_paciente_ventana(paciente)

        editar_button = tk.Button(
            reporte,
            text="Editar Paciente",
            command=editar_paciente,
            font=('Arial', 12),
            bg='#FF9800',
            fg='white',
            padx=10,
            pady=5
        )
        editar_button.pack(pady=(10, 0))

        # Botón para cerrar la ventana
        tk.Button(
            reporte,
            text="Cerrar",
            command=reporte.destroy,
            font=('Arial', 12),
            bg='#f44336',
            fg='white',
            padx=10,
            pady=5
        ).pack(pady=(0,10))

    def editar_paciente_ventana(self, paciente):
        """Crea una ventana para editar los datos de un paciente específico."""
        ventana_editar = tk.Toplevel(self.root)
        ventana_editar.title(f"Editar Paciente {paciente['id']}")
        ventana_editar.geometry("400x300")
        ventana_editar.configure(bg='#f0f8ff')

        # Campo de nombre
        tk.Label(ventana_editar, text="Nombre del Paciente:", bg='#f0f8ff').pack(pady=5)
        nombre_entry = tk.Entry(ventana_editar)
        nombre_entry.insert(0, paciente['nombre'])
        nombre_entry.pack(pady=5)

        # ComboBox de especialidad
        tk.Label(ventana_editar, text="Especialidad:", bg='#f0f8ff').pack(pady=5)
        especialidad_entry = ttk.Combobox(ventana_editar, state="readonly", width=40)
        especialidades = [esp['nombre'] for esp in self.datos['especialidades']]
        especialidad_entry['values'] = especialidades
        especialidad_entry.set(paciente['especialidad'])  # Establecer la especialidad actual del paciente
        especialidad_entry.pack(pady=5)

        # ComboBox de consultorio
        tk.Label(ventana_editar, text="Consultorio:", bg='#f0f8ff').pack(pady=5)
        consultorio_entry = ttk.Combobox(ventana_editar, state="readonly", width=40)
        consultorios = [f"Consultorio {i}" for i in range(1, 15)]  # Consultorios de 1 a 14
        consultorio_entry['values'] = consultorios
        consultorio_entry.set(paciente['consultorio'])  # Establecer el consultorio actual del paciente
        consultorio_entry.pack(pady=5)

        # Botón para guardar cambios
        def guardar_cambios():
            paciente['nombre'] = nombre_entry.get()
            paciente['especialidad'] = especialidad_entry.get()
            paciente['consultorio'] = consultorio_entry.get()

            # Guardar los cambios en el archivo
            if guardar_datos(self.archivo_datos, self.datos):
                messagebox.showinfo("Éxito", "Paciente editado con éxito.", parent=ventana_editar)
                ventana_editar.destroy()
                self.actualizar_listas()

        tk.Button(ventana_editar, text="Guardar Cambios", command=guardar_cambios, bg='#4CAF50', fg='white').pack(pady=20)

        # Botón para cerrar la ventana de edición
        tk.Button(ventana_editar, text="Cerrar", command=ventana_editar.destroy, bg='#f44336', fg='white').pack(pady=5)

    def exportar_csv(self, pacientes):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV","*.csv")],
            title="Guardar Reporte como CSV"
        )
        if not filepath:
           return

        try:
           with open(filepath, 'w', newline='', encoding='utf-8') as f:
               writer = csv.writer(f)
               # Cabecera
               writer.writerow([
                  "ID", "Nombre", "Especialidad",
                  "Consultorio", "Fecha Registro",
                  "Atendido", "Fecha Atención"
               ])
               # Filas
               for p in pacientes:
                   writer.writerow([
                       p.get("id", ""),
                       p.get("nombre", ""),
                       p.get("especialidad", ""),
                       p.get("consultorio", ""),
                       p.get("fecha_registro", ""),
                       "Sí" if p.get("atendido") else "No",
                       p.get("fecha_atencion", "")
                   ])
           messagebox.showinfo("Éxito", f"Reporte exportado a:\n{filepath}", parent=self.root)
        except Exception as e:
           messagebox.showerror("Error", f"No se pudo exportar CSV:\n{e}", parent=self.root)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ModuloAdmision()
    app.run()

