# client.py

import socket
import threading
import logging
from protocol import Protocolo # Importamos nuestra clase de protocolo

# Configuración básica de logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Cliente:
    def __init__(self, host='127.0.0.1', port=55555):
        """
        Inicializa el cliente.
        
        Args:
            host (str): La dirección IP del servidor al que se conectará.
            port (int): El puerto del servidor.
        """
        self.host = host
        self.port = port
        self.socket_cliente = None
        self.nombre_usuario = ""
        # Variable para controlar los bucles de los hilos.
        self.activo = True

    def iniciar(self):
        """
        Inicia la conexión del cliente con el servidor.
        """
        self.nombre_usuario = input("Introduce tu nombre de usuario: ").strip()
        
        try:
            # Crea el socket y se conecta al servidor.
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((self.host, self.port))
            logging.info("Conectado al servidor.")
            
            # Inicia un hilo para recibir mensajes del servidor.
            hilo_recepcion = threading.Thread(target=self._bucle_recibir, daemon=True)
            hilo_recepcion.start()
            
            # El hilo principal se encarga de leer la entrada del usuario.
            self._bucle_entrada()

        except ConnectionRefusedError:
            logging.error("No se pudo conectar al servidor. Asegúrate de que esté en ejecución.")
        finally:
            # Cuando el cliente termina, se asegura de cerrar el socket.
            self.activo = False
            if self.socket_cliente:
                self.socket_cliente.close()
            logging.info("Desconectado.")

    def _bucle_recibir(self):
        """
        Bucle que se ejecuta en un hilo para recibir y procesar mensajes del servidor.
        """
        while self.activo:
            try:
                mensaje = Protocolo.recibir(self.socket_cliente)
                if not mensaje:
                    # Si no hay mensaje, el servidor cerró la conexión.
                    print(">>> El servidor se ha desconectado.")
                    break
                
                # Procesamos el mensaje según su tipo.
                tipo_mensaje = mensaje.get("type")
                
                if tipo_mensaje == "username_request":
                    # El servidor pide nuestro nombre de usuario.
                    Protocolo.enviar(self.socket_cliente, {"username": self.nombre_usuario})
                
                elif tipo_mensaje == "message":
                    print(f"{mensaje.get('username')}: {mensaje.get('text')}")
                
                elif tipo_mensaje == "join":
                    print(f">>> {mensaje.get('username')} se ha unido al chat.")
                
                elif tipo_mensaje == "leave":
                    print(f">>> {mensaje.get('username')} ha abandonado el chat.")

            except Exception as e:
                # Si el cliente sigue activo, mostramos el error. Si no, es normal que falle al cerrar.
                if self.activo:
                    logging.error(f"Error al recibir mensaje: {e}")
                break
        
        # Si salimos del bucle, detenemos al cliente.
        self.activo = False

    def _bucle_entrada(self):
        """
        Bucle que se ejecuta en el hilo principal para leer la entrada del usuario y enviarla.
        """
        while self.activo:
            try:
                texto = input()
                if texto.strip() and self.activo:
                    # Si el usuario escribe algo, lo enviamos como un mensaje.
                    Protocolo.enviar(self.socket_cliente, {
                        "type": "message",
                        "text": texto
                    })
            except (EOFError, KeyboardInterrupt):
                # El usuario presionó Ctrl+D o Ctrl+C para salir.
                print("\nCerrando cliente...")
                break
            except Exception as e:
                logging.error(f"Error al enviar mensaje: {e}")
                break
        
        # Si salimos del bule, detenemos al cliente.
        self.activo = False