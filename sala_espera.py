import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
import threading
import time
import os
import sys
import pyttsx3
from hospital_lib import cargar_datos

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FONT_TITLE_SIZE = 28
FONT_LIST_SIZE = 26
LOGO_WIDTH = 500
LOGO_HEIGHT = 500

class SalaEspera:
    def __init__(self):
        self.audio_enabled = True
        self.current_audio_thread = None
        self.ultimo_llamado = None

        try:
            self.engine = pyttsx3.init()

            # Cambiar la velocidad de lectura
            rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', rate - 70)  # Reduce la velocidad en 70 palabras por minuto

            # Obtener las voces disponibles
            voices = self.engine.getProperty('voices')

            # Buscar y seleccionar la voz "Microsoft Sabina Desktop - México"
            for voice in voices:
                if "Sabina" in voice.name and "Mexico" in voice.name:  # Verifica si la voz es Sabina - México
                    self.voice_spanish = voice.id
                    self.engine.setProperty('voice', self.voice_spanish)
                    print(f"Voz seleccionada: {voice.name}")
                    break
            else:
                print("No se encontró la voz 'Microsoft Sabina Desktop - México', usando la voz predeterminada.")
                self.voice_spanish = voices[0].id  # Si no se encuentra, usa la primera voz disponible
                self.engine.setProperty('voice', self.voice_spanish)

        except Exception as e:
            print(f"Error al inicializar pyttsx3: {e}")
            self.audio_enabled = False

        self.datos = cargar_datos()
        self.logo = None

        self.root = tk.Tk()
        self.root.title("Sala de Espera – Hospital de Apoyo Palpa")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(800, 600)
        self.root.configure(bg='#f0f0f0')
        self.root.state('zoomed')

        self.fuente_tit = tkfont.Font(family='Arial', size=FONT_TITLE_SIZE, weight='bold')
        self.fuente_lst = tkfont.Font(family='Arial', size=FONT_LIST_SIZE)

        self._setup_ui()
        self._cargar_listas()
        self._verificar_cambios()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _execute_audio_playback(self, texto):
        try:
            print(f"Reproduciendo mensaje en español: {texto}")
            self.engine.setProperty('voice', self.voice_spanish)  # Asegúrate de que siempre use la voz en español
            self.engine.say(texto)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error en síntesis de voz: {e}")

    def _setup_ui(self):
        total_width = self.root.winfo_screenwidth()
        left_width = int(total_width * 0.6)
        right_width = int(total_width * 0.4)

        self.root.grid_columnconfigure(0, weight=6, minsize=left_width)
        self.root.grid_columnconfigure(1, weight=4, minsize=right_width)
        self.root.grid_rowconfigure(0, weight=1)

        izq = tk.Frame(self.root, bg='#DCEEFF', width=left_width)
        izq.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        izq.grid_propagate(False)
        izq.grid_rowconfigure(0, weight=1)
        izq.grid_columnconfigure(0, weight=1)

        der = tk.Frame(self.root, bg="#f0f0f0", width=right_width)
        der.grid(row=0, column=1, sticky='nsew', padx=(0,5), pady=10)
        der.grid_rowconfigure(0, weight=1)
        der.grid_rowconfigure(1, weight=1)
        der.grid_columnconfigure(0, weight=1)

        espera = tk.Frame(der, bg='#e6f3ff', bd=2, relief=tk.RAISED)
        espera.grid(row=0, column=0, sticky='nsew', pady=(0,3), padx=5)
        espera.grid_columnconfigure(0, weight=1)
        espera.grid_rowconfigure(1, weight=1)

        tk.Label(espera, text="EN ESPERA", font=self.fuente_tit, bg='#004a99', fg='white').grid(row=0, column=0, sticky='ew', pady=1)

        espera_frame = tk.Frame(espera)
        espera_frame.grid(row=1, column=0, sticky='nsew')
        espera_frame.grid_columnconfigure(0, weight=1)
        espera_frame.grid_rowconfigure(0, weight=1)

        scroll_y = tk.Scrollbar(espera_frame)
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x = tk.Scrollbar(espera_frame, orient='horizontal')
        scroll_x.grid(row=1, column=0, sticky='ew')

        self.txt_espera = tk.Listbox(espera_frame, font=self.fuente_lst, bg='#e6f3ff', xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        self.txt_espera.grid(row=0, column=0, sticky='nsew')

        scroll_x.config(command=self.txt_espera.xview)
        scroll_y.config(command=self.txt_espera.yview)

        atencion = tk.Frame(der, bg='#ffe6e6', bd=2, relief=tk.RAISED)
        atencion.grid(row=1, column=0, sticky='nsew', pady=(3,0), padx=5)
        atencion.grid_columnconfigure(0, weight=1)
        atencion.grid_rowconfigure(1, weight=1)

        tk.Label(atencion, text="EN ATENCIÓN", font=self.fuente_tit, bg='#990000', fg='white').grid(row=0, column=0, sticky='ew', pady=1)

        atencion_frame = tk.Frame(atencion)
        atencion_frame.grid(row=1, column=0, sticky='nsew')
        atencion_frame.grid_columnconfigure(0, weight=1)
        atencion_frame.grid_rowconfigure(0, weight=1)

        scroll_y2 = tk.Scrollbar(atencion_frame)
        scroll_y2.grid(row=0, column=1, sticky='ns')
        scroll_x2 = tk.Scrollbar(atencion_frame, orient='horizontal')
        scroll_x2.grid(row=1, column=0, sticky='ew')

        self.txt_atencion = tk.Listbox(atencion_frame, font=self.fuente_lst, bg='#ffe6e6', xscrollcommand=scroll_x2.set, yscrollcommand=scroll_y2.set)
        self.txt_atencion.grid(row=0, column=0, sticky='nsew')

        scroll_x2.config(command=self.txt_atencion.xview)
        scroll_y2.config(command=self.txt_atencion.yview)

        self.lbl_last = tk.Label(izq, font=('Arial', 28, 'bold'), fg='#000000', bg='#FFCC66', wraplength=int(left_width * 0.9), justify='center', anchor='center')
        self.lbl_last.grid(row=4, column=0, pady=(5,20), padx=10, sticky='ew')
        self.lbl_last.config(text="Último atendido: Ninguno")

        try:
            posibles_rutas = [
                os.path.join(os.path.dirname(__file__)),
                os.path.dirname(sys.executable),
                os.getcwd()
            ]
            logo_path = None
            for ruta in posibles_rutas:
                temp_path = os.path.join(ruta, 'logo_hospital.png')
                if os.path.exists(temp_path):
                    logo_path = temp_path
                    break

            if logo_path:
                from PIL import Image, ImageTk
                image = Image.open(logo_path)
                logo_size = int(left_width * 0.4)
                image = image.resize((logo_size, logo_size), Image.LANCZOS)
                self.logo = ImageTk.PhotoImage(image)
                tk.Label(izq, image=self.logo, bg='#DCEEFF').grid(row=2, column=0, pady=(10,20))
            else:
                raise FileNotFoundError("Logo no encontrado")
        except Exception as e:
            print(f"Error al cargar logo: {e}")
            tk.Label(izq, text="HOSPITAL DE APOYO PALPA", font=('Arial', FONT_TITLE_SIZE, 'bold'), fg='black', bg='#DCEEFF').grid(row=2, column=0, pady=(10,20))

        self.lbl_reloj = tk.Label(izq, font=('Arial', FONT_TITLE_SIZE), fg='black', bg='#DCEEFF')
        self.lbl_reloj.grid(row=3, column=0, pady=(0,5))
        self._update_clock()

    def _update_clock(self):
        self.lbl_reloj.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)

    def _cargar_listas(self):
        self.txt_espera.delete(0, tk.END)
        self.txt_atencion.delete(0, tk.END)
        pacientes = self.datos.get('pacientes', [])

        pacientes_pendientes = {}
        pacientes_atendidos = {}

        for p in pacientes:
            paciente_id = p.get('paciente_id')
            nombre = p.get('nombre', 'Nombre desconocido')
            especialidad = p.get('especialidad', '')
            consultorio = p.get('consultorio', '')
            atendido = p.get('atendido', False)
            fecha_registro = p.get('fecha_registro')
            fecha_atencion = p.get('fecha_atencion')

            if not atendido:
                if paciente_id not in pacientes_pendientes:
                    pacientes_pendientes[paciente_id] = {
                        'nombre': nombre,
                        'consultorios': []
                    }
                pacientes_pendientes[paciente_id]['consultorios'].append(f"{especialidad} - {consultorio}")
            else:
                if paciente_id not in pacientes_atendidos:
                    pacientes_atendidos[paciente_id] = {
                        'nombre': nombre,
                        'consultorios': [],
                        'fecha_registro': fecha_registro,
                        'fecha_atencion': fecha_atencion
                    }
                pacientes_atendidos[paciente_id]['consultorios'].append(f"{especialidad} - {consultorio}")

        for pid, info in pacientes_pendientes.items():
            lista_consultorios = ", ".join(info['consultorios'])
            self.txt_espera.insert(tk.END, f"{pid}. {info['nombre']} ({lista_consultorios})")

        atendidos_ordenados = sorted(
            pacientes_atendidos.items(),
            key=lambda item: item[1]['fecha_atencion'] if item[1]['fecha_atencion'] else datetime.min,
            reverse=True
        )

        for pid, info in atendidos_ordenados:
            h_reg = info['fecha_registro'].strftime("%H:%M") if info['fecha_registro'] else ""
            h_aten = info['fecha_atencion'].strftime("%H:%M") if info['fecha_atencion'] else ""
            lista_consultorios = ", ".join(info['consultorios'])
            self.txt_atencion.insert(tk.END, f"{pid}. {info['nombre']} ({lista_consultorios}) - Reg: {h_reg}, At: {h_aten}")

    def _verificar_cambios(self):
        try:
            nuevos_datos = cargar_datos()
            nuevo_llamado = nuevos_datos.get('ultimo_llamado')

            if nuevo_llamado != self.ultimo_llamado:
                if nuevo_llamado and nuevo_llamado.startswith("RELLAMADO_"):
                    mensaje = nuevo_llamado.split('_', 1)[1]
                    self._play_audio(mensaje)
                    self.lbl_last.config(text=f"Re-llamando: {mensaje}")
                elif nuevo_llamado:
                    self._play_audio(nuevo_llamado)
                    self.lbl_last.config(text=f"{nuevo_llamado}")

                self.ultimo_llamado = nuevo_llamado

            self.datos = nuevos_datos
            self._cargar_listas()
        except Exception as e:
            print(f"Error al verificar cambios: {e}")
        finally:
            self.root.after(3000, self._verificar_cambios)

    def _play_audio(self, texto):
        print(f"_play_audio llamado con texto: {texto}")
        if not self.audio_enabled:
            print("Audio deshabilitado, no se reproducirá el mensaje")
            return

        self._stop_audio()

        self.current_audio_thread = threading.Thread(
            target=self._execute_audio_playback,
            args=(texto,),
            daemon=True
        )
        self.current_audio_thread.start()

    def _stop_audio(self):
        # pyttsx3 no necesita detener audio explícitamente
        pass

    def _on_close(self):
        try:
            if self.audio_enabled:
                self.engine.stop()
        except:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = SalaEspera()
        app.run()
    except Exception as e:
        print(f"Error fatal: {e}")
        tk.Tk().withdraw()
        tk.messagebox.showerror("Error", f"No se pudo iniciar la aplicación: {str(e)}")











