import asyncio
import websockets
import mysql.connector
import serial
from datetime import datetime
import json

# Configuración de la base de datos
db_config = {
    'host': "localhost",
    'user': "root",
    'password': "Chaparro1",
    'database': "DB_PYTHON"
}

# Configura el puerto serial según tu configuración de Arduino
arduino_serial = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

def update_led_status_in_db(status):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Actualizar el estado del LED en la tabla estado_led
        cursor.execute("UPDATE estado_led SET led_status = %s WHERE id_estado_led = 1", (status,))

        # Determinar el mensaje del evento según el estado del LED
        if status == '1':
            message = 'Encendido'
        else:
            message = 'Apagado'

        # Insertar el evento en la tabla Estado_Eventos
        cursor.execute("INSERT INTO Estado_Eventos (evento_foco) VALUES (%s)", (message,))

        conn.commit()
    except mysql.connector.Error as e:
        print(f"Error de base de datos: {e}")
    finally:
        cursor.close()
        conn.close()

def get_led_status_from_db():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT led_status FROM estado_led WHERE id_estado_led = 1")
        status = cursor.fetchone()[0]
        return status
    except mysql.connector.Error as e:
        print(f"Error de base de datos: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_all_led():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT evento_fecha, evento_foco FROM Estado_Eventos")
        respuesta = cursor.fetchall()

        datos = []
        for fecha, foco in respuesta:
            fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")
            datos.append({"fecha": fecha_str, "estado": foco})

        return json.dumps(datos)
    except mysql.connector.Error as error:
        print(f"Error de base de datos {error}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

async def handle_led(websocket, path):
    try:
        async for message in websocket:
            parsed_message = json.loads(message)
            if parsed_message["type"] == "command":
                if parsed_message["value"] == "getAll":
                    all_led_data = get_all_led()
                    await websocket.send(json.dumps({"type": "data", "value": all_led_data}))
                elif parsed_message["value"] in ["1", "0"]:
                    update_led_status_in_db(parsed_message["value"])
                    arduino_serial.write(parsed_message["value"].encode())
                    await websocket.send(json.dumps({"type": "state", "value": parsed_message["value"]}))
                else:
                    print("Comando no reconocido:", parsed_message["value"])
            else:
                print("Tipo de mensaje no reconocido:", parsed_message["type"])
    except websockets.exceptions.ConnectionClosedOK:
        print("Cliente desconectado")

async def start_server():
    async with websockets.serve(handle_led, "localhost", 8765):
        await asyncio.Future()  # Ejecuta el servidor indefinidamente

if __name__ == "__main__":
    asyncio.run(start_server())
