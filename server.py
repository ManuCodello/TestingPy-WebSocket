# server.py

import socket
import threading
import logging
from protocol import Protocolo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Servidor:
    def __init__(self, host='127.0.0.1', port=55555, test_hooks=None):
        """
        Initializes the server.
        Args:
            test_hooks (dict, optional): A dictionary for passing synchronization events for tests.
        """
        self.host = host
        self.port = port
        self.socket_servidor = None
        self.clientes = {}
        self.lock_clientes = threading.Lock()
        self.activo = False
        self.hilo_principal = None
        # --- Hooks for synchronization in tests ---
        self.test_hooks = test_hooks or {}

    def iniciar(self):
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_servidor.bind((self.host, self.port))
        self.socket_servidor.listen(5)
        logging.info(f'Servidor escuchando en {self.host}:{self.port}')
        self.activo = True
        self.hilo_principal = threading.Thread(target=self._bucle_aceptacion)
        self.hilo_principal.start()

    def detener(self):
        self.activo = False
        if self.socket_servidor:
            try:
                # This is a more graceful shutdown
                self.socket_servidor.shutdown(socket.SHUT_RDWR)
                self.socket_servidor.close()
            except OSError:
                pass # Socket may already be closed
        if self.hilo_principal:
            self.hilo_principal.join()
        logging.info("Servidor detenido.")

    def _bucle_aceptacion(self):
        while self.activo:
            try:
                socket_cliente, direccion = self.socket_servidor.accept()
                if not self.activo: 
                    break
                logging.info(f'Conexión aceptada desde {direccion}')
                hilo_cliente = threading.Thread(
                    target=self._manejar_cliente,
                    args=(socket_cliente,),
                    daemon=True
                )
                hilo_cliente.start()
            except OSError:
                if self.activo:
                    logging.error("Error en el socket del servidor.")
                break

    def _manejar_cliente(self, socket_cliente):
        nombre_usuario = None
        try:
            Protocolo.enviar(socket_cliente, {"type": "username_request"})
            respuesta = Protocolo.recibir(socket_cliente)
            if not respuesta or "username" not in respuesta: 
                return
            nombre_usuario = respuesta["username"].strip()
            if not nombre_usuario: 
                return

            with self.lock_clientes:
                self.clientes[socket_cliente] = nombre_usuario

            # --- Trigger the "client joined" hook for tests ---
            if 'on_client_joined' in self.test_hooks:
                self.test_hooks['on_client_joined'].set()

            logging.info(f'{nombre_usuario} se ha unido al chat.')
            self.broadcast({"type": "join", "username": nombre_usuario}, socket_cliente)

            while self.activo:
                mensaje = Protocolo.recibir(socket_cliente)
                if not mensaje: 
                    break
                if mensaje.get("type") == "message":
                    self.broadcast({
                        "type": "message",
                        "username": nombre_usuario,
                        "text": mensaje.get("text", "")
                    }, socket_cliente)
        except (ConnectionAbortedError, ConnectionResetError):
            logging.warning(f"Conexión cerrada abruptamente por {nombre_usuario or 'un cliente'}")
        except Exception:
            pass # Ignore other errors during shutdown/disconnect
        finally:
            self._eliminar_cliente(socket_cliente, nombre_usuario)

    def broadcast(self, mensaje, socket_emisor):
        if mensaje.get("type") == "message":
            if not mensaje.get("text", "").strip():
                return
        with self.lock_clientes:
            # Create a copy to avoid issues if the dictionary is modified during iteration
            for cliente in list(self.clientes.keys()):
                if cliente != socket_emisor:
                    try:
                        Protocolo.enviar(cliente, mensaje)
                    except Exception:
                        # If sending fails, we'll let the receive loop handle the removal
                        pass

    def _eliminar_cliente(self, socket_cliente, nombre_usuario):
        with self.lock_clientes:
            if socket_cliente in self.clientes:
                del self.clientes[socket_cliente]
                try:
                    socket_cliente.close()
                except:
                    pass
        
        if nombre_usuario:
            logging.info(f'{nombre_usuario} ha abandonado el chat.')
            # --- Trigger the "client left" hook for tests ---
            if 'on_client_left' in self.test_hooks:
                self.test_hooks['on_client_left'].set()

            self.broadcast({"type": "leave", "username": nombre_usuario}, socket_cliente)