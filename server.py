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
        #bandera para controlar el bucle principal 
        self.activo = False
        self.hilo_principal = None

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
        
        self.activo = True
        # --- CAMBIO: El bucle de aceptación ahora corre en su propio hilo ---
        self.hilo_principal = threading.Thread(target=self._bucle_aceptacion)
        self.hilo_principal.start()

    # Método para detener el servidor de forma controlada ---
    def detener(self):
        """
        Detiene el servidor de forma segura.
        """
        self.activo = False
        # Cierra el socket para desbloquear la llamada a `accept()` en el bucle.
        if self.socket_servidor:
            self.socket_servidor.close()
        # Espera a que el hilo principal termine.
        if self.hilo_principal:
            self.hilo_principal.join()
        logging.info("Servidor detenido.")

    def _bucle_aceptacion(self):
        """
        Bucle principal que acepta nuevas conexiones de clientes.
        Se ejecuta en un hilo separado.
        """
        # --- CAMBIO: El bucle ahora depende de la bandera `self.activo` ---
        while self.activo:
            try:
                socket_cliente, direccion = self.socket_servidor.accept()
                logging.info(f'Conexión aceptada desde {direccion}')
                
                hilo_cliente = threading.Thread(
                    target=self._manejar_cliente,
                    args=(socket_cliente,),
                    daemon=True
                )
                hilo_cliente.start()
            except OSError:
                # Ocurre un error cuando cerramos el socket en `detener()`.
                # Es normal, simplemente salimos del bucle.
                if self.activo:
                    logging.error("Error en el socket del servidor.")
                break

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
            
        # -- ADD THIS NEW PRIVATE METHOD AFTER TDD REFACTOR --
    def _es_mensaje_valido(self, mensaje: dict) -> bool:
        """
        Valida un mensaje para ser transmitido.
        Un mensaje es válido si no está vacío y no excede el límite de longitud.
        """
        if mensaje.get("type") == "message":
            texto_mensaje = mensaje.get("text", "").strip()
            # A message is INVALID if it's empty OR too long.
            if not texto_mensaje or len(texto_mensaje) > 512:
                return False
        # For all other message types, or valid messages, return True.
        return True

    def broadcast(self, mensaje, socket_emisor):
        """
        Envía un mensaje a todos los clientes conectados, excepto al que lo envió.
        """
        # # --- START MODIFICATION ---

        # # 1. Validate the message before sending
        # # This is where we add our new logic to satisfy the test.
        # if mensaje.get("type") == "message":
        #     texto_mensaje = mensaje.get("text", "").strip()
        #     # Check for empty message OR a message that is too long.
        #     if not texto_mensaje or len(texto_mensaje) > 512:
        #         # If invalid, simply stop and do not send anything.
        #         return

        # # --- END MODIFICATION ---
        
                # --- TDD REFACTOR: Replace the old logic with a call to the new method ---
        if not self._es_mensaje_valido(mensaje):
            return # Stop if the message is invalid
        
        with self.lock_clientes:
            for cliente in list(self.clientes.keys()):
                if cliente != socket_emisor:
                    try:
                        Protocolo.enviar(cliente, mensaje)
                    except Exception:
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