import psycopg2
from psycopg2.extras import RealDictCursor, DictCursor
from psycopg2.pool import SimpleConnectionPool
import tkinter as tk
from datetime import datetime
from PIL import Image, ImageTk
import os
import sys

# Configuración de la base de datos (ajusta según tu entorno)
DB_CONFIG = {
    'dbname': 'hospital',
    'user': 'postgres',
    'password': '123456',
    'host': 'localhost',
    'port': '5432'
}

# Pool de conexiones
connection_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    **DB_CONFIG
)

def obtener_conexion():
    try:
        return connection_pool.getconn()
    except psycopg2.Error as e:
        print(f"Error al obtener conexión del pool: {e}")
        raise

def liberar_conexion(conexion):
    try:
        if conexion:
            if not conexion.closed:
                conexion.rollback()
            connection_pool.putconn(conexion)
    except Exception as e:
        print(f"Error al liberar conexión: {e}")
        if conexion and not conexion.closed:
            conexion.close()

def marcar_paciente_atendido(paciente_id, consultorio):
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("""
                UPDATE pacientes_especialidades
                SET atendido = TRUE, fecha_atencion = NOW()
                WHERE paciente_id = %s AND consultorio = %s
            """, (paciente_id, consultorio))
            conexion.commit()
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
                SELECT p.id, p.nombre, e.nombre AS especialidad,
                       pe.consultorio, pe.fecha_registro, pe.atendido, pe.fecha_atencion
                FROM pacientes p
                JOIN pacientes_especialidades pe ON p.id = pe.paciente_id
                JOIN especialidades e ON pe.especialidad_id = e.id
                WHERE pe.consultorio = %s AND pe.atendido = FALSE
                ORDER BY pe.fecha_registro ASC
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
                SELECT p.id, p.nombre, e.nombre AS especialidad,
                       pe.consultorio, pe.fecha_registro, pe.atendido, pe.fecha_atencion
                FROM pacientes p
                JOIN pacientes_especialidades pe ON p.id = pe.paciente_id
                JOIN especialidades e ON pe.especialidad_id = e.id
                WHERE pe.consultorio = %s AND pe.atendido = TRUE
                ORDER BY pe.fecha_atencion DESC
            """, (consultorio,))
            return cursor.fetchall()
    except Exception as e:
        raise e
    finally:
        if conexion:
            liberar_conexion(conexion)

def cargar_datos():
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, nombre, consultorio FROM especialidades ORDER BY id")
            especialidades = cursor.fetchall()

            cursor.execute("""
                SELECT p.id, p.nombre, e.nombre AS especialidad,
                       pe.consultorio, pe.fecha_registro, pe.atendido, pe.fecha_atencion
                FROM pacientes p
                LEFT JOIN pacientes_especialidades pe ON p.id = pe.paciente_id
                LEFT JOIN especialidades e ON pe.especialidad_id = e.id
                WHERE DATE(p.fecha_registro) = CURRENT_DATE
                ORDER BY pe.fecha_registro
            """)
            pacientes = cursor.fetchall()

            cursor.execute("SELECT mensaje FROM ultimos_llamados ORDER BY fecha DESC LIMIT 1")
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
            cursor.execute("INSERT INTO ultimos_llamados (mensaje) VALUES (%s)", (mensaje,))
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

def guardar_paciente_multiple_especialidades(nombre, lista_especialidades, lista_consultorios):
    if len(lista_especialidades) != len(lista_consultorios):
        raise Exception("La cantidad de especialidades y consultorios debe coincidir")

    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pacientes (nombre, fecha_registro, atendido)
                VALUES (%s, CURRENT_TIMESTAMP, FALSE)
                RETURNING id
            """, (nombre,))
            paciente_id = cursor.fetchone()[0]

            for esp_nombre, consultorio in zip(lista_especialidades, lista_consultorios):
                cursor.execute("SELECT id FROM especialidades WHERE nombre = %s", (esp_nombre,))
                res = cursor.fetchone()
                if not res:
                    raise Exception(f"Especialidad '{esp_nombre}' no encontrada")
                especialidad_id = res[0]

                cursor.execute("""
                    INSERT INTO pacientes_especialidades (paciente_id, especialidad_id, consultorio)
                    VALUES (%s, %s, %s)
                """, (paciente_id, especialidad_id, consultorio))

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
                SELECT p.id, p.nombre, pe.consultorio
                FROM pacientes p
                JOIN pacientes_especialidades pe ON p.id = pe.paciente_id
                WHERE pe.consultorio = %s
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
                RETURNING id, nombre, atendido
            """, (paciente['id'],))

            paciente_atendido = cursor.fetchone()
            conexion.commit()

            return {
                'id': paciente_atendido['id'],
                'nombre': paciente_atendido['nombre'],
                'consultorio': paciente['consultorio']
            }
    except Exception as e:
        if conexion:
            conexion.rollback()
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
                SELECT p.id, p.nombre, p.fecha_registro,
                       e.nombre AS especialidad,
                       pe.consultorio
                FROM pacientes p
                JOIN pacientes_especialidades pe ON p.id = pe.paciente_id
                JOIN especialidades e ON pe.especialidad_id = e.id
                WHERE pe.consultorio = %s
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
                SELECT p.id, p.nombre, p.fecha_registro, p.fecha_atencion,
                    STRING_AGG(DISTINCT e.nombre, ', ') AS especialidades,
                    pe.consultorio
                FROM pacientes p
                JOIN pacientes_especialidades pe ON p.id = pe.paciente_id
                JOIN especialidades e ON pe.especialidad_id = e.id
                WHERE pe.consultorio = %s
                  AND p.atendido = TRUE
                  AND DATE(p.fecha_registro) = CURRENT_DATE
                GROUP BY p.id, p.nombre, p.fecha_registro, p.fecha_atencion, pe.consultorio
                ORDER BY p.fecha_atencion DESC
            """, (consultorio,))
            return cursor.fetchall()
    except Exception as e:
        raise e
    finally:
        if conexion:
            liberar_conexion(conexion)

def actualizar_paciente(paciente_id, nombre, especialidad_nombre, consultorio):
    conexion = None
    try:
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id FROM especialidades WHERE nombre = %s", (especialidad_nombre,))
            res = cursor.fetchone()
            if not res:
                raise Exception("Especialidad no encontrada")
            especialidad_id = res[0]

            cursor.execute("""
                UPDATE pacientes
                SET nombre = %s
                WHERE id = %s
            """, (nombre, paciente_id))

            cursor.execute("""
                SELECT 1 FROM pacientes_especialidades 
                WHERE paciente_id = %s AND especialidad_id = %s
            """, (paciente_id, especialidad_id))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE pacientes_especialidades 
                    SET consultorio = %s 
                    WHERE paciente_id = %s AND especialidad_id = %s
                """, (consultorio, paciente_id, especialidad_id))
            else:
                cursor.execute("""
                    INSERT INTO pacientes_especialidades (paciente_id, especialidad_id, consultorio)
                    VALUES (%s, %s, %s)
                """, (paciente_id, especialidad_id, consultorio))

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





