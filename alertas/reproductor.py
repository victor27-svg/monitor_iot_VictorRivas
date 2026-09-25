# MODULO DE REPRODUCCION MEDIANTE COLA Y MARCAS DE TIEMPO

import os
import sys  # LABORATORIO
import time
import wave  # LABORATORIO
from collections import deque
import config

if os.name == "nt":  # LABORATORIO
    import winsound

_cola = deque(maxlen=config.MAX_COLA_SONIDOS)  # LABORATORIO: tope para no acumular alertas viejas
_bloqueado_hasta = time.time()  # LABORATORIO: instante hasta el que hay un sonido sonando


def _resolver_ruta(archivo_sonido):
    """Devuelve la ruta absoluta del archivo de sonido desde la raiz del proyecto."""
    if not archivo_sonido:
        return ""
    if os.path.isabs(archivo_sonido):
        return archivo_sonido

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base, archivo_sonido)
    if not os.path.exists(ruta):
        ruta = os.path.join(base, "alertas", archivo_sonido)
    return ruta if os.path.exists(ruta) else archivo_sonido


def _duracion(ruta):  # LABORATORIO
    """Duracion real del .wav en segundos. Si no se puede leer, usa la de config."""
    try:
        with wave.open(ruta, "rb") as w:
            return w.getnframes() / w.getframerate()
    except (wave.Error, EOFError, OSError):
        return config.DURACION_SONIDO


def _reproducir(ruta):  # LABORATORIO
    """Lanza el sonido y regresa al instante: SND_ASYNC no espera a que termine."""
    if os.name == "nt":
        try:
            winsound.PlaySound(ruta, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except RuntimeError:
            winsound.MessageBeep()
    else:
        sys.stdout.write("\a")   # campana del sistema (macOS / Linux)
        sys.stdout.flush()


def encolar(archivo_sonido):
    """Sonido a la cola si el modo silencioso esta apagado."""
    if config.MODO_SILENCIOSO or not archivo_sonido:
        return
    ruta = _resolver_ruta(archivo_sonido)  # LABORATORIO
    if ruta in _cola:  # LABORATORIO: si ese mismo aviso ya espera turno, no se repite
        return
    _cola.append(ruta)


def procesar():
    """Se ejecuta en cada ciclo del nucleo. Extrae y reproduce si es el momento"""
    global _bloqueado_hasta
    ahora = time.time()

    if _cola and ahora >= _bloqueado_hasta:
        sonido = _cola.popleft()
        if os.path.exists(sonido):
            _reproducir(sonido)  # LABORATORIO
            # LABORATORIO: el turno siguiente espera lo que dura ESTE archivo (mas una pausa)
            _bloqueado_hasta = ahora + _duracion(sonido) + config.PAUSA_ENTRE_SONIDOS
