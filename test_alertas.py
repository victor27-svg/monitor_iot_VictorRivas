# PRUEBAS UNITARIAS
import os
import unittest
from unittest.mock import patch
import config
from alertas import reproductor
from eventos import detectores, manejadores


def lectura_red(conectado, valor=0.0):  # LABORATORIO
    return {"valor": valor, "extra": {"conectado": conectado}}


def nombres(eventos):  # LABORATORIO
    return [nombre for nombre, _ in eventos]


class TestAlertas(unittest.TestCase):
    def setUp(self):
        reproductor._cola.clear()
        detectores._estado["nombres"] = set()
        detectores._estado["procesos_pesados"] = set()
        # LABORATORIO: cada prueba parte de una red sin historial y con sonido activo
        detectores._estado["conexion"] = None
        detectores._estado["caida_desde"] = None
        detectores._estado["ultimo_aviso_red"] = None
        detectores._estado["alarma"].pop("red", None)
        silencio = config.MODO_SILENCIOSO
        config.MODO_SILENCIOSO = False
        self.addCleanup(setattr, config, "MODO_SILENCIOSO", silencio)

    def test_modo_silencioso(self):
        config.MODO_SILENCIOSO = True
        reproductor.encolar("dummy.wav")
        self.assertEqual(len(reproductor._cola), 0, "No debe encolar si esta en silecion")

    def test_encolado_activo(self):
        config.MODO_SILENCIOSO = False
        reproductor.encolar("dummy.wav")
        self.assertEqual(len(reproductor._cola), 1, "Debe agregar 1 elemento a la cola")

    def test_alerta_usa_archivo_real(self):
        config.MODO_SILENCIOSO = False
        reproductor._cola.clear()
        reproductor.encolar(config.SONIDO_CPU)  # LABORATORIO
        self.assertTrue(len(reproductor._cola) == 1)
        self.assertTrue(os.path.exists(reproductor._cola[0]))

    def test_proceso_pesado_encola_alerta(self):
        config.MODO_SILENCIOSO = False
        reproductor._cola.clear()
        lectura = {
            "extra": {
                "nombres": ["python"],
                "top": [{"pid": 123, "nombre": "python", "cpu": 90.0, "ram": 50.0}],
            }
        }
        primero = detectores.detectar("procesos", lectura)
        self.assertEqual(len(primero), 1)
        manejadores.proceso_pesado(primero[0][1])
        self.assertEqual(len(reproductor._cola), 1)

        segundo = detectores.detectar("procesos", lectura)
        self.assertEqual(segundo, [])
        self.assertEqual(len(reproductor._cola), 1)

    # ------------------------------------------------------------------
    # LABORATORIO: eventos de conexion de red
    # ------------------------------------------------------------------
    def test_red_desconectada_por_flanco(self):
        self.assertEqual(nombres(detectores.detectar("red", lectura_red(True))), [])
        self.assertEqual(nombres(detectores.detectar("red", lectura_red(False))),
                         ["red_desconectada"])
        # Sigue caida en la lectura siguiente: NO repite (es flanco, no nivel)
        self.assertEqual(nombres(detectores.detectar("red", lectura_red(False))), [])

    def test_red_conectada_al_recuperarse(self):
        detectores.detectar("red", lectura_red(True))
        detectores.detectar("red", lectura_red(False))
        eventos = detectores.detectar("red", lectura_red(True))
        self.assertEqual(nombres(eventos), ["red_conectada"])
        self.assertEqual(nombres(detectores.detectar("red", lectura_red(True))), [])

    def test_recordatorio_por_tiempo(self):
        with patch.object(detectores, "time") as reloj:
            reloj.time.return_value = 1000.0
            detectores.detectar("red", lectura_red(True))
            detectores.detectar("red", lectura_red(False))

            reloj.time.return_value = 1000.0 + config.TIEMPO_RECORDATORIO_RED / 2
            self.assertEqual(nombres(detectores.detectar("red", lectura_red(False))), [],
                             "Antes de cumplirse el tiempo no debe recordar")

            reloj.time.return_value = 1000.0 + config.TIEMPO_RECORDATORIO_RED
            self.assertEqual(nombres(detectores.detectar("red", lectura_red(False))),
                             ["red_sigue_desconectada"])
            # Justo despues, el reloj se reinicia y no vuelve a sonar
            self.assertEqual(nombres(detectores.detectar("red", lectura_red(False))), [])

    def test_trafico_sigue_funcionando(self):
        # Agregar la conexion no debe romper el evento por umbral de trafico
        eventos = detectores.detectar("red", lectura_red(True, valor=config.RED_PICO_KBS + 1))
        self.assertEqual(nombres(eventos), ["red_pico"])

    def test_manejadores_red_devuelven_nivel_y_mensaje(self):
        # Antes red_desconectada devolvia solo "FALLA" y el despachador fallaba al desempaquetar
        for manejador, dato in ((manejadores.red_desconectada, {}),
                                (manejadores.red_sigue_desconectada, {"segundos": 30}),
                                (manejadores.red_conectada, {"segundos": 30})):
            nivel, mensaje = manejador(dato)
            self.assertIn(nivel, ("INFO", "AVISO", "ALERTA", "FALLA"))
            self.assertTrue(mensaje)

    # ------------------------------------------------------------------
    # LABORATORIO: un sonido distinto por tipo de problema
    # ------------------------------------------------------------------
    def test_cada_problema_encola_su_sonido(self):
        casos = (
            (manejadores.cpu_alta, {"valor": 90, "umbral": 70}, config.SONIDO_CPU),
            (manejadores.ram_alta, {"valor": 90}, config.SONIDO_MEMORIA),
            (manejadores.red_pico, {"valor": 900}, config.SONIDO_RED_TRAFICO),
            (manejadores.red_desconectada, {}, config.SONIDO_RED_DESCONECTADA),
            (manejadores.red_sigue_desconectada, {"segundos": 30}, config.SONIDO_RED_RECORDATORIO),
            (manejadores.red_conectada, {"segundos": 30}, config.SONIDO_RED_CONECTADA),
        )
        for manejador, dato, sonido in casos:
            reproductor._cola.clear()
            manejador(dato)
            self.assertEqual(len(reproductor._cola), 1, manejador.__name__)
            self.assertEqual(os.path.basename(reproductor._cola[0]), os.path.basename(sonido),
                             manejador.__name__)

    def test_sonidos_distintos_y_existentes(self):
        sonidos = [config.SONIDO_CPU, config.SONIDO_MEMORIA, config.SONIDO_RED_TRAFICO,
                   config.SONIDO_RED_DESCONECTADA, config.SONIDO_RED_CONECTADA,
                   config.SONIDO_RED_RECORDATORIO]
        self.assertEqual(len(set(sonidos)), len(sonidos), "Dos problemas comparten sonido")
        for s in sonidos:
            self.assertTrue(os.path.exists(reproductor._resolver_ruta(s)), s)

    # ------------------------------------------------------------------
    # LABORATORIO: la cola no bloquea y respeta la duracion de cada sonido
    # ------------------------------------------------------------------
    def test_no_repite_el_mismo_aviso_en_cola(self):
        reproductor.encolar(config.SONIDO_CPU)
        reproductor.encolar(config.SONIDO_CPU)
        self.assertEqual(len(reproductor._cola), 1)

    def test_procesar_no_bloquea_y_espera_la_duracion_del_sonido(self):
        reproducidos = []
        reproductor.encolar(config.SONIDO_MEMORIA)
        reproductor.encolar(config.SONIDO_CPU)
        duracion = reproductor._duracion(reproductor._resolver_ruta(config.SONIDO_MEMORIA))

        with patch.object(reproductor, "_reproducir", reproducidos.append), \
             patch.object(reproductor, "time") as reloj:
            reloj.time.return_value = 5000.0
            reproductor._bloqueado_hasta = 0.0
            reproductor.procesar()                       # arranca el primero
            self.assertEqual(len(reproducidos), 1)
            self.assertEqual(len(reproductor._cola), 1)  # el segundo espera, sin bloquear

            reloj.time.return_value = 5000.0 + duracion / 2
            reproductor.procesar()                       # aun suena el primero
            self.assertEqual(len(reproducidos), 1)

            reloj.time.return_value = 5000.0 + duracion + config.PAUSA_ENTRE_SONIDOS
            reproductor.procesar()                       # ya termino: turno del segundo
            self.assertEqual(len(reproducidos), 2)
            self.assertEqual(len(reproductor._cola), 0)


if __name__ == '__main__':
    unittest.main()
