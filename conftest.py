# conftest.py (en la raíz del proyecto)
import sys
from pathlib import Path

# Agrega la raíz al path de Python
sys.path.insert(0, str(Path(__file__).parent))