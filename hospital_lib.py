import json
import os
import sys
from datetime import datetime
from PIL import Image, ImageTk
import tkinter as tk

def cargar_datos(archivo):
    """Carga los datos del archivo JSON o crea una estructura vacía si no existe"""
    try:
        if not os.path.exists(archivo):
            datos = {
                'pacientes': [],
                'ultimo_llamado': None,
                'especialidades': [
                    {'nombre': 'Traumatología', 'consultorio': 'Consultorio 1'},
                    {'nombre': 'Internista', 'consultorio': 'Consultorio 2'},
                    {'nombre': 'Cirugía', 'consultorio': 'Consultorio 3'},
                    {'nombre': 'Pediatría', 'consultorio': 'Consultorio 4'},
                    {'nombre': 'Ginecología', 'consultorio': 'Consultorio 5'},
                    {'nombre': 'Neurología', 'consultorio': 'Consultorio 6'},
                    {'nombre': 'Urólogo', 'consultorio': 'Consultorio 7'},
                    {'nombre': 'Cardiología', 'consultorio': 'Consultorio 8'},
                    {'nombre': 'Radiología', 'consultorio': 'Consultorio 9'},
                    {'nombre': 'Medicina', 'consultorio': 'Consultorio 10'},
                    {'nombre': 'Obstetricia 1', 'consultorio': 'Consultorio 11'},
                    {'nombre': 'Obstetricia 2', 'consultorio': 'Consultorio 12'},
                    {'nombre': 'Psicología', 'consultorio': 'Consultorio 13'},
                    {'nombre': 'Dental', 'consultorio': 'Consultorio 14'}
                ]
            }
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4)
            return datos
            
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        return {
            'pacientes': [],
            'ultimo_llamado': None,
            'especialidades': []
        }

def guardar_datos(archivo, datos):
    """Guarda los datos en el archivo JSON"""
    try:
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4)
        return True
    except Exception as e:
        print(f"Error al guardar datos: {e}")
        return False


def cargar_logo(parent):
    """
    Carga y devuelve un tk.Label con el logo 'logo_hospital.png'.
    En modo PyInstaller (frozen), lo busca en sys._MEIPASS.
    Sino, lo busca junto al ejecutable o en el mismo directorio del script.
    """
    posibles = []
    if getattr(sys, 'frozen', False):
        posibles.append(sys._MEIPASS)
        posibles.append(os.path.dirname(sys.executable))
    posibles.append(os.path.dirname(os.path.abspath(__file__)))

    image_path = None
    for base in posibles:
        ruta = os.path.join(base, 'logo_hospital.png')
        if os.path.isfile(ruta):
            image_path = ruta
            break

    if not image_path:
        print("Error al cargar logo: logo_hospital.png no encontrado en ninguna ruta conocida")
        return tk.Label(parent, text="Logo no encontrado", bg='#f0f8ff')

    try:
        img = Image.open(image_path)
        img = img.resize((200, 200), Image.LANCZOS)
        logo = ImageTk.PhotoImage(img)
        lbl = tk.Label(parent, image=logo, bg='#f0f8ff')
        lbl.image = logo  # Referencia para evitar GC
        return lbl
    except Exception as e:
        print(f"Error al procesar logo: {e}")
        return tk.Label(parent, text="Logo no cargado", bg='#f0f8ff')

def validar_nombre_paciente(nombre):
    """Valida que el nombre del paciente sea correcto"""
    if not nombre or len(nombre.strip()) < 3:
        return False, "El nombre debe tener al menos 3 caracteres"
    if any(c.isdigit() for c in nombre):
        return False, "El nombre no puede contener números"
    return True, ""

def obtener_consultorio_especialidad(datos, especialidad):
    """Obtiene el consultorio asignado a una especialidad"""
    for esp in datos.get('especialidades', []):
        if esp['nombre'].lower() == especialidad.lower():
            return esp['consultorio']
    return None

def obtener_especialidad_consultorio(datos, consultorio_id):
    """Obtiene la especialidad de un consultorio"""
    consultorio = f"Consultorio {consultorio_id}"
    for esp in datos.get('especialidades', []):
        if esp['consultorio'] == consultorio:
            return esp['nombre']
    return None

def obtener_pacientes_espera_consultorio(datos, consultorio_id):
    """Obtiene pacientes en espera para un consultorio específico"""
    consultorio = f"Consultorio {consultorio_id}"
    hoy = datetime.now().strftime("%Y-%m-%d")
    return [p for p in datos['pacientes'] 
           if p['consultorio'] == consultorio 
           and not p.get('atendido', False)
           and p['fecha_registro'].startswith(hoy)]

def obtener_historial_atencion_consultorio(datos, consultorio_id):
    """Obtiene historial de atención de un consultorio específico"""
    consultorio = f"Consultorio {consultorio_id}"
    hoy = datetime.now().strftime("%Y-%m-%d")
    return [p for p in datos['pacientes'] 
           if p['consultorio'] == consultorio 
           and p.get('atendido', False)
           and p['fecha_registro'].startswith(hoy)]
