import sys

def revisar_entorno():
    """Comprueba que todo lo necesario este instalado."""
    print("Revision del entorno")
    print("-" * 40)
    try:
        import psutil
        print(f" psutil       OK (version {psutil.__version__})")
    except ImportError:
        print(" psutil       FALTA -> pip install psutil")
        return False
        
    try:
        import tkinter
        print(f" tkinter      OK (Tk {tkinter.TkVersion})")
    except ImportError:
        print(" tkinter      FALTA -> use: python main.py --consola")
        
    import sensores
    activos = sensores.disponibles()
    print("-" * 40)
    for clave, modulo in sensores.LECTORES.items():
        estado = "disponible" if clave in activos else "NO disponible"
        print(f" {modulo.ETIQUETA:<14} {estado}")
    print("-" * 40)
    print("La bateria aparece como NO disponible en computadoras de")
    print("escritorio. No es un error: es un sensor ausente y el")
    print("programa lo maneja como tal.")
    return True

def main():
    if "--revisar" in sys.argv:
        revisar_entorno()
        return
        
    if "--consola" in sys.argv:
        from dashboard import consola
        consola.iniciar()
        return
        
    try:
        from dashboard import ventana
    except ImportError:
        print("tkinter no esta disponible en este equipo.")
        print("Se inicia el dashboard de consola.")
        from dashboard import consola
        consola.iniciar()
        return
        
    ventana.iniciar()

if __name__ == "__main__":
    main()