# protocol.py

import json
import logging
import struct

"""
Este módulo define el protocolo de comunicación para el chat.
Se encarga de serializar (convertir a bytes) y deserializar (convertir de bytes)
los mensajes para que puedan ser enviados a través de la red de forma fiable.
"""

class Protocolo:
    """
    Protocolo simple para la comunicación:
    Cada mensaje se envía con un prefijo de 4 bytes que indica el tamaño del payload (contenido),
    seguido del payload en formato JSON.
    
    [ 4 bytes de tamaño ][ Payload en JSON codificado en UTF-8 ]
    """

    @staticmethod
    def enviar(sock, data):
        """
        Empaqueta los datos en JSON, calcula su tamaño, y los envía a través del socket.
        
        Args:
            sock (socket.socket): El socket a través del cual se enviará el mensaje.
            data (dict): Un diccionario con los datos a enviar.
        """
        try:
            # Convierte el diccionario de Python a una cadena JSON y luego a bytes.
            payload = json.dumps(data).encode('utf-8')
            
            # Empaqueta la longitud del payload en 4 bytes, en formato de red (!I).
            # '!': Orden de bytes de red (big-endian)
            # 'I': Entero sin signo de 4 bytes
            tamaño = struct.pack('!I', len(payload))
            
            # Envía el tamaño seguido del payload. sock.sendall se asegura de que se envíen todos los datos.
            sock.sendall(tamaño + payload)
            
        except Exception as e:
            logging.error(f"Error al enviar datos: {e}")
            # Relanzamos la excepción para que el código que llamó a esta función pueda manejarla.
            raise

    @staticmethod
    def recibir(sock):
        """
        Recibe un mensaje, leyendo primero el tamaño y luego el payload correspondiente.
        
        Args:
            sock (socket.socket): El socket desde el cual se recibirá el mensaje.
            
        Returns:
            dict: Un diccionario con los datos recibidos, o None si la conexión se cierra o hay un error.
        """
        try:
            # 1. Leer el prefijo de tamaño (4 bytes)
            datos_tamaño = sock.recv(4)
            if not datos_tamaño:
                # Si no se reciben datos, significa que el otro extremo cerró la conexión.
                return None
            
            # Desempaqueta los 4 bytes para obtener el tamaño del payload.
            tamaño = struct.unpack('!I', datos_tamaño)[0]
            
            # 2. Leer el payload completo
            payload = b""
            # Leemos datos del socket hasta haber recibido la cantidad de bytes que indica el tamaño.
            while len(payload) < tamaño:
                # Calculamos cuántos bytes faltan por recibir.
                chunk = sock.recv(tamaño - len(payload))
                if not chunk:
                    # La conexión se cerró inesperadamente antes de recibir el mensaje completo.
                    return None
                payload += chunk
            
            # Decodifica los bytes a una cadena JSON y luego la convierte a un diccionario de Python.
            return json.loads(payload.decode('utf-8'))
            
        except Exception as e:
            logging.error(f"Error al recibir datos: {e}")
            return None