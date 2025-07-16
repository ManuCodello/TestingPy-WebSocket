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
        except Exception as e:
            print(f"❌ Error al recibir mensaje: {e}")  # Si hay error, lo muestra
            break  # Sale del bucle

def conectar_con_reintentos():
    """Intenta conectarse al servidor. Si falla, reintenta cada 3 segundos."""
    while True:
        try:
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crea un nuevo socket TCP
            cliente.connect((HOST, PORT))  # Intenta conectarse al servidor con IP y puerto definidos
            print("✅ Conectado al servidor.")  # Muestra que la conexión fue exitosa
            return cliente  # Devuelve el socket ya conectado
        except Exception as e:
            print(f"⚠️ Error al conectar con el servidor: {e}")  # Muestra el error si no se pudo conectar
            print("🔁 Reintentando en 3 segundos...")  # Aviso de reintento
            time.sleep(3)  # Espera 3 segundos antes de volver a intentar

def main():
    cliente = conectar_con_reintentos()  # Llama a la función que intenta conectarse al servidor

    nombre = input("🧑 Tu nombre: ")  # Pide al usuario que escriba su nombre
    cliente.send(nombre.encode('utf-8'))  # Envía el nombre al servidor codificado en UTF-8

    threading.Thread(target=recibir_mensajes, args=(cliente,), daemon=True).start()
    # Lanza un hilo que escucha los mensajes que llegan desde el servidor

    while True:
        mensaje = input()  # Espera a que el usuario escriba un mensaje
        if mensaje.strip().lower() == "/salir":
            cliente.send(f"⚠️ {nombre} ha salido del chat.".encode('utf-8'))  # Informa al servidor que este cliente se va
            cliente.close()  # Cierra el socket
            print("👋 Cerrando cliente...")  # Mensaje final
            break  # Sale del bucle y termina el programa

        mensaje_con_nombre = f"{nombre}: {mensaje}"  # Prepara el mensaje con el nombre del cliente al inicio
        try:
            cliente.send(mensaje_con_nombre.encode('utf-8'))  # Envía el mensaje al servidor codificado en UTF-8
        except Exception as e:
            print(f"❌ Error al enviar mensaje: {e}")  # Muestra error si no se puede enviar
            break  # Termina el bucle si ocurre un error al enviar

if __name__ == "__main__":
    main()  # Punto de entrada principal del programa: ejecuta la función main




