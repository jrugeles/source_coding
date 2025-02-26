import machine
import utime

# Configuración del ADC (GP26)
adc = machine.ADC(26)
conversion_factor = 3.3 / 65535  # Factor para convertir la lectura a voltaje

# Parámetros de muestreo
sample_interval = 0.001  # Intervalo entre muestras en segundos (e.g., 0.001 = 1 ms -> 1000 muestras/s)
num_samples = 10000     # Número total de muestras a recolectar

# Archivo para guardar datos: cada línea tendrá "Tiempo(ms)  Voltaje(V)"
filename = "datos.txt"

with open(filename, "w") as f:
    f.write("Tiempo_ms\tVoltaje_V\n")  # Escribimos la cabecera
    start = utime.ticks_ms()  # Marca de tiempo inicial
    for i in range(num_samples):
        # Calcula el tiempo transcurrido (en ms) desde el inicio
        t = utime.ticks_diff(utime.ticks_ms(), start)
        # Lectura del ADC y conversión a voltaje
        reading = adc.read_u16()
        voltage = reading * conversion_factor
        # Escribe los datos: tiempo y voltaje, separados por tabulación
        f.write("{}\t{:.5f}\n".format(t, voltage))
        utime.sleep(sample_interval)

print("Datos guardados en:", filename)
