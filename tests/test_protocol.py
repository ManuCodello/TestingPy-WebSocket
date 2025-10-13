# tests/test_protocol.py

import json
import struct
from unittest.mock import Mock # Nuestra herramienta para simular objetos

# Importamos la clase que queremos probar.
# Necesitamos ajustar el path para que Python encuentre nuestros módulos.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from protocol import Protocolo

# --- Pruebas para Protocolo.enviar ---

def test_enviar_serializa_y_empaqueta_correctamente():
    """
    PRUEBA POSITIVA (Happy Path):
    Verifica que el método 'enviar' construye el mensaje correctamente:
    4 bytes de tamaño + payload en JSON.
    """
    # 1. Preparación (Arrange)
    # Creamos un 'Mock' que simula ser un socket.
    # Los Mocks registran cómo son utilizados, para que podamos verificarlo.
    mock_socket = Mock()
    
    # Los datos que queremos enviar.
    datos_a_enviar = {"type": "message", "text": "hola"}
    
    # Calculamos el resultado esperado.
    payload_esperado = json.dumps(datos_a_enviar).encode('utf-8')
    tamaño_esperado = struct.pack('!I', len(payload_esperado))
    mensaje_completo_esperado = tamaño_esperado + payload_esperado

    # 2. Actuación (Act)
    # Llamamos a la función que estamos probando.
    Protocolo.enviar(mock_socket, datos_a_enviar)

    # 3. Aserción (Assert)
    # Verificamos que el método 'sendall' del socket fue llamado
    # exactamente una vez y con los datos que esperábamos.
    mock_socket.sendall.assert_called_once_with(mensaje_completo_esperado)

# --- Pruebas para Protocolo.recibir ---

def test_recibir_desempaqueta_y_deserializa_correctamente():
    """
    PRUEBA POSITIVA (Happy Path):
    Verifica que 'recibir' puede leer un mensaje empaquetado y devolver el diccionario correcto.
    """
    # 1. Preparación (Arrange)
    mock_socket = Mock()
    datos_originales = {"user": "test", "status": "ok"}
    
    # Construimos el flujo de bytes que simulará llegar por la red.
    payload = json.dumps(datos_originales).encode('utf-8')
    tamaño = struct.pack('!I', len(payload))
    
    # Configuramos nuestro mock: cuando se llame a `recv`, debe devolver
    # primero el tamaño y luego el payload. `side_effect` es perfecto para esto.
    mock_socket.recv.side_effect = [tamaño, payload]

    # 2. Actuación (Act)
    datos_recibidos = Protocolo.recibir(mock_socket)

    # 3. Aserción (Assert)
    # Verificamos que los datos que obtuvimos son los que enviamos originalmente.
    assert datos_recibidos == datos_originales

def test_recibir_devuelve_none_si_el_socket_se_cierra():
    """
    PRUEBA NEGATIVA:
    Verifica que la función maneja correctamente el caso en que la conexión
    se cierra (recv devuelve bytes vacíos).
    """
    # 1. Preparación
    mock_socket = Mock()
    # Simulamos que el socket se cierra inmediatamente.
    mock_socket.recv.return_value = b''

    # 2. Actuación
    resultado = Protocolo.recibir(mock_socket)

    # 3. Aserción
    # Esperamos que la función devuelva None para indicar una desconexión.
    assert resultado is None
