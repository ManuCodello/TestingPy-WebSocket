import socket
import asyncio
import threading

username = input("Colocá tu nombre de usuario: ")

host = "127.0.0.1"
port = 55555

# Crear socket IPV4, TCP
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cliente.connect((host, port)) #conectar al servidor
cliente.setblocking(True)  # ← esto arregla el error WinError 10035

cola_mensajes = asyncio.Queue() # Cola para manejar mensajes de forma asíncrona

# Hilo para leer input del usuario y meter en la cola
def leer_input(loop):
    while True: # Bucle para leer continuamente
        try:
            texto = input() 
            mensaje = f"{username} : {texto}"  
            # Enviar la tarea al loop desde el hilo de input
            asyncio.run_coroutine_threadsafe(cola_mensajes.put(mensaje), loop)
        except Exception as e:  #
            print(f"Error leyendo input: {e}")
            break


# Recibir mensajes del servidor
async def recibir_mensajes():
    while True:
        try:
            data = await asyncio.get_event_loop().run_in_executor(None, cliente.recv, 1024)
            if data:
                mensaje = data.decode("utf-8")
                if mensaje == "@username":
                    cliente.send(username.encode("utf-8"))
                else:
                    print(mensaje)
            else:
                print("Servidor desconectado.")
                cliente.close()
                break
        except Exception as e:
            print(f"Error al recibir mensaje: {e}")
            cliente.close()
            break


# Enviar mensajes al servidor desde la cola
async def enviar_mensajes():
    while True:
        mensaje = await cola_mensajes.get()
        try:
            cliente.send(mensaje.encode("utf-8"))
        except Exception as e:
            print(f"Error al enviar mensaje: {e}")
            cliente.close()
            break


# Main del cliente
async def main():
    loop = asyncio.get_running_loop()

    # Iniciar el hilo para leer del teclado, pasándole el loop
    threading.Thread(target=leer_input, args=(loop,), daemon=True).start()

    # Ejecutar receptor y emisor
    await asyncio.gather(
        recibir_mensajes(),
        enviar_mensajes()
    )


# Ejecutar cliente
asyncio.run(main())
