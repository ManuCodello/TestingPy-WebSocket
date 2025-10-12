# main.py

import sys
from server import Servidor
from client import Cliente

if __name__ == "__main__":
    # Revisa los argumentos pasados por la línea de comandos.
    # sys.argv es una lista que contiene el nombre del script y los argumentos.
    # Ejemplo: python main.py server
    
    # Si se pasa "server" como argumento, o si no se pasa ninguno (para facilitar)
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Crea una instancia del servidor y lo inicia.
        servidor = Servidor()
        servidor.iniciar()
    # Si se pasa "client" como argumento
    elif len(sys.argv) > 1 and sys.argv[1] == "client":
        # Crea una instancia del cliente y lo inicia.
        cliente = Cliente()
        cliente.iniciar()
    # Si no se especifica un argumento válido
    else:
        print("Uso: python main.py [server|client]")