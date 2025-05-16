import psycopg2
from psycopg2.extras import RealDictCursor, DictCursor
from psycopg2.pool import SimpleConnectionPool
import tkinter as tk
from datetime import datetime
from PIL import Image, ImageTk
import os
import sys

# Configuración de la base de datos (mejor usar variables de entorno)
DB_CONFIG = {
    'dbname': 'hospital',
    'user': 'postgres',
    'password': '123456',
    'host': 'localhost',
    'port': '5432'
}

# Creación del pool de conexiones
connection_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    **DB_CONFIG
)

def obtener_conexion():
    """Obtiene una conexión del pool"""
    try:
        return connection_pool.getconn()
    except psycopg2.Error as e:
        print(f"Error al obtener conexión del pool: {e}")
        raise

def liberar_conexion(conexion):
    """Libera una conexión devolviéndola al pool"""
    try:
        if conexion:
            if not conexion.closed:
                conexion.rollback()  # Asegurar que no hay transacciones pendientes
            connection_pool.putconn(conexion)
    except Exception as e:
        print(f"Error al liberar conexión: {e}")
        if conexion and not conexion.closed:
            conexion.close()

def cargar_datos():
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, nombre, consultorio FROM especialidades ORDER BY id")
            especialidades = cursor.fetchall()

            cursor.execute("""
                SELECT p.id, p.nombre, p.consultorio, p.fecha_registro, 
                       p.atendido, p.fecha_atencion, e.nombre as especialidad
                FROM pacientes p
                LEFT JOIN especialidades e ON p.especialidad_id = e.id
                WHERE DATE(p.fecha_registro) = CURRENT_DATE
                ORDER BY p.fecha_registro
            """)
            pacientes = cursor.fetchall()
            
            # Nuevo: obtener el último llamado desde alguna tabla o configuración
            cursor.execute("""
                SELECT mensaje FROM ultimos_llamados ORDER BY fecha DESC LIMIT 1
            """)
            ultimo = cursor.fetchone()
            ultimo_llamado = ultimo['mensaje'] if ultimo else None


        return {
            'especialidades': especialidades,
            'pacientes': pacientes,
            'ultimo_llamado': ultimo_llamado
        }
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        raise
    finally:
        if conexion:
            liberar_conexion(conexion)

def guardar_ultimo_llamado(mensaje):
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO ultimos_llamados (mensaje) VALUES (%s)
            """, (mensaje,))
            conexion.commit()
    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error al guardar último llamado: {e}")
        raise
    finally:
        if conexion:
            liberar_conexion(conexion)
            
def limpiar_ultimo_llamado():
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM ultimos_llamados")
            conexion.commit()
    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error al limpiar último llamado: {e}")
        raise
    finally:
        if conexion:
            liberar_conexion(conexion)


def guardar_paciente(nombre, especialidad_nombre, consultorio):
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM pacientes 
                WHERE nombre = %s 
                AND DATE(fecha_registro) = CURRENT_DATE 
                AND atendido = FALSE
            """, (nombre,))
            if cursor.fetchone():
                raise Exception("Este paciente ya tiene un turno pendiente para hoy")

            cursor.execute("SELECT id FROM especialidades WHERE nombre = %s", (especialidad_nombre,))
            especialidad_id = cursor.fetchone()
            if not especialidad_id:
                raise Exception("Especialidad no encontrada")
            especialidad_id = especialidad_id[0]

            cursor.execute("""
                INSERT INTO pacientes 
                (nombre, especialidad_id, consultorio, fecha_registro)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (nombre, especialidad_id, consultorio))
            
            paciente_id = cursor.fetchone()[0]
            conexion.commit()
            return paciente_id
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise e
    finally:
        if conexion:
            liberar_conexion(conexion)

def llamar_siguiente_paciente(consultorio_id):
    consultorio = f"Consultorio {consultorio_id}"
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT p.id, p.nombre, e.nombre as especialidad, p.consultorio
                FROM pacientes p
                JOIN especialidades e ON p.especialidad_id = e.id
                WHERE p.consultorio = %s 
                AND p.atendido = FALSE 
                AND DATE(p.fecha_registro) = CURRENT_DATE
                ORDER BY p.fecha_registro ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """, (consultorio,))
            
            paciente = cursor.fetchone()
            if not paciente:
                return None

            cursor.execute("""
                UPDATE pacientes 
                SET atendido = TRUE, 
                    fecha_atencion = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, nombre, consultorio
            """, (paciente['id'],))
            
            paciente_atendido = cursor.fetchone()
            conexion.commit()
            return dict(paciente_atendido)
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise e
    finally:
        if conexion:
            liberar_conexion(conexion)

def actualizar_paciente(paciente_id, nombre, especialidad_nombre, consultorio):
    """Actualiza los datos de un paciente dado su ID"""
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id FROM especialidades WHERE nombre = %s", (especialidad_nombre,))
            especialidad_id = cursor.fetchone()
            if not especialidad_id:
                raise Exception("Especialidad no encontrada")
            especialidad_id = especialidad_id[0]

            cursor.execute("""
                UPDATE pacientes
                SET nombre = %s, especialidad_id = %s, consultorio = %s
                WHERE id = %s
            """, (nombre, especialidad_id, consultorio, paciente_id))

            conexion.commit()
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise e
    finally:
        if conexion:
            liberar_conexion(conexion)

def cargar_logo(parent):
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
        lbl.image = logo
        return lbl
    except Exception as e:
        print(f"Error al procesar logo: {e}")
        return tk.Label(parent, text="Logo no cargado", bg='#f0f8ff')

def validar_nombre_paciente(nombre):
    if not nombre or len(nombre.strip()) < 3:
        return False, "El nombre debe tener al menos 3 caracteres"
    if any(c.isdigit() for c in nombre):
        return False, "El nombre no puede contener números"
    return True, ""

def obtener_consultorio_especialidad(datos, especialidad):
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT consultorio FROM especialidades 
                WHERE nombre = %s
            """, (especialidad,))
            consultorio = cursor.fetchone()
            return consultorio[0] if consultorio else None
    except Exception as e:
        raise e
    finally:
        if conexion:
            liberar_conexion(conexion)

def obtener_especialidad_consultorio(datos, consultorio_id):
    consultorio = f"Consultorio {consultorio_id}"
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT nombre FROM especialidades 
                WHERE consultorio = %s
            """, (consultorio,))
            especialidad = cursor.fetchone()
            return especialidad[0] if especialidad else None
    except Exception as e:
        raise e
    finally:
        if conexion:
            liberar_conexion(conexion)

def obtener_pacientes_espera_consultorio(consultorio_id):
    consultorio = f"Consultorio {consultorio_id}"
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT p.id, p.nombre, p.fecha_registro, e.nombre as especialidad
                FROM pacientes p
                JOIN especialidades e ON p.especialidad_id = e.id
                WHERE p.consultorio = %s 
                AND p.atendido = FALSE 
                AND DATE(p.fecha_registro) = CURRENT_DATE
                ORDER BY p.fecha_registro ASC
            """, (consultorio,))
            return cursor.fetchall()
    except Exception as e:
        raise e
    finally:
        if conexion:
            liberar_conexion(conexion)

def obtener_historial_atencion_consultorio(consultorio_id):
    consultorio = f"Consultorio {consultorio_id}"
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT p.id, p.nombre, p.fecha_registro, 
                       p.fecha_atencion, e.nombre as especialidad
                FROM pacientes p
                JOIN especialidades e ON p.especialidad_id = e.id
                WHERE p.consultorio = %s 
                AND p.atendido = TRUE 
                AND DATE(p.fecha_registro) = CURRENT_DATE
                ORDER BY p.fecha_atencion DESC
            """, (consultorio,))
            return cursor.fetchall()
    except Exception as e:
        raise e
    finally:
        if conexion:
            liberar_conexion(conexion)



