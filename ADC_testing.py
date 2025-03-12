# Programa de pruebas conversion de la fuente
# Curso de comunicaciones Digitales
# Ingeniería en Telecomunicaciones
# UMNG - José Rugeles

from machine import ADC, Pin
import utime
import array
import math
import cmath

# Configuración inicial
adc = ADC(Pin(27))
N = 512
N_FFT = 1024
f_muestreo = 2000  # Frecuencia objetivo de muestreo (Hz)
dt_us = int(1_000_000 / f_muestreo)
data = array.array('H', [0] * N)

# Adquisición de datos con tiempos uniformes
def acquire_data():
    tiempos = []
    muestras = []
    start = utime.ticks_us()

    for i in range(N):
        t_actual = utime.ticks_diff(utime.ticks_us(), start) / 1_000_000
        tiempos.append(t_actual)
        muestras.append(adc.read_u16())
        utime.sleep_us(dt_us)

    elapsed_time = tiempos[-1]
    fs_real = N / elapsed_time
    print(f"Frecuencia deseada: {f_muestreo} Hz, frecuencia real: {fs_real:.2f} Hz")

    # Guardar muestras en archivo
    with open("muestras.txt", "w") as f:
        f.write("Tiempo(s)\tVoltaje(V)\n")
        voltajes = [(x / 65535) * 3.3 for x in muestras]
        for t, v in zip(tiempos, voltajes):
            f.write(f"{t:.6f}\t{v:.5f}\n")

    return muestras, fs_real

# Convertir datos a voltaje y eliminar offset DC
def convert_to_voltage(data, VREF=3.3):
    return [(x / 65535) * VREF for x in data]

def remove_offset(data):
    avg_dc = sum(data) / len(data)
    print(f"Offset DC removido: {avg_dc:.3f} V")
    return [d - avg_dc for d in data]

# Aplicar ventana Hanning
def apply_hanning_window(data):
    N = len(data)
    window = [0.5 * (1 - math.cos(2 * math.pi * i / (N - 1))) for i in range(N)]
    return [d * w for d, w in zip(data, window)]

# FFT manual (Radix-2)
def fft_manual(x, N_FFT):
    def bit_reversal(n, logN):
        rev = 0
        for i in range(logN):
            if (n >> i) & 1:
                rev |= 1 << (logN - 1 - i)
        return rev

    X = [complex(v, 0) for v in x[:N_FFT]] + [0]*(N_FFT - len(x))
    logN = int(math.log2(N_FFT))

    for i in range(N_FFT):
        j = bit_reversal(i, logN)
        if j > i:
            X[i], X[j] = X[j], X[i]

    for s in range(logN):
        m = 2 ** (s + 1)
        half_m = m // 2
        w_m = cmath.exp(-2j * math.pi / m)
        for k in range(0, N_FFT, m):
            w = 1
            for j in range(half_m):
                t = w * X[k + j + half_m]
                u = X[k + j]
                X[k + j] = u + t
                X[k + j + half_m] = u - t
                w *= w_m
    return X

# Análisis FFT
def analyze_fft(fft_result, fs_real, N_FFT):
    magnitudes = [abs(c) / (N_FFT / 2) for c in fft_result[:N_FFT // 2]]
    frequencies = [i * fs_real / N_FFT for i in range(N_FFT // 2)]

    max_index = magnitudes.index(max(magnitudes[1:]))
    dominant_freq = frequencies[max_index]
    signal_amplitude = magnitudes[max_index]

    noise_magnitudes = magnitudes[:]
    noise_magnitudes[max_index] = 0
    noise_floor_v = sum(noise_magnitudes) / (N_FFT // 2 - 1)
    noise_floor_db = 20 * math.log10(noise_floor_v / 3.3)
    SNR = 20 * math.log10(signal_amplitude / noise_floor_v)
    ENOB = (SNR - 1.76) / 6.02

    print(f"Frecuencia dominante: {dominant_freq:.2f} Hz")
    print(f"Amplitud señal: {signal_amplitude:.3f} V")
    print(f"Piso de ruido: {noise_floor_v:.5f} V ({noise_floor_db:.2f} dB FS)")
    print(f"SNR: {SNR:.2f} dB, ENOB: {ENOB:.2f} bits")

    # Guardar FFT en archivo
    with open("fft.txt", "w") as f:
        f.write("Frecuencia(Hz)\tMagnitud(V)\n")
        for freq, mag in zip(frequencies, magnitudes):
            f.write(f"{freq:.2f}\t{mag:.5f}\n")

    return frequencies, magnitudes

# Programa principal
def main():
    print("Iniciando adquisición y análisis...")
    muestras, fs_real = acquire_data()
    voltajes = convert_to_voltage(muestras)
    voltajes_sin_offset = remove_offset(voltajes)
    senal_ventaneada = apply_hanning_window(voltajes_sin_offset)

    fft_result = fft_manual(senal_ventaneada, N_FFT)
    analyze_fft(fft_result, fs_real, N_FFT)

if __name__ == "__main__":
    main()
