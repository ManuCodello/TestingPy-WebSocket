# tests/test_server.py

from unittest.mock import Mock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # añade el directorio raíz al path

from server import Servidor
from protocol import Protocolo


def test_broadcast_no_retransmite_mensajes_vacios():
    """
    Prueba que los mensajes vacíos o con solo espacios no se envían a otros clientes.
    """
    # 1. Preparación (Arrange)
    servidor = Servidor() # Creamos una instancia real del servidor
    
    # Creamos clientes simulados
    mock_cliente_emisor = Mock()
    mock_cliente_receptor = Mock()
    
    # Añadimos los clientes al estado interno del servidor
    servidor.clientes = {
        mock_cliente_emisor: "UsuarioEmisor",
        mock_cliente_receptor: "UsuarioReceptor"
    }
    
    # Mensaje que queremos probar
    mensaje_vacio = {
        "type": "message",
        "username": "UsuarioEmisor",
        "text": "    " # Un mensaje con solo espacios
    }

    # 2. Actuación (Act)
    # Sobrescribimos temporalmente Protocolo.enviar con un Mock para espiarlo
    Protocolo.enviar = Mock()
    
    servidor.broadcast(mensaje_vacio, mock_cliente_emisor)

    # 3. Aserción (Assert)
    # Verificamos que Protocolo.enviar NUNCA fue llamado.
    # Esto significa que el mensaje vacío fue ignorado, como queríamos.
    Protocolo.enviar.assert_not_called()
