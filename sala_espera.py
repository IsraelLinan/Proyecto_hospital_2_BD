import tkinter as tk
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
LOGO_WIDTH = 200
LOGO_HEIGHT = 200

class SalaEspera:
    def __init__(self):
            self.audio_enabled = True
            self.current_audio_thread = None
            self.ultimo_llamado = None
            self._initialize_audio_system()
            
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

    def _initialize_audio_system(self):
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=2048)
            
        except Exception:
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

        izq = tk.Frame(self.root, bg='black')
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
                tk.Label(izq, image=self.logo, bg='black').grid(row=0, column=0, pady=(10,20))
            else:
                raise FileNotFoundError("Logo no encontrado")
        except Exception as e:
            print(f"Error al cargar logo: {e}")
            tk.Label(izq, text="HOSPITAL DE APOYO PALPA", 
                    font=('Arial', FONT_TITLE_SIZE, 'bold'), 
                    fg='white', bg='black').grid(row=0, column=0, pady=(10,20))

        self.lbl_reloj = tk.Label(izq, font=('Arial', FONT_TITLE_SIZE), fg='white', bg='black')
        self.lbl_reloj.grid(row=1, column=0, pady=(0,5))
        self._update_clock()

        self.lbl_last = tk.Label(izq, font=('Arial', FONT_LIST_SIZE + 5), 
                               fg='white', bg='black', width=50, anchor='w')
        self.lbl_last.grid(row=2, column=0, pady=(5,20))
        self.lbl_last.config(text="Último atendido: Ninguno")

        der = tk.Frame(self.root, bg='#f0f0f0')
        der.grid(row=0, column=1, sticky='nsew', padx=(0,5), pady=10)
        der.grid_rowconfigure(0, weight=1)
        der.grid_rowconfigure(1, weight=1)
        der.grid_columnconfigure(0, weight=1, minsize=400)

        espera = tk.Frame(der, bg='#e6f3ff', bd=2, relief=tk.RAISED)
        espera.grid(row=0, column=0, sticky='nsew', pady=(0,3), padx=5)
        espera.grid_columnconfigure(0, weight=1)
        espera.grid_rowconfigure(1, weight=1)
        tk.Label(espera, text="EN ESPERA", font=self.fuente_tit, bg='#004a99', fg='white'
                ).grid(row=0, column=0, sticky='ew', pady=1)
        self.txt_espera = tk.Listbox(espera, font=self.fuente_lst, bg='#e6f3ff', width=40, height=20)
        self.txt_espera.grid(row=1, column=0, sticky='nsew')

        atencion = tk.Frame(der, bg='#ffe6e6', bd=2, relief=tk.RAISED)
        atencion.grid(row=1, column=0, sticky='nsew', pady=(3,0), padx=5)
        atencion.grid_columnconfigure(0, weight=1)
        atencion.grid_rowconfigure(1, weight=1)
        tk.Label(atencion, text="EN ATENCIÓN", font=self.fuente_tit, bg='#990000', fg='white'
                ).grid(row=0, column=0, sticky='ew', pady=1)
        self.txt_atencion = tk.Listbox(atencion, font=self.fuente_lst, bg='#ffe6e6', width=40, height=20)
        self.txt_atencion.grid(row=1, column=0, sticky='nsew')

    def _update_clock(self):
        self.lbl_reloj.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)
        
    def _cargar_listas(self):
        self.txt_espera.delete(0, tk.END)
        self.txt_atencion.delete(0, tk.END)

        for p in self.datos.get('pacientes', []):
            consultorio = p.get('consultorio') or 'Consultorio desconocido'
            especialidad = p.get('especialidad', '')
            nombre_p = p.get('nombre', 'Nombre desconocido')
            id_p = p.get('paciente_id', '?')

            fecha_registro = p.get('fecha_registro')
            fecha_atencion = p.get('fecha_atencion')
            h_reg = fecha_registro.strftime("%H:%M") if fecha_registro else ""
            h_aten = fecha_atencion.strftime("%H:%M") if fecha_atencion else ""

            if not p.get('atendido', False):
               self.txt_espera.insert(tk.END, f"  {id_p}. {nombre_p} ({especialidad} - {consultorio})")
            else:
               self.txt_atencion.insert(tk.END, f"{id_p}. {nombre_p} ({especialidad} - {consultorio}) - Reg: {h_reg}, At: {h_aten}")


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
        tk.Tk().withdraw()
        tk.messagebox.showerror("Error", f"No se pudo iniciar la aplicación: {str(e)}")





