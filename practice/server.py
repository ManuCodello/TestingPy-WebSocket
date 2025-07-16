import socket  # Librería para trabajar con sockets (conexiones de red)
import threading  # Librería para usar hilos (manejar múltiples clientes a la vez)

# Dirección IP y puerto donde se ejecutará el servidor
HOST = "127.0.0.1"  # IP local (localhost)
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
        print(f"Cliente conectado desde {direccion}")  # Muestra de qué dirección se conectó
        broadcast(f"🔵 {nombre} se ha unido al chat.", cliente_socket)  # Avisa a los demás que se unió

        # 2. Loop de mensajes
        while True:
            mensaje = cliente_socket.recv(1024).decode('utf-8')  # Escucha mensajes del cliente
            if mensaje:
                broadcast(f"{nombre}: {mensaje}", cliente_socket)  # Reenvía a todos los demás clientes
    except Exception as e:
        # Si el cliente se desconecta o hay error
        nombre_cliente = clientnames.get(cliente_socket, "Desconocido")  # Busca el nombre, si no lo encuentra usa "Desconocido"
        print(f"Error, {nombre_cliente} se ha desconectado: {e}")  # Muestra el error
        broadcast(f"{nombre_cliente} se fue del chat.", cliente_socket)  # Avisa al resto del chat

# Función para eliminar a un cliente del diccionario y cerrar su socket
def eliminar_cliente(cliente_socket):
    if cliente_socket in clientnames:
        del clientnames[cliente_socket]  # Elimina del diccionario
    
    try:
        cliente_socket.close()  # Intenta cerrar el socket
    except:
        pass  # Ignora errores si ya estaba cerrado

# Función para enviar un mensaje a todos los clientes, menos al que lo envió
def broadcast (mensaje_enviado, cliente_excluido):
    for cliente in list(clientnames.keys()):  # Recorre todos los clientes conectados
        if cliente != cliente_excluido:  # No le reenvía el mensaje al que lo envió
            try:
                cliente.send(mensaje_enviado.encode('utf-8'))  # Envía el mensaje
            except Exception as e:
                cliente.close()  # Si falla, cierra el socket
                print(f"Error, al enviar mensaje {e}")  # Muestra el error
                eliminar_cliente(cliente)  # Elimina al cliente de la lista

# Función que acepta nuevas conexiones entrantes al servidor
def aceptar_clientes ():   
    while True:
        try:
            cliente_socket, direccion = server.accept()  # Acepta una conexión entrante
            hilo = threading.Thread(target=manejar_clientes, args=(cliente_socket, direccion), daemon=True)
            hilo.start()  # Crea un hilo para manejar a ese cliente en paralelo
        except Exception as e:
            print(f"Error aceptando clientes: {e}")  # Si falla algo al aceptar, lo muestra
            break  # Sale del bucle

# Función que controla el estado del servidor desde consola
def control_servidor():
    global server, servidor_activo  # Usa las variables globales

    while True:
        comando = input("🛠️  Comando (abrir / cerrar / salir): ").strip().lower()  # Pide un comando por consola

        if comando == "abrir" and not servidor_activo:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crea un socket TCP
            server.bind((HOST, PORT))  # Lo enlaza a la IP y puerto
            server.listen()  # Lo pone a escuchar conexiones entrantes
            servidor_activo = True  # Marca el servidor como activo
            print("Servidor ABIERTO y escuchando...")  # Muestra mensaje de éxito
            
            # Acá arrancás el hilo que acepta clientes
            threading.Thread(target=aceptar_clientes, daemon=True).start()  # Inicia el hilo que aceptará clientes

        elif comando == "cerrar" and servidor_activo:
            servidor_activo = False  # Cambia el estado a inactivo
            server.close()  # Cierra el socket del servidor
            print("Servidor CERRADO (no acepta nuevos clientes)")  # Muestra mensaje

        elif comando == "salir":
            print("Cerrando servidor y terminando...")  # Muestra mensaje final
            if servidor_activo:
                server.close()  # Si está activo, lo cierra
            break  # Sale del bucle y termina la ejecución

        else:
            print("Comando inválido o acción no disponible en este estado.")  # Si el comando no es válido

# Punto de entrada del programa
if __name__ == "__main__":
    control_servidor()  # Inicia la función principal de control
