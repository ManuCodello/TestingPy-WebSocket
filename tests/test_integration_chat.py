# tests/test_integration_chat.py

import pytest
import socket
import threading
import time
from queue import Queue, Empty

# We need to adjust the path so pytest can find our application code
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import Servidor
from protocol import Protocolo

# A helper class to run a client in a separate thread.
# This is CRUCIAL for testing a server without blocking the main test thread.
class TestClient:
    """
    Un cliente de ayuda que encapsula la comunicaciÃ³n de red en un hilo separado,
    evitando que el hilo principal de la prueba se bloquee.
    """
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.mensajes = Queue() # A thread-safe queue to store received messages
        self.activo = True
        self.hilo_escucha = threading.Thread(target=self._escuchar, daemon=True)
        self.hilo_escucha.start()

    def _escuchar(self):
        """
        Bucle que se ejecuta en segundo plano, escuchando constantemente
        y guardando los mensajes en la cola.
        """
        while self.activo:
            try:
                msg = Protocolo.recibir(self.sock)
                if msg:
                    self.mensajes.put(msg)
                else:
                    break # Connection closed
            except Exception:
                if self.activo:
                    print("Client listening loop error")
                break

    def enviar(self, data):
        Protocolo.enviar(self.sock, data)

    def enviar_texto(self, texto):
        self.enviar({"type": "message", "text": texto})

    def obtener_mensaje(self, timeout=1.0):
        """
        Recupera un mensaje de la cola, esperando como mÃ¡ximo el timeout.
        Devuelve None si no llega ningÃºn mensaje.
        """
        try:
            return self.mensajes.get(timeout=timeout)
        except Empty:
            return None

    def cerrar(self):
        self.activo = False
        self.sock.close()
        self.hilo_escucha.join()

@pytest.fixture
def servidor_activo():
    """
    Esta fixture inicia el servidor antes de cada prueba y se asegura
    de detenerlo despuÃ©s, incluso si la prueba falla.
    """
    servidor = Servidor('127.0.0.1', 55555)
    servidor.iniciar()
    # Wait a moment for the server thread to start listening
    time.sleep(0.1)

    # 'yield' passes control to the test function
    yield servidor.host, servidor.port

    # This code runs after the test is complete
    servidor.detener()


def test_multiples_conexiones_y_broadcast(servidor_activo):
    """
    Verifica que mÃºltiples clientes pueden conectarse y que un mensaje
    enviado por uno es recibido por el otro.
    """
    host, port = servidor_activo
    alice = TestClient(host, port)
    bob = TestClient(host, port)

    # Alice authenticates
    assert alice.obtener_mensaje().get("type") == "username_request"
    alice.enviar({"username": "Alice"})

    # Bob authenticates
    assert bob.obtener_mensaje().get("type") == "username_request"
    bob.enviar({"username": "Bob"})

    # Verify Alice gets join notification for Bob
    msg_join_bob = alice.obtener_mensaje()
    assert msg_join_bob.get("type") == "join" and "Bob" in msg_join_bob.get("username")

    # Alice sends a message
    alice.enviar_texto("Hola a todos!")

    # Verify Bob receives the message from Alice
    mensaje_recibido = bob.obtener_mensaje()
    assert mensaje_recibido is not None, "Bob no recibiÃ³ el mensaje de Alice a tiempo."
    assert mensaje_recibido.get("username") == "Alice"
    assert mensaje_recibido.get("text") == "Hola a todos!"

    # Cleanup
    alice.cerrar()
    bob.cerrar()


def test_manejo_de_desconexion_inesperada(servidor_activo):
    """
    Verifica que el servidor maneja la desconexiÃ³n abrupta de un cliente
    sin caerse y notifica correctamente a los demÃ¡s.
    """
    host, port = servidor_activo
    alice = TestClient(host, port)
    bob = TestClient(host, port)
    charlie = TestClient(host, port)

    # Authenticate all clients
    alice.obtener_mensaje()
    alice.enviar({"username": "Alice"})
    bob.obtener_mensaje()
    bob.enviar({"username": "Bob"})
    charlie.obtener_mensaje()
    charlie.enviar({"username": "Charlie"})

    # Clear initial join messages
    time.sleep(0.1)
    while alice.obtener_mensaje(timeout=0.01) is not None: 
        pass
    while bob.obtener_mensaje(timeout=0.01) is not None: 
        pass

    # Charlie disconnects abruptly
    charlie.cerrar()

    # Alice and Bob should receive a "leave" notification
    msg_leave_alice = alice.obtener_mensaje(timeout=1)
    msg_leave_bob = bob.obtener_mensaje(timeout=1)

    assert msg_leave_alice is not None, "Alice no recibiÃ³ la notificaciÃ³n de 'leave'."
    assert msg_leave_alice.get("type") == "leave" and msg_leave_alice.get("username") == "Charlie"

    assert msg_leave_bob is not None, "Bob no recibiÃ³ la notificaciÃ³n de 'leave'."
    assert msg_leave_bob.get("type") == "leave" and msg_leave_bob.get("username") == "Charlie"

    # Alice sends a message to ensure the chat is still operational
    alice.enviar_texto("El chat sigue operativo")
    mensaje_final = bob.obtener_mensaje(timeout=1)

    assert mensaje_final is not None, "Bob no recibiÃ³ el mensaje final de Alice."
    assert mensaje_final.get("text") == "El chat sigue operativo"

    # Cleanup
    alice.cerrar()
    bob.cerrar()
    
    # -- ADD THIS NEW TEST TO THE END OF THE FILE --
def test_mensajes_no_se_pierden_ni_duplican_bajo_carga(servidor_activo):
    """
    Verifica la integridad de los mensajes bajo una carga rÃ¡pida.
    Esto prueba que la concurrencia del servidor es robusta y que no
    se pierden ni se desordenan los mensajes.
    """
    # 1. Arrange
    host, port = servidor_activo
    emisor = TestClient(host, port)
    receptor = TestClient(host, port)

    # Authenticate clients
    emisor.obtener_mensaje()
    emisor.enviar({"username": "Emisor"})
    receptor.obtener_mensaje()
    receptor.enviar({"username": "Receptor"})

    # Clear the join notifications from the queue to not interfere with the test
    time.sleep(0.1)
    while receptor.obtener_mensaje(timeout=0.01) is not None: 
        pass

    # 2. Act
    mensajes_enviados = []
    for i in range(50):
        texto = f"Mensaje nÃºmero {i}"
        emisor.enviar_texto(texto)
        mensajes_enviados.append(texto)

    # 3. Assert
    mensajes_recibidos = []
    # Try to receive all 50 messages
    for _ in range(50):
        msg = receptor.obtener_mensaje(timeout=2) # Use a generous timeout
        if msg and msg.get("type") == "message":
            mensajes_recibidos.append(msg.get("text"))

    # The final, critical assertion. The lists must be identical.
    assert mensajes_recibidos == mensajes_enviados

    # Cleanup
    emisor.cerrar()
    receptor.cerrar()
    
    # -- ADD THIS FINAL NEGATIVE CASE TEST --
def test_servidor_maneja_cliente_sin_autenticacion(servidor_activo):
    """
    â Œ CASO NEGATIVO: Un cliente se conecta pero nunca envÃ­a un nombre de usuario.
    POR QUÃ‰: El servidor no debe quedarse esperando para siempre. Debe desconectar
    al cliente silenciosamente sin afectar a los demÃ¡s.
    """
    # 1. Arrange
    host, port = servidor_activo
    cliente_bueno = TestClient(host, port)
    cliente_malo = TestClient(host, port) # This client will not authenticate

    # El cliente bueno se autentica y opera normalmente
    cliente_bueno.obtener_mensaje()
    cliente_bueno.enviar({"username": "ClienteBueno"})

    # El cliente malo recibe la peticiÃ³n de username, pero la ignora.
    msg_req = cliente_malo.obtener_mensaje()
    assert msg_req.get("type") == "username_request"

    # 2. Act
    # El cliente bueno envÃ­a un mensaje para confirmar que el chat funciona
    cliente_bueno.enviar_texto("Â¿Hay alguien ahÃ­?")

    # 3. Assert
    # El cliente bueno NO deberÃ­a recibir NADA. Ni su propio mensaje, ni
    # notificaciones del cliente malo. Usamos un timeout corto.
    mensaje_inesperado = cliente_bueno.obtener_mensaje(timeout=0.5)
    assert mensaje_inesperado is None, "El cliente bueno recibiÃ³ un mensaje inesperado."

    # Cleanup
    cliente_bueno.cerrar()
    cliente_malo.cerrar()


# python -m pytest --cov=server --cov=protocol --cov-report term-missing