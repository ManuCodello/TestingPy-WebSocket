# tests/test_server.py

from unittest.mock import Mock, patch
import sys
import os
# This path adjustment is necessary for pytest to find your modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server import Servidor
from protocol import Protocolo


def test_broadcast_no_retransmite_mensajes_vacios():
	"""
	Prueba que los mensajes vacíos o con solo espacios no se envían a otros clientes.
	"""
	# 1. Preparación (Arrange)
	servidor = Servidor()

	mock_cliente_emisor = Mock()
	mock_cliente_receptor = Mock()

	servidor.clientes = {
		mock_cliente_emisor: "UsuarioEmisor",
		mock_cliente_receptor: "UsuarioReceptor"
	}

	mensaje_vacio = {
		"type": "message",
		"username": "UsuarioEmisor",
		"text": "    "
	}

	# 2. Actuación (Act)
	# We use 'patch' to temporarily replace Protocolo.enviar with a mock
	with patch('protocol.Protocolo.enviar') as mock_enviar:
		servidor.broadcast(mensaje_vacio, mock_cliente_emisor)

		# 3. Aserción (Assert)
		# Verificamos que Protocolo.enviar NUNCA fue llamado.
		mock_enviar.assert_not_called()


# -- ADD THIS NEW TEST --
def test_broadcast_no_retransmite_mensajes_demasiado_largos():
	"""
	RED: Prueba que los mensajes que exceden el límite de caracteres son ignorados.
	"""
	# 1. Arrange: Set up the scenario
	servidor = Servidor()
	mock_cliente_emisor = Mock()
	mock_cliente_receptor = Mock()
	servidor.clientes = {
		mock_cliente_emisor: "Emisor",
		mock_cliente_receptor: "Receptor"
	}

	# Create a message that is intentionally too long
	mensaje_largo = {
		"type": "message",
		"username": "Emisor",
		"text": "a" * 513  # 1 character over the 512 limit
	}

	# 2. Act: Call the method under test
	# We use patch from unittest.mock. It's the modern, preferred way to mock.
	# It ensures the mock is only active within this block.
	with patch('protocol.Protocolo.enviar') as mock_enviar:
		servidor.broadcast(mensaje_largo, mock_cliente_emisor)

		# 3. Assert: Verify the outcome
		# The server should NOT have called the send method.
		mock_enviar.assert_not_called()