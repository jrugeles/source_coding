import machine
import utime
import math

print("----------------------------------------------------")
print("Programa de muestreo y análisis estadístico")
print("----------------------------------------------------")

# Solicitar al usuario el nombre del archivo para las muestras
sample_filename = input("Ingrese el nombre del archivo para las muestras (ej. samples.txt): ")
# Solicitar al usuario el nombre del archivo para el histograma
hist_filename = input("Ingrese el nombre del archivo para el histograma (ej. histogram.txt): ")

print("Los datos de muestras se guardarán en: {}".format(sample_filename))
print("Los datos del histograma se guardarán en: {}".format(hist_filename))

# Configuración del ADC (por ejemplo, en GP26)
adc = machine.ADC(26)
conversion_factor = 3.3 / 65535  # Conversión de valor crudo a voltaje

# Parámetro: número de muestras a recolectar (único ciclo)
num_samples = 10000  # Ajustable según necesidades

# Crear el archivo de muestras y escribir la cabecera
with open(sample_filename, "w") as f:
    f.write("Tiempo_ms\tVoltaje_V\n")
print("Archivo de muestras '{}' creado.".format(sample_filename))

# Variables para el histograma (usando la resolución nativa de 12 bits)
val_hist = dict()

# Variables para el cálculo incremental (algoritmo de Welford) de media y varianza
n = 0
mean = 0.0
M2 = 0.0

# Contador de muestras y tiempo de inicio
cnt = 0
start = utime.ticks_ms()

# Buffer para acumular datos de muestras y escribir en bloque
write_buffer = ""
write_interval = 100  # Se escribe en el archivo cada 100 muestras

print("Comenzando recolección de {} muestras...".format(num_samples))

while cnt < num_samples:
    # Lectura del ADC (valor crudo de 16 bits)
    raw_val = adc.read_u16()
    
    # Calcular el voltaje a partir del valor crudo
    voltage = raw_val * conversion_factor

    # Calcular el tiempo transcurrido (en ms) desde el inicio del ciclo
    t = utime.ticks_diff(utime.ticks_ms(), start)
    
    # Acumular la muestra en el buffer (formato: tiempo_ms y voltaje_V)
    write_buffer += "{}\t{:.5f}\n".format(t, voltage)

    # Actualización incremental de estadísticas (algoritmo de Welford)
    n += 1
    delta = voltage - mean
    mean += delta / n
    delta2 = voltage - mean
    M2 += delta * delta2

    # Actualización del histograma (con resolución nativa de 12 bits)
    native_val = raw_val >> 4  # Conversión a 12 bits (0-4095)
    val_hist[native_val] = val_hist.get(native_val, 0) + 1
    
    cnt += 1

    # Escribir el buffer en el archivo cada 'write_interval' muestras
    if cnt % write_interval == 0:
        with open(sample_filename, "a") as f:
            f.write(write_buffer)
            f.flush()
        write_buffer = ""
    
    # Mostrar mensaje de progreso cada 1000 muestras
    if cnt % 1000 == 0:
        print("Se han recolectado {} muestras...".format(cnt))

# Escribir cualquier dato pendiente en el buffer
if write_buffer:
    with open(sample_filename, "a") as f:
        f.write(write_buffer)
        f.flush()

# Calcular la desviación estándar
variance = M2 / n if n > 1 else 0
std_dev = math.sqrt(variance)

print("----------------------------------------------------")
print("Ciclo de muestreo completado con {} muestras.".format(num_samples))
print("Estadísticas del ciclo:")
print("  Total de muestras: {}".format(n))
print("  Media: {:.5f} V".format(mean))
print("  Desviación Estándar: {:.5f} V".format(std_dev))
print("Histograma de lecturas (res. 12 bits):")
print(val_hist)

# Guardar el histograma en un archivo aparte
with open(hist_filename, "w") as f:
    f.write("Valor_ADC_12bits\tFrecuencia\n")
    # Ordenamos las claves para que el archivo tenga orden ascendente
    for key in sorted(val_hist.keys()):
        f.write("{}\t{}\n".format(key, val_hist[key]))
print("Datos del histograma guardados en '{}'".format(hist_filename))
print("Programa finalizado.")
