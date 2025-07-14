import threading
import socket

# Dirección IP y puerto del servidor
host = "127.0.0.1"
port = 55555

# Creación del socket TCP (SOCK_STREAM)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
print(f'Server corriendo en: {host} : {port}')

# Diccionario que relaciona sockets con sus nombres de usuario
usuarios = {}  # cliente_socket: username


# Envía un mensaje a todos los clientes conectados, excepto el que lo envió
def broadcast(mensaje, cliente_excluido):
    for cliente in list(usuarios.keys()):
        if cliente != cliente_excluido:
            try:
                cliente.send(mensaje)
            except:
                # Si el cliente falla, lo eliminamos del diccionario
                cliente.close()
                if cliente in usuarios:
                    del usuarios[cliente]


# Maneja todos los mensajes de un cliente individual
def manejo_mensajes(cliente):
    while True:
        try:
            mensaje = cliente.recv(1024)
            broadcast(mensaje, cliente)
        except:
            # Si ocurre un error, eliminamos al cliente y avisamos al resto
            username = usuarios.get(cliente, "Desconocido")
            broadcast(f'Ocurrió un error con el usuario: {username}'.encode('utf-8'), cliente)
            cliente.close()
            if cliente in usuarios:
                del usuarios[cliente]
            break


# Acepta nuevas conexiones de clientes y arranca un hilo por cliente
def recibir_conexiones():
    while True:
        cliente, address = server.accept()
        cliente.send('@username'.encode('utf-8'))
        try:
            username = cliente.recv(1024).decode('utf-8')
        except:
            cliente.close()
            continue

        usuarios[cliente] = username
        print(f'{username} se conectó desde {str(address)}')

        mensaje = f'El usuario: {username} entró al chat'.encode('utf-8')
        broadcast(mensaje, cliente)
        cliente.send('Conectado al servidor.'.encode('utf-8'))

        hilo = threading.Thread(target=manejo_mensajes, args=(cliente,), daemon=True)
        hilo.start()


# Arranca la escucha del servidor
recibir_conexiones()
