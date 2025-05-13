import tkinter as tk
from tkinter import font as tkfont
import time
import pygame
from datetime import datetime
from gtts import gTTS
import winsound
from PIL import Image, ImageTk
import os
from hospital_lib import cargar_datos, guardar_datos

# Configuración de tamaños
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FONT_TITLE_SIZE = 28
FONT_LIST_SIZE = 26
LOGO_WIDTH = 800
LOGO_HEIGHT = 600

class SalaEspera:
    def __init__(self):
        try:
            # Inicializa audio
            pygame.mixer.quit()
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

            # Datos
            self.archivo = 'datos_hospital.json' #r'\\192.168.10.220\cita_medicas_hap\datos_hospital.json'
            self.datos = cargar_datos(self.archivo)
            self.ultimo_llamado = None
            self.logo = None

            # Ventana principal
            self.root = tk.Tk()
            self.root.title("Sala de Espera – Hospital de Apoyo Palpa")
            self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
            self.root.minsize(800, 600)
            self.root.resizable(True, True)
            self.root.configure(bg='#f0f0f0')
            self.root.state('zoomed')

            # Configuración de grid
            self.root.grid_columnconfigure(0, weight=3, minsize=300)  # Columna izquierda con ancho fijo mínimo
            self.root.grid_columnconfigure(1, weight=7, minsize=500)  # Columna derecha con ancho fijo mínimo
            self.root.grid_rowconfigure(0, weight=1)

            # Fuentes
            self.fuente_tit = tkfont.Font(family='Arial', size=FONT_TITLE_SIZE, weight='bold')
            self.fuente_lst = tkfont.Font(family='Arial', size=FONT_LIST_SIZE)

            self._setup_ui()
            self._cargar_listas()
            self._verificar_cambios()

        except Exception as e:
            print(f"Error al iniciar Sala de Espera: {e}")
            raise

    def _setup_ui(self):
        # Columna Izquierda
        izq = tk.Frame(self.root, bg='black')
        izq.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        izq.grid_rowconfigure(0, weight=1)
        izq.grid_columnconfigure(0, weight=1)

        # Logo
        try:
            image = Image.open("logo_hospital.png")
            image = image.resize((LOGO_WIDTH, LOGO_HEIGHT), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(image)
            tk.Label(izq, image=self.logo, bg='black').grid(row=0, column=0, pady=(10,20))
        except:
            tk.Label(izq, text="HOSPITAL DE APOYO PALPA", 
                    font=('Arial', FONT_TITLE_SIZE, 'bold'), 
                    fg='white', bg='black').grid(row=0, column=0, pady=(10,20))

        # Reloj
        self.lbl_reloj = tk.Label(izq, font=('Arial', FONT_TITLE_SIZE), fg='white', bg='black')
        self.lbl_reloj.grid(row=1, column=0, pady=(0,5))
        self._update_clock()

        # Último atendido
        self.lbl_last = tk.Label(izq, font=('Arial', FONT_LIST_SIZE + 5), fg='white', bg='black', width=50, anchor='w')
        self.lbl_last.grid(row=2, column=0, pady=(5,20))
        self.lbl_last.config(text="Último atendido: Ninguno")

        # Columna Derecha
        der = tk.Frame(self.root, bg='#f0f0f0')
        der.grid(row=0, column=1, sticky='nsew', padx=(0,5), pady=10)
        der.grid_rowconfigure(0, weight=1)
        der.grid_rowconfigure(1, weight=1)  # Aseguramos que ambos paneles tengan el mismo peso
        der.grid_columnconfigure(0, weight=1, minsize=400)

        # Panel EN ESPERA
        espera = tk.Frame(der, bg='#e6f3ff', bd=2, relief=tk.RAISED)
        espera.grid(row=0, column=0, sticky='nsew', pady=(0,3), padx=5)
        espera.grid_columnconfigure(0, weight=1)
        espera.grid_rowconfigure(1, weight=1)
        tk.Label(espera, text="EN ESPERA", font=self.fuente_tit, bg='#004a99', fg='white').grid(row=0, column=0, sticky='ew', pady=1)
        # Listbox estático (width en caracteres, height en filas)
        self.txt_espera = tk.Listbox(espera, font=self.fuente_lst, bg='#e6f3ff', width=40, height=20)
        self.txt_espera.grid(row=1, column=0, sticky='nsew')

        # Panel EN ATENCIÓN
        atencion = tk.Frame(der, bg='#ffe6e6', bd=2, relief=tk.RAISED)
        atencion.grid(row=1, column=0, sticky='nsew', pady=(3,0), padx=5)
        atencion.grid_columnconfigure(0, weight=1)
        atencion.grid_rowconfigure(1, weight=1)
        tk.Label(atencion, text="EN ATENCIÓN", font=self.fuente_tit, bg='#990000', fg='white').grid(row=0, column=0, sticky='ew', pady=1)
        self.txt_atencion = tk.Listbox(atencion, font=self.fuente_lst, bg='#ffe6e6', width=40, height=20)
        self.txt_atencion.grid(row=1, column=0, sticky='nsew')

    def _update_clock(self):
        self.lbl_reloj.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)

    def _cargar_listas(self):
        """Carga las listas de pacientes en espera y en atención"""
        self.txt_espera.delete(0, tk.END)
        self.txt_atencion.delete(0, tk.END)

        # Agrupar pacientes por consultorio
        pacientes_por_consultorio = {}
        hoy = datetime.now().strftime("%Y-%m-%d")
        
        for p in self.datos['pacientes']:
            if p['fecha_registro'].startswith(hoy):
                consultorio = p['consultorio']
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
            
            self.txt_espera.insert(tk.END, f"--- {consultorio} ---")
            for p in pacientes:
                h = p['fecha_registro'].split(' ')[1][:5]
                self.txt_espera.insert(tk.END, f"  {p['id']}. {p['nombre']} ({h})")

        # Mostrar atendidos ordenados por tiempo de atención
        todos_atendidos = []
        for consultorio in pacientes_por_consultorio:
            todos_atendidos.extend(pacientes_por_consultorio[consultorio]['atendidos'])
        
        todos_atendidos.sort(key=lambda x: x.get('fecha_atencion', ''), reverse=True)
        
        for p in todos_atendidos[:20]:  # Mostrar solo los últimos 20
            h_reg = p['fecha_registro'].split(' ')[1][:5]
            h_aten = p.get('fecha_atencion', '').split(' ')[1][:5] if 'fecha_atencion' in p else ''
            self.txt_atencion.insert(tk.END, 
                                   f"{p['id']}. {p['nombre']} ({p['consultorio']}) - Reg: {h_reg}, At: {h_aten}")

        # Actualizar último atendido
        if todos_atendidos:
            ultimo = todos_atendidos[0]
            self.lbl_last.config(text=f"En atención: {ultimo['id']}. {ultimo['nombre']} ({ultimo['consultorio']})")
        else:
            self.lbl_last.config(text="En atención: Ninguno")

        if self.txt_espera.size() == 0:
            self.txt_espera.insert(tk.END, "Sin pacientes en espera")
        if self.txt_atencion.size() == 0:
            self.txt_atencion.insert(tk.END, "Sin atenciones hoy")

    def _verificar_cambios(self):
        try:
            nuevos_datos = cargar_datos(self.archivo)
            pygame.mixer.music.stop()

            if 'ultimo_llamado' in nuevos_datos and nuevos_datos['ultimo_llamado'] and nuevos_datos['ultimo_llamado'].startswith("RELLAMADO_"):
                mensaje = nuevos_datos['ultimo_llamado'].split('_',1)[1]
                nuevos_datos['ultimo_llamado'] = None
                guardar_datos(self.archivo, nuevos_datos)
                self._play_audio(mensaje)
                self.datos = nuevos_datos
                self._cargar_listas()
                self.root.after(3000, self._verificar_cambios)
                return

            # Verificar si hay nuevos pacientes atendidos
            nuevos_atendidos = [p for p in nuevos_datos['pacientes'] 
                              if p.get('atendido') and 
                              (not self.datos or 
                               not any(p2['id'] == p['id'] and p2.get('atendido') 
                                      for p2 in self.datos['pacientes']))]
            
            if nuevos_atendidos:
                ultimo = max(nuevos_atendidos, key=lambda x: x.get('fecha_atencion', ''))
                mensaje = f"Paciente {ultimo['nombre']}, favor dirigirse al {ultimo['consultorio']}"
                self._play_audio(mensaje)

            self.datos = nuevos_datos
            self._cargar_listas()
            self.root.after(3000, self._verificar_cambios)
        except Exception as e:
            print(f"Error al verificar cambios: {e}")
            self.root.after(3000, self._verificar_cambios)

    """def _play_audio(self, texto):
        try:
            # Limitar la longitud del texto para TTS
            if len(texto) > 200:
                texto = texto[:200] + "..."
                
            pygame.mixer.quit()
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            temp_file = f"temp_audio_{int(time.time())}.mp3"
            tts = gTTS(text=texto, lang='es', slow=False)
            tts.save(temp_file)
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): 
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
            os.remove(temp_file)
        except Exception as e:
            print(f"Error en reproducción de audio: {e}")
            winsound.Beep(1000, 500)"""
    
    def _play_audio(self, texto):
       try:
           # Limitar la longitud del texto para TTS
           max_length = 200  # Limite máximo de caracteres por segmento
           if len(texto) > max_length:
               # Divide el texto en fragmentos de longitud adecuada
               texto_fragments = [texto[i:i+max_length] for i in range(0, len(texto), max_length)]
           else:
               texto_fragments = [texto]
        
               # Reproduce cada fragmento de texto por separado
           for fragment in texto_fragments:
               pygame.mixer.quit()
               pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
               temp_file = f"temp_audio_{int(time.time())}.mp3"
               tts = gTTS(text=fragment, lang='es', slow=False)
               tts.save(temp_file)
               pygame.mixer.music.load(temp_file)
               pygame.mixer.music.play()
               while pygame.mixer.music.get_busy():  # Esperar a que termine la reproducción
                  pygame.time.Clock().tick(10)
               pygame.mixer.music.unload()
               os.remove(temp_file)  # Eliminar el archivo temporal después de reproducirlo

       except Exception as e:
           print(f"Error en reproducción de audio: {e}")
           winsound.Beep(1000, 500)


    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = SalaEspera()
        app.run()
    except Exception as e:
        print(f"Error fatal: {e}")
