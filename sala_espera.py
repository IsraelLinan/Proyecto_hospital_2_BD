import ttkbootstrap as tb
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import font as tkfont
import pygame
from datetime import datetime
from gtts import gTTS
import winsound
from PIL import Image, ImageTk
import tempfile
import threading
import os
import time
import sys
from hospital_lib import cargar_datos

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FONT_TITLE_SIZE = 28
FONT_LIST_SIZE = 26
LOGO_WIDTH = 800  #tamaño del logo
LOGO_HEIGHT = 800 #tamaño del logo

class SalaEspera:
    def __init__(self):
        try:
            self.audio_enabled = True
            self.current_audio_thread = None
            self.ultimo_llamado = None
            self._initialize_audio_system()
            
            self.datos = cargar_datos()
            self.logo = None

            self.root = tb.Window(themename="flatly")
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

        except Exception as e:
            print(f"Error al iniciar Sala de Espera: {e}")
            raise

    def _initialize_audio_system(self):
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=2048)
            if not pygame.mixer.get_init():
               raise Exception("Mixer no se inicializó correctamente")
            print("Sistema de audio pygame inicializado correctamente")
        except Exception as e:
            print(f"Error al inicializar pygame mixer: {e}")
            try:
               winsound.Beep(1000, 100)
               print("Usando winsound como respaldo de audio")
            except Exception as e2:
              print(f"Error usando winsound: {e2}")
              print("Sistema de audio completamente deshabilitado")
              self.audio_enabled = False

    def _execute_audio_playback(self, texto):
        try:
            print(f"Intentando reproducir: {texto}")
            if pygame.mixer.get_init():
                try:
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                        temp_path = tmp.name
                    tts = gTTS(text=texto, lang='es', slow=False)
                    tts.save(temp_path)
                    sound = pygame.mixer.Sound(temp_path)
                    sound.set_volume(1.0)
                    sound.play()
                    print("Audio iniciado, esperando a que termine...")
                    while pygame.mixer.get_busy():
                        time.sleep(0.1)
                finally:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception as e:
                        print(f"Error al limpiar archivo temporal: {e}")
            else:
                winsound.Beep(1000, 500)
                time.sleep(0.3)
                winsound.Beep(1500, 500)
        except Exception as e:
            print(f"Error en reproducción de audio: {e}")
            print(f"MENSAJE DE VOZ (no se pudo reproducir): {texto}")

    def _setup_ui(self):
        self.root.grid_columnconfigure(0, weight=3, minsize=300)
        self.root.grid_columnconfigure(1, weight=7, minsize=500)
        self.root.grid_rowconfigure(0, weight=1)

        izq = tb.Frame(self.root, bootstyle="dark", padding=10)
        izq.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        izq.grid_rowconfigure(0, weight=1)
        izq.grid_columnconfigure(0, weight=1)

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
                image = Image.open(logo_path)
                image = image.resize((LOGO_WIDTH, LOGO_HEIGHT), Image.LANCZOS)
                self.logo = ImageTk.PhotoImage(image)
                tb.Label(izq, image=self.logo, bootstyle="dark").grid(row=0, column=0, pady=(10,20))
            else:
                raise FileNotFoundError("Logo no encontrado")
        except Exception as e:
            print(f"Error al cargar logo: {e}")
            tb.Label(izq, text="HOSPITAL DE APOYO PALPA", 
                    font=('Arial', FONT_TITLE_SIZE, 'bold'), 
                    foreground='white', background='#1a1a1a', bootstyle="dark").grid(row=0, column=0, pady=(10,20))

        self.lbl_reloj = tb.Label(izq, font=('Arial', FONT_TITLE_SIZE), foreground='white', background='#1a1a1a', bootstyle="dark")
        self.lbl_reloj.grid(row=1, column=0, pady=(0,5))
        self._update_clock()

        self.lbl_last = tb.Label(izq, font=('Arial', FONT_LIST_SIZE + 5), 
                               foreground='white', background='#1a1a1a', bootstyle="dark", width=50, anchor='w')
        self.lbl_last.grid(row=2, column=0, pady=(5,20))
        self.lbl_last.config(text="Último atendido: Ninguno")

        der = tb.Frame(self.root, bootstyle="secondary", padding=10)
        der.grid(row=0, column=1, sticky='nsew', padx=(0,5), pady=10)
        der.grid_rowconfigure(0, weight=1)
        der.grid_rowconfigure(1, weight=1)
        der.grid_columnconfigure(0, weight=1, minsize=400)

        espera = tb.Frame(der, bootstyle="info", padding=5, relief="raised")
        espera.grid(row=0, column=0, sticky='nsew', pady=(0,3), padx=5)
        espera.grid_columnconfigure(0, weight=1)
        espera.grid_rowconfigure(1, weight=1)
        tb.Label(espera, text="EN ESPERA", font=self.fuente_tit, bootstyle="info-inverse"
                ).grid(row=0, column=0, sticky='ew', pady=1)
        self.txt_espera = tk.Listbox(espera, font=self.fuente_lst, width=40, height=20)
        self.txt_espera.grid(row=1, column=0, sticky='nsew')

        atencion = tb.Frame(der, bootstyle="danger", padding=5, relief="raised")
        atencion.grid(row=1, column=0, sticky='nsew', pady=(3,0), padx=5)
        atencion.grid_columnconfigure(0, weight=1)
        atencion.grid_rowconfigure(1, weight=1)
        tb.Label(atencion, text="EN ATENCIÓN", font=self.fuente_tit, bootstyle="danger-inverse"
                ).grid(row=0, column=0, sticky='ew', pady=1)
        self.txt_atencion = tk.Listbox(atencion, font=self.fuente_lst, width=40, height=20)
        self.txt_atencion.grid(row=1, column=0, sticky='nsew')

    def _update_clock(self):
        self.lbl_reloj.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)

    def _cargar_listas(self):
        self.txt_espera.delete(0, tk.END)
        self.txt_atencion.delete(0, tk.END)

        try:
            current_consultorio = None
            for p in self.datos.get('pacientes', []):
                if not p.get('atendido', False):
                    consultorios = p.get('consultorios', None)
                    if consultorios:
                        lista_consultorios = [c.strip() for c in consultorios.split(',')]
                        if len(lista_consultorios) > 2:
                            consultorio_p = ", ".join(lista_consultorios[:2]) + ", ..."
                        else:
                            consultorio_p = consultorios
                    else:
                        consultorio_p = 'Consultorio desconocido'

                    if consultorio_p != current_consultorio:
                        self.txt_espera.insert(tk.END, f"--- {consultorio_p} ---")
                        current_consultorio = consultorio_p

                    fecha_registro = p.get('fecha_registro')
                    try:
                        if isinstance(fecha_registro, datetime):
                            h = fecha_registro.strftime("%H:%M")
                        elif isinstance(fecha_registro, str) and ' ' in fecha_registro:
                            h = fecha_registro.split(' ')[1][:5]
                        else:
                            h = "Hora desconocida"
                    except Exception as e:
                        print(f"Error al procesar fecha_registro paciente {p.get('id', '?')}: {e}")
                        h = "Hora error"

                    nombre_p = p.get('nombre', 'Nombre desconocido')
                    id_p = p.get('id', '?')

                    self.txt_espera.insert(tk.END, f"  {id_p}. {nombre_p} ({h})")

            atendidos = [p for p in self.datos.get('pacientes', []) if p.get('atendido', False)]
            atendidos.sort(key=lambda x: x.get('fecha_atencion') or '', reverse=True)

            for p in atendidos[:20]:
                consultorios = p.get('consultorios', None)
                if consultorios:
                    lista_consultorios = [c.strip() for c in consultorios.split(',')]
                    if len(lista_consultorios) > 2:
                        consultorio_p = ", ".join(lista_consultorios[:2]) + ", ..."
                    else:
                        consultorio_p = consultorios
                else:
                    consultorio_p = 'Consultorio desconocido'

                fecha_registro = p.get('fecha_registro')
                fecha_atencion = p.get('fecha_atencion')

                try:
                    if isinstance(fecha_registro, datetime):
                        h_reg = fecha_registro.strftime("%H:%M")
                    elif isinstance(fecha_registro, str) and ' ' in fecha_registro:
                        h_reg = fecha_registro.split(' ')[1][:5]
                    else:
                        h_reg = "Hora desconocida"
                except Exception as e:
                    print(f"Error en fecha_registro paciente {p.get('id', '?')}: {e}")
                    h_reg = "Hora error"

                try:
                    if isinstance(fecha_atencion, datetime):
                        h_aten = fecha_atencion.strftime("%H:%M")
                    elif isinstance(fecha_atencion, str) and ' ' in fecha_atencion:
                        h_aten = fecha_atencion.split(' ')[1][:5]
                    else:
                        h_aten = ""
                except Exception as e:
                    print(f"Error en fecha_atencion paciente {p.get('id', '?')}: {e}")
                    h_aten = ""

                id_p = p.get('id', '?')
                nombre_p = p.get('nombre', 'Nombre desconocido')

                self.txt_atencion.insert(tk.END, f"{id_p}. {nombre_p} ({consultorio_p}) - Reg: {h_reg}, At: {h_aten}")

            if atendidos:
                ultimo = atendidos[0]
                consultorios = ultimo.get('consultorios', None)
                if consultorios:
                    lista_consultorios = [c.strip() for c in consultorios.split(',')]
                    if len(lista_consultorios) > 2:
                        consultorio_p = ", ".join(lista_consultorios[:2]) + ", ..."
                    else:
                        consultorio_p = consultorios
                else:
                    consultorio_p = 'Consultorio desconocido'

                self.lbl_last.config(text=f"En atención: {ultimo.get('id', '?')}. {ultimo.get('nombre', 'Desconocido')} ({consultorio_p})")
            else:
                self.lbl_last.config(text="En atención: Ninguno")

        except Exception as e:
            print(f"Error al cargar listas: {e}")
            self.txt_espera.insert(tk.END, "Error al cargar datos")
            self.txt_atencion.insert(tk.END, "Error al cargar datos")

    def _verificar_cambios(self):
        try:
            nuevos_datos = cargar_datos()
            nuevo_llamado = nuevos_datos.get('ultimo_llamado')

            if nuevo_llamado:
                if nuevo_llamado.startswith("RELLAMADO_"):
                    mensaje = nuevo_llamado.split('_', 1)[1]
                    if self.ultimo_llamado != nuevo_llamado:
                        self._play_audio(mensaje)
                    self.lbl_last.config(text=f"Re-llamando: {mensaje}")
                elif self.ultimo_llamado != nuevo_llamado:
                    self._play_audio(nuevo_llamado)
                    self.lbl_last.config(text=f"Llamando: {nuevo_llamado}")

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
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                for i in range(pygame.mixer.get_num_channels()):
                    pygame.mixer.Channel(i).stop()
        except Exception as e:
            print(f"Error al detener audio: {e}")

    def _on_close(self):
        try:
            self._stop_audio()
            if pygame.mixer.get_init():
                pygame.mixer.quit()
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
        messagebox.showerror("Error", f"No se pudo iniciar la aplicación: {str(e)}")



