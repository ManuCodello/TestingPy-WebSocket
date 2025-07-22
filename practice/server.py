#server.py
# Servidor de chat simple usando sockets y hilos en Python


import socket  
import threading  

# Dirección IP y puerto donde se ejecutará el servidor
HOST = "localhost"  # IP local (localhost) 192.168.0.1
PORT = 55555  # Puerto por el cual se conectarán los clientes

clientnames = {}  # Diccionario que guarda los nombres de los clientes conectados
servidor_activo = False  # Variable de control para saber si el servidor está activo
server = None  # Variable que contendrá el socket del servidor

# Función que maneja a cada cliente conectado
def manejar_clientes (cliente_socket, direccion):
    try:
        # 1. Recibir nombre una sola vez
        nombre = cliente_socket.recv(1024).decode('utf-8')  # Recibe el nombre del cliente
        clientnames[cliente_socket] = nombre  # Lo guarda en el diccionario con su socket como clave
        print(f"Cliente conectado desde {direccion}") 
        broadcast(f"🔵 {nombre} se ha unido al chat.", cliente_socket)  

        # 2. Loop de mensajes
        while True:
            mensaje = cliente_socket.recv(1024).decode('utf-8')  # Escucha mensajes del cliente
            if mensaje:
                broadcast(f"{nombre}: {mensaje}", cliente_socket) 
    except (ConnectionResetError, OSError):
        nombre_cliente = clientnames.get(cliente_socket, "Desconocido")
        broadcast(f"{nombre_cliente} se fue del chat.", cliente_socket)
        eliminar_cliente(cliente_socket)
    except Exception as e:
        print(f"💥 Error inesperado con cliente: {e}")
        eliminar_cliente(cliente_socket)

# Función para eliminar a un cliente del diccionario y cerrar su socket
def eliminar_cliente(cliente_socket):
    if cliente_socket in clientnames:
        del clientnames[cliente_socket]  
    try:
        cliente_socket.close()  #cerrar el socket
    except:
        pass  # Ignora errores si ya estaba cerrado

# Función para enviar un mensaje a todos los clientes, menos al que lo envió
def broadcast (mensaje_enviado, cliente_excluido):
    for cliente in list(clientnames.keys()):  # Recorre el nombre de los clientes conectados
        if cliente != cliente_excluido:  
            try:
                cliente.send(mensaje_enviado.encode('utf-8'))  # Envía el mensaje
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                print(f"❌ Error al enviar mensaje a un cliente: {e}")
                cliente.close()
                eliminar_cliente(cliente)
            except Exception as e:
                print(f"💥 Error inesperado en broadcast: {e}")
                cliente.close()
                eliminar_cliente(cliente)  

# Función que acepta nuevas conexiones entrantes al servidor
def aceptar_clientes ():   
    while True:
        try:
            cliente_socket, direccion = server.accept()  # Acepta una conexión entrante
            hilo = threading.Thread(target=manejar_clientes, args=(cliente_socket, direccion), daemon=True)
            hilo.start()  # Crea un hilo para manejar a ese cliente en paralelo
        except OSError as e:
            print(f"⚠️ Error aceptando clientes (probablemente el socket se cerró): {e}")
            break
        except Exception as e:
            print(f"💥 Error inesperado al aceptar clientes: {e}")
            break
# Función que controla el estado del servidor desde consola
def control_servidor():
    global server, servidor_activo  # Usa las variables globales

    while True:
        comando = input("🛠️  Comando (abrir / cerrar / salir): ").strip().lower()  

        if comando == "abrir" and not servidor_activo:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crea un socket TCP, con protocolos IPv4
            server.bind((HOST, PORT))  # Lo enlaza a la IP y puerto
            server.listen()  
            servidor_activo = True  
            print("Servidor ABIERTO y escuchando...") 
            
            # Acá arrancás el hilo que acepta clientes
            threading.Thread(target=aceptar_clientes, daemon=True).start()  # Inicia el hilo que aceptará clientes

        elif comando == "cerrar" and servidor_activo:
            servidor_activo = False  # Cambia el estado a inactivo
            server.close()  # Cierra el socket del servidor
            print("Servidor CERRADO, no acepta nuevos clientes") 

        elif comando == "salir":
            print("Cerrando servidor y terminando...")
            if servidor_activo:
                for cliente in list(clientnames.keys()):
                    try:
                        cliente.send("⚠️ El servidor se ha cerrado.".encode('utf-8'))
                        cliente.close()
                    except (BrokenPipeError, OSError):
                        pass
                    except Exception as e:
                        print(f"💥 Error inesperado cerrando cliente: {e}")
                    del clientnames[cliente]
                server.close()
            break
                

# Punto de entrada del programa
if __name__ == "__main__":
    control_servidor()  # Inicia la función principal de control


