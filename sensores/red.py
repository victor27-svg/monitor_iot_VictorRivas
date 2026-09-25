"""
sensores/red.py
Trafico de red.
Cuidado con esta metrica: psutil.net_io_counters() NO devuelve una
velocidad, devuelve un contador acumulado desde que arranco el equipo.
Para obtener KB/s hay que restar la lectura anterior y dividir entre el
tiempo transcurrido. Es el mismo patron 'valor actual menos valor
anterior' que se usa para detectar flancos.
"""

import time
import psutil

ETIQUETA = "Red"
UNIDAD = "KB/s"
KB = 1024.0
MB = 1024.0 ** 2
# Estado anterior: sin el, no se puede calcular una velocidad.
_anterior = {"enviados": 0, "recibidos": 0, "marca": 0.0}
_iniciado = False

def disponible():
    try:
        return psutil.net_io_counters() is not None
    except Exception:
        return False

def _iniciar():
    global _iniciado
    c = psutil.net_io_counters()
    _anterior.update({"enviados": c.bytes_sent,
                      "recibidos": c.bytes_recv,
                      "marca": time.time()})
    _iniciado = True

def leer():
    global _iniciado
    if not _iniciado:
        try:
            _iniciar()
            return None
        except Exception:
            return None             # la primera vuelta no alcanza para una velocidad

    c = psutil.net_io_counters()
    ahora = time.time()
    transcurrido = ahora - _anterior["marca"]

    if transcurrido <= 0:
        return None

    subida = (c.bytes_sent - _anterior["enviados"]) / KB / transcurrido
    bajada = (c.bytes_recv - _anterior["recibidos"]) / KB / transcurrido

    _anterior.update({"enviados": c.bytes_sent,
                      "recibidos": c.bytes_recv,
                      "marca": ahora})

    total = subida + bajada
    # La barra se escala contra el doble del umbral de pico.
    import config
    tope = max(config.RED_PICO_KBS * 2, 1.0)

    stats = psutil.net_if_stats()
    
    # LABORATORIO - Lista de palabras clave de adaptadores que debemos ignorar
    ignorados = ["Loopback", "VMware", "Virtual", "vEthernet", "Bluetooth", "Ethernet 2"]
    
    # Solo es True si hay alguna interfaz encendida que NO sea virtual
    conectado = any(
        s.isup for n, s in stats.items() 
        if not any(ignorado in n for ignorado in ignorados)
    )

    return {
        "valor": round(total, 1),
        "unidad": UNIDAD,
        "porcentaje": min(100.0, total / tope * 100.0),
        "detalle": (f"sube {subida:.1f} | baja {bajada:.1f} KB/s | "
                    f"total {(c.bytes_sent + c.bytes_recv) / MB:.0f} MB"),
        "extra": {
            "subida_kbs": round(subida, 1),
            "bajada_kbs": round(bajada, 1),
            "conectado": conectado, # Nueva señal
        },
    }