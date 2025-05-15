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
        try:
            # Configuración inicial del sistema de audio
            self.audio_enabled = True
            self.current_audio_thread = None
            self._initialize_audio_system()
            
            self.datos = cargar_datos()
            self.ultimo_llamado = None
            self.logo = None

            # Configuración de la ventana principal
            self.root = tk.Tk()
            self.root.title("Sala de Espera – Hospital de Apoyo Palpa")
            self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
            self.root.minsize(800, 600)
            self.root.configure(bg='#f0f0f0')
            self.root.state('zoomed')

            # Configuración de fuentes
            self.fuente_tit = tkfont.Font(family='Arial', size=FONT_TITLE_SIZE, weight='bold')
            self.fuente_lst = tkfont.Font(family='Arial', size=FONT_LIST_SIZE)

            # Inicializar interfaz
            self._setup_ui()
            self._cargar_listas()
            self._verificar_cambios()

            # Configurar manejo de cierre
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        except Exception as e:
            print(f"Error al iniciar Sala de Espera: {e}")
            raise

    def _initialize_audio_system(self):
        """Inicializa el sistema de audio con múltiples intentos"""
        try:
            # Intento 1: Pygame Mixer
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=2048)
            if not pygame.mixer.get_init():
                raise Exception("Mixer no se inicializó correctamente")
            print("Sistema de audio pygame inicializado correctamente")
        except Exception as e:
            print(f"Error al inicializar pygame mixer: {e}")
            try:
                # Intento 2: Winsound como respaldo
                winsound.Beep(1000, 100)
                print("Usando winsound como respaldo de audio")
            except:
                print("Sistema de audio completamente deshabilitado")
                self.audio_enabled = False

    def _setup_ui(self):
        """Configura la interfaz gráfica de usuario"""
        # Configuración del grid principal
        self.root.grid_columnconfigure(0, weight=3, minsize=300)
        self.root.grid_columnconfigure(1, weight=7, minsize=500)
        self.root.grid_rowconfigure(0, weight=1)

        # Panel izquierdo (logo y reloj)
        izq = tk.Frame(self.root, bg='black')
        izq.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        izq.grid_rowconfigure(0, weight=1)
        izq.grid_columnconfigure(0, weight=1)

        # Cargar logo
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

        # Reloj
        self.lbl_reloj = tk.Label(izq, font=('Arial', FONT_TITLE_SIZE), fg='white', bg='black')
        self.lbl_reloj.grid(row=1, column=0, pady=(0,5))
        self._update_clock()

        # Etiqueta de último atendido
        self.lbl_last = tk.Label(izq, font=('Arial', FONT_LIST_SIZE + 5), 
                               fg='white', bg='black', width=50, anchor='w')
        self.lbl_last.grid(row=2, column=0, pady=(5,20))
        self.lbl_last.config(text="Último atendido: Ninguno")

        # Panel derecho (listas de espera y atención)
        der = tk.Frame(self.root, bg='#f0f0f0')
        der.grid(row=0, column=1, sticky='nsew', padx=(0,5), pady=10)
        der.grid_rowconfigure(0, weight=1)
        der.grid_rowconfigure(1, weight=1)
        der.grid_columnconfigure(0, weight=1, minsize=400)

        # Frame de pacientes en espera
        espera = tk.Frame(der, bg='#e6f3ff', bd=2, relief=tk.RAISED)
        espera.grid(row=0, column=0, sticky='nsew', pady=(0,3), padx=5)
        espera.grid_columnconfigure(0, weight=1)
        espera.grid_rowconfigure(1, weight=1)
        tk.Label(espera, text="EN ESPERA", font=self.fuente_tit, bg='#004a99', fg='white'
                ).grid(row=0, column=0, sticky='ew', pady=1)
        self.txt_espera = tk.Listbox(espera, font=self.fuente_lst, bg='#e6f3ff', width=40, height=20)
        self.txt_espera.grid(row=1, column=0, sticky='nsew')

        # Frame de pacientes atendidos
        atencion = tk.Frame(der, bg='#ffe6e6', bd=2, relief=tk.RAISED)
        atencion.grid(row=1, column=0, sticky='nsew', pady=(3,0), padx=5)
        atencion.grid_columnconfigure(0, weight=1)
        atencion.grid_rowconfigure(1, weight=1)
        tk.Label(atencion, text="EN ATENCIÓN", font=self.fuente_tit, bg='#990000', fg='white'
                ).grid(row=0, column=0, sticky='ew', pady=1)
        self.txt_atencion = tk.Listbox(atencion, font=self.fuente_lst, bg='#ffe6e6', width=40, height=20)
        self.txt_atencion.grid(row=1, column=0, sticky='nsew')

    def _update_clock(self):
        """Actualiza el reloj cada segundo"""
        self.lbl_reloj.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)

    def _cargar_listas(self):
        """Carga las listas de pacientes en espera y atendidos"""
        self.txt_espera.delete(0, tk.END)
        self.txt_atencion.delete(0, tk.END)

        try:
            # Procesar pacientes en espera
            current_consultorio = None
            for p in self.datos['pacientes']:
                if not p['atendido']:
                    if p['consultorio'] != current_consultorio:
                        self.txt_espera.insert(tk.END, f"--- {p['consultorio']} ---")
                        current_consultorio = p['consultorio']

                    h = p['fecha_registro'].strftime("%H:%M") if isinstance(p['fecha_registro'], datetime) else p['fecha_registro'].split(' ')[1][:5]
                    self.txt_espera.insert(tk.END, f"  {p['id']}. {p['nombre']} ({h})")

            # Procesar pacientes atendidos
            atendidos = [p for p in self.datos['pacientes'] if p['atendido']]
            atendidos.sort(key=lambda x: x.get('fecha_atencion', ''), reverse=True)

            for p in atendidos[:20]:  # Mostrar solo los últimos 20
                h_reg = p['fecha_registro'].strftime("%H:%M") if isinstance(p['fecha_registro'], datetime) else p['fecha_registro'].split(' ')[1][:5]
                h_aten = p['fecha_atencion'].strftime("%H:%M") if isinstance(p.get('fecha_atencion'), datetime) else p.get('fecha_atencion', '').split(' ')[1][:5] if p.get('fecha_atencion') else ''
                self.txt_atencion.insert(tk.END, f"{p['id']}. {p['nombre']} ({p['consultorio']}) - Reg: {h_reg}, At: {h_aten}")

            # Actualizar último atendido
            if atendidos:
                ultimo = atendidos[0]
                self.lbl_last.config(text=f"En atención: {ultimo['id']}. {ultimo['nombre']} ({ultimo['consultorio']})")
            else:
                self.lbl_last.config(text="En atención: Ninguno")

        except Exception as e:
            print(f"Error al cargar listas: {e}")
            self.txt_espera.insert(tk.END, "Error al cargar datos")
            self.txt_atencion.insert(tk.END, "Error al cargar datos")

    def _verificar_cambios(self):
        """Verifica periódicamente si hay cambios en los datos"""
        try:
            nuevos_datos = cargar_datos()

            # Verificar si hay un nuevo llamado
            if 'ultimo_llamado' in nuevos_datos and nuevos_datos['ultimo_llamado']:
                if nuevos_datos['ultimo_llamado'].startswith("RELLAMADO_"):
                    mensaje = nuevos_datos['ultimo_llamado'].split('_',1)[1]
                    self._play_audio(mensaje)
                elif self.ultimo_llamado != nuevos_datos['ultimo_llamado']:
                    self._play_audio(nuevos_datos['ultimo_llamado'])
                
                self.ultimo_llamado = nuevos_datos['ultimo_llamado']

            self.datos = nuevos_datos
            self._cargar_listas()
            self.root.after(3000, self._verificar_cambios)
        except Exception as e:
            print(f"Error al verificar cambios: {e}")
            self.root.after(3000, self._verificar_cambios)

    def _play_audio(self, texto):
        """Reproduce el audio del mensaje"""
        if not self.audio_enabled:
            print("Audio deshabilitado, no se reproducirá el mensaje")
            return

        # Detener cualquier reproducción anterior
        self._stop_audio()

        # Crear un nuevo hilo para la reproducción
        self.current_audio_thread = threading.Thread(
            target=self._execute_audio_playback,
            args=(texto,),
            daemon=True
        )
        self.current_audio_thread.start()

    def _execute_audio_playback(self, texto):
        """Ejecuta la reproducción de audio en un hilo separado"""
        try:
            print(f"Intentando reproducir: {texto}")
            
            # Primero intentar con pygame
            if pygame.mixer.get_init():
                try:
                    # Crear archivo temporal
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                        temp_path = tmp.name
                    
                    # Generar audio
                    tts = gTTS(text=texto, lang='es', slow=False)
                    tts.save(temp_path)
                    
                    # Reproducir audio
                    sound = pygame.mixer.Sound(temp_path)
                    sound.play()
                    
                    # Esperar a que termine la reproducción
                    while pygame.mixer.get_busy():
                        time.sleep(0.1)
                        
                finally:
                    # Limpiar archivo temporal
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception as e:
                        print(f"Error al limpiar archivo temporal: {e}")
            
            # Si pygame falla, usar winsound
            else:
                winsound.Beep(1000, 500)
                time.sleep(0.3)
                winsound.Beep(1500, 500)
                
        except Exception as e:
            print(f"Error en reproducción de audio: {e}")
            # Como último recurso, mostrar en consola
            print(f"MENSAJE DE VOZ (no se pudo reproducir): {texto}")

    def _stop_audio(self):
        """Detiene cualquier reproducción de audio en curso"""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                for i in range(pygame.mixer.get_num_channels()):
                    pygame.mixer.Channel(i).stop()
        except Exception as e:
            print(f"Error al detener audio: {e}")

    def _on_close(self):
        """Maneja el cierre de la aplicación"""
        try:
            self._stop_audio()
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except:
            pass
        self.root.destroy()

    def run(self):
        """Inicia el bucle principal de la aplicación"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = SalaEspera()
        app.run()
    except Exception as e:
        print(f"Error fatal: {e}")
        # Mostrar mensaje de error al usuario
        tk.Tk().withdraw()
        tk.messagebox.showerror("Error", f"No se pudo iniciar la aplicación: {str(e)}")