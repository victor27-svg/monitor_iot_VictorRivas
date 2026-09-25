import os

# Identificación del nodo
NODO = "laptop-lab3"
UBICACION = "Laboratorio 3 - FISC"

# --------------------------------------------------------------------------
# Periodos de muestreo, en segundos.
# Cada metrica tiene el suyo: leer los procesos es caro, leer la CPU no.
# --------------------------------------------------------------------------

PERIODO_RAPIDO = 1.0        # cpu, memoria, red
PERIODO_LENTO = 5.0         # disco, procesos, bateria
PERIODO_REPORTE = 30.0      # resumen periodico hacia la bitacora

REFRESCO_MS = 200           # cada cuanto refresca el dashboard (milisegundos)

# --------------------------------------------------------------------------
# Umbrales. Dos valores por metrica: uno para entrar en alarma y otro,
# mas bajo, para salir de ella. Esa diferencia es la HISTERESIS y evita
# que una lectura oscilando en el limite genere decenas de eventos falsos.
# --------------------------------------------------------------------------

CPU_ALTO = 70.0
CPU_BAJO = 50.0
CPU_NUCLEO_SATURADO = 90.0      # un nucleo individual por encima de esto

RAM_ALTA = 60.0
RAM_BAJA = 50.0

DISCO_LLENO = 90.0             # porcentaje de ocupacion
DISCO_ALIVIADO = 85.0

RED_PICO_KBS = 500.0           # kilobytes por segundo
RED_CALMA_KBS = 200.0

BATERIA_BAJA = 20.0             # porcentaje de carga
BATERIA_RECUPERADA = 30.0

PROCESO_PESADO = 50.0             # porcentaje de CPU usado por un proceso

# Variacion brusca entre dos muestras consecutivas: evento de anomalia
SALTO_ANOMALO = 40.0

# --------------------------------------------------------------------------
# Ventana movil y almacenamiento
# --------------------------------------------------------------------------

VENTANA = 10
MAX_EVENTOS_LOG = 200
ARCHIVO_BITACORA = "bitacora.json"

# --------------------------------------------------------------------------
# Unidad de disco a vigilar. Se detecta sola segun el sistema operativo.
# --------------------------------------------------------------------------

UNIDAD_DISCO = "C:\\" if os.name == "nt" else "/"

# Cantida de procesos que se muestran en el raking
TOP_PROCESOS = 8

# Procesos del sistema que no vale la pena reportar: en Linux los
# 'kworker' y 'kthread' aparecen y desaparecen constantemente y llenarian
# la bitacora de ruido.
PROCESOS_IGNORADOS = ("kworker", "kthread", "ksoftirqd", "migration",
"rcu_", "irq/", "svchost")

# AÑADIDO DEL LABORATORIO 1 - ALERTAS DE SONIDOS
MODO_SILENCIOSO = False          # True durante la clase: no suena nada
DURACION_SONIDO = 2.0            # LABORATORIO: solo se usa si no se puede leer la duracion del .wav (s)
PAUSA_ENTRE_SONIDOS = 0.2        # LABORATORIO: silencio entre dos alertas seguidas (s)
MAX_COLA_SONIDOS = 5             # LABORATORIO: tope de alertas esperando turno
TIEMPO_RECORDATORIO_RED = 30.0   # cada cuanto se repite el aviso mientras siga sin red (s)

# LABORATORIO: un sonido distinto por tipo de problema
SONIDO_CPU = "sonidos/cpu.wav"                          # cpu_alta y proceso_pesado
SONIDO_MEMORIA = "sonidos/memoria.wav"                  # ram_alta
SONIDO_RED_TRAFICO = "sonidos/trafico.wav"              # red_pico
SONIDO_RED_DESCONECTADA = "sonidos/desconectada.wav"    # red_desconectada
SONIDO_RED_CONECTADA = "sonidos/conectada.wav"          # red_conectada
SONIDO_RED_RECORDATORIO = "sonidos/recordatorio.wav"    # red_sigue_desconectada
