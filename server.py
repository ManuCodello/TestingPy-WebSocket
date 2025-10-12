# server.py

import socket
import threading
import logging
from protocol import Protocolo # Importamos nuestra clase de protocolo

# Configuración básica de logging para mostrar mensajes informativos y de error.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Servidor:
    def __init__(self, host='127.0.0.1', port=55555):
        """
        Inicializa el servidor.
        
        Args:
            host (str): La dirección IP en la que el servidor escuchará.
            port (int): El puerto en el que el servidor escuchará.
        """
        self.host = host
        self.port = port
        self.socket_servidor = None
        # Diccionario para almacenar los clientes conectados. {socket: username}
        self.clientes = {}
        # Un Lock para evitar problemas de concurrencia al modificar la lista de clientes desde múltiples hilos.
        self.lock_clientes = threading.Lock()

    def iniciar(self):
        """
        Inicia el servidor, lo enlaza a la dirección/puerto y comienza a escuchar conexiones.
        """
        # Crea un socket TCP/IP (IPv4).
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Permite reutilizar la dirección del socket inmediatamente después de cerrarlo.
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Enlaza el socket a la dirección y puerto especificados.
        self.socket_servidor.bind((self.host, self.port))
        # Pone el servidor en modo de escucha, aceptando hasta 5 conexiones en cola.
        self.socket_servidor.listen(5)
        logging.info(f'Servidor escuchando en {self.host}:{self.port}')

        try:
            # Bucle infinito para aceptar nuevas conexiones de clientes.
            while True:
                # Acepta una nueva conexión. `accept()` es bloqueante.
                socket_cliente, direccion = self.socket_servidor.accept()
                logging.info(f'Conexión aceptada desde {direccion}')
                
                # Crea un nuevo hilo para manejar al cliente.
                # `daemon=True` permite que el programa principal termine aunque los hilos sigan corriendo.
                hilo_cliente = threading.Thread(
                    target=self._manejar_cliente,
                    args=(socket_cliente,),
                    daemon=True
                )
                hilo_cliente.start()
        except KeyboardInterrupt:
            logging.info("Servidor finalizando por petición del usuario (Ctrl+C).")
        finally:
            # Cierra el socket principal del servidor.
            self.socket_servidor.close()

    def _manejar_cliente(self, socket_cliente):
        """
        Gestiona la conexión de un cliente individual: recibe su nombre y sus mensajes.
        Esta función se ejecuta en un hilo separado por cada cliente.
        """
        nombre_usuario = None
        try:
            # 1. Solicitar y recibir el nombre de usuario.
            Protocolo.enviar(socket_cliente, {"type": "username_request"})
            respuesta = Protocolo.recibir(socket_cliente)
            
            if not respuesta or "username" not in respuesta:
                # Si el cliente no envía un nombre de usuario válido, se cierra la conexión.
                return
            
            nombre_usuario = respuesta["username"].strip()
            if not nombre_usuario:
                return

            # 2. Registrar al cliente y notificar a los demás.
            # Usamos 'with self.lock_clientes:' para asegurar que solo un hilo a la vez modifique el diccionario.
            with self.lock_clientes:
                self.clientes[socket_cliente] = nombre_usuario
            
            logging.info(f'{nombre_usuario} se ha unido al chat.')
            self.broadcast({"type": "join", "username": nombre_usuario}, socket_cliente)

            # 3. Bucle para recibir mensajes del cliente.
            while True:
                mensaje = Protocolo.recibir(socket_cliente)
                if not mensaje:
                    # Si `recibir` devuelve None, el cliente se desconectó.
                    break
                
                # Si el mensaje es de tipo 'message', lo retransmitimos.
                if mensaje.get("type") == "message":
                    self.broadcast({
                        "type": "message",
                        "username": nombre_usuario,
                        "text": mensaje.get("text", "")
                    }, socket_cliente)

        except Exception as e:
            logging.error(f"Error con el cliente {nombre_usuario}: {e}")
        
        finally:
            # 4. Limpieza: eliminar al cliente cuando se desconecta o hay un error.
            self._eliminar_cliente(socket_cliente, nombre_usuario)

    def broadcast(self, mensaje, socket_emisor):
        """
        Envía un mensaje a todos los clientes conectados, excepto al que lo envió.
        """
        with self.lock_clientes:
            # Iteramos sobre una copia de las claves para poder modificar el diccionario de forma segura.
            for cliente in list(self.clientes.keys()):
                if cliente != socket_emisor:
                    try:
                        Protocolo.enviar(cliente, mensaje)
                    except Exception:
                        # Si falla el envío, asumimos que el cliente está desconectado y lo eliminamos.
                        self._eliminar_cliente(cliente, self.clientes.get(cliente))

    def _eliminar_cliente(self, socket_cliente, nombre_usuario):
        """
        Elimina a un cliente del registro y notifica a los demás sobre su partida.
        """
        with self.lock_clientes:
            # Comprobamos si el cliente todavía existe antes de intentar eliminarlo.
            if socket_cliente in self.clientes:
                del self.clientes[socket_cliente]
                try:
                    socket_cliente.close()
                except:
                    pass # Ignoramos errores al cerrar, puede que ya esté cerrado.
        
        if nombre_usuario:
            logging.info(f'{nombre_usuario} ha abandonado el chat.')
            # Notificamos a los clientes restantes que el usuario se ha ido.
            self.broadcast({"type": "leave", "username": nombre_usuario}, socket_cliente)
            
            