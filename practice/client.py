#cliente.py
# Cliente de chat simple usando sockets y asyncio en Python


import socket  # Importa la librería para crear conexiones de red (sockets)
import threading  # Importa la librería para manejar múltiples hilos (multitarea)
import time  # Importa la librería para manejar el tiempo (esperas, pausas)

HOST = "127.0.0.1"  # Dirección IP del servidor (localhost en este caso)
PORT = 55555  # Puerto por el cual el cliente se conecta al servidor

def recibir_mensajes(cliente):
    # Función que corre en segundo plano para recibir mensajes del servidor
    while True:
        try:
            respuesta = cliente.recv(1024)  # Intenta recibir hasta 1024 bytes de datos
            if not respuesta:
                print("❌ El servidor se desconectó.")  # Si no recibe nada, se asume que se cerró la conexión
                break  # Sale del bucle y termina el hilo
            print(respuesta.decode('utf-8'))  # Decodifica el mensaje y lo imprime en consola
        except (ConnectionResetError, OSError) as e:
            print(f"❌ Conexión perdida con el servidor: {e}")
            break
        except Exception as e:
            print(f"💥 Error inesperado al recibir mensaje: {e}")
            break

def conectar_con_reintentos():
    """Intenta conectarse al servidor. Si falla, reintenta cada 3 segundos."""
    while True:
        try:
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crea un nuevo socket TCP con IPV4
            cliente.connect((HOST, PORT))  # conecta al servidor con IP y puerto definidos
            print("✅ Conectado al servidor.")  
            return cliente  # Devuelve el socket ya conectado
        except (ConnectionRefusedError, TimeoutError, OSError):
            print("🔁 Reintentando en 3 segundos...")
            time.sleep(3)

def main():
    cliente = conectar_con_reintentos()  # Llama a la función que intenta conectarse al servidor

    nombre = input("🧑 Tu nombre: ")  # Pide al usuario que escriba su nombre
    
    cliente.send(nombre.encode('utf-8'))  # Envía el nombre al servidor codificado 
    
    threading.Thread(target=recibir_mensajes, args=(cliente,), daemon=True).start()
    # hilo que escucha los mensajes que llegan desde el servidor

    while True:
        
        mensaje = input()  # Espera a que el usuario escriba un mensaje
        if not mensaje.strip().lower() == "/salir":
            mensaje_con_nombre = f"{mensaje}"
            try:
                cliente.send(mensaje_con_nombre.encode('utf-8'))
            except Exception as e:
                print(f"❌ Error al enviar mensaje: {e}")  # Muestra error si no se puede enviar
                break  
        else:
            try:
                cliente.close()
                print("👋 Cerrando cliente...")
                break
            except OSError as e:
                print(f"⚠️ Error al cerrar conexión: {e}")
                break



if __name__ == "__main__":
    main()  # Punto de entrada principal del programa: ejecuta la función main




