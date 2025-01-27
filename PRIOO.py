import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import queue
import time
import random

# Lista inicial de procesos
procesos = []  # Almacena los procesos con sus atributos.
queue_tabla = queue.Queue()  # Cola para actualizar la tabla en la interfaz gráfica.
queue_grafico = queue.Queue()  # Cola para actualizar el gráfico de Gantt.
lock = threading.Lock()  # Lock para manejar acceso concurrente a la lista de procesos.

# Genera procesos aleatorios con atributos como tiempo de llegada, ráfaga y prioridad.
def generar_procesos():
    ids = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]  # Identificadores de procesos.
    tll_actual = 0  # Tiempo de llegada inicial.

    for i in range(len(ids)):
        with lock:  # Asegura acceso exclusivo a la lista de procesos.
            procesos.append({
                "id": ids[i],
                "tll": tll_actual,  # Tiempo de llegada.
                "rafaga": random.randint(2, 10),  # Duración de la ráfaga (aleatoria entre 2 y 10).
                "prioridad": random.randint(1, 4),  # Prioridad (aleatoria entre 1 y 4).
                "estado": "Nuevo"  # Estado inicial del proceso.
            })
        tll_actual += random.randint(1, 3)  # Incrementa el tiempo de llegada aleatoriamente.
        time.sleep(random.uniform(1, 2))  # Simula un retraso entre la generación de procesos.

# Calcula los tiempos del planificador, como tiempo de comienzo, final, retorno y espera.
def calcular_tiempos():
    tiempo_actual = 0  # Tiempo actual del simulador.

    while True:
        with lock:
            if not procesos:  # Si no hay procesos, detiene el cálculo.
                queue_grafico.put(None)
                queue_tabla.put(None)
                break

            # Ordena los procesos por prioridad y tiempo de llegada.
            procesos_ordenados = sorted(procesos, key=lambda x: (x["prioridad"], x["tll"]))

        for proceso in procesos_ordenados:
            if proceso["estado"] == "Nuevo":  # Solo procesa los que están en estado "Nuevo".
                proceso["tc"] = max(tiempo_actual, proceso["tll"])  # Tiempo de comienzo.
                proceso["tf"] = proceso["tc"] + proceso["rafaga"]  # Tiempo final.
                proceso["tr"] = proceso["tf"] - proceso["tll"]  # Tiempo de retorno.
                proceso["te"] = proceso["tr"] - proceso["rafaga"]  # Tiempo de espera.
                proceso["estado"] = "Ejecución"  # Cambia el estado a "Ejecución".

                tiempo_actual = proceso["tf"]  # Actualiza el tiempo actual al final del proceso.

                # Simula un bloqueo aleatorio (10% de probabilidad).
                if random.random() < 0.1:
                    proceso["estado"] = "Bloqueado"
                    time.sleep(2)  # Simula el tiempo de bloqueo.

                # Si no está bloqueado, marca el proceso como terminado.
                if proceso["estado"] != "Bloqueado":
                    proceso["estado"] = "Terminado"

                # Prepara la tabla con los datos actualizados.
                tabla = [[
                    p["id"], p["tll"], p["rafaga"], p["prioridad"], p.get("tc", ""), 
                    p.get("tf", ""), p.get("tr", ""), p.get("te", ""), 
                    p["estado"]
                ] for p in procesos_ordenados]

                queue_tabla.put(tabla)  # Envía la tabla actualizada a la cola.
                queue_grafico.put((procesos_ordenados, tabla))  # Envía los datos para el gráfico.
                time.sleep(2)  # Simula un intervalo entre cálculos.

# Actualiza la tabla en la interfaz gráfica.
def actualizar_tabla(tree):
    if not queue_tabla.empty():  # Si hay datos en la cola de la tabla.
        tabla = queue_tabla.get()
        if tabla is None:  # Si no hay más datos, detiene la actualización.
            return

        # Limpia la tabla.
        for row in tree.get_children():
            tree.delete(row)

        # Agrega las filas actualizadas.
        for row in tabla:
            tree.insert("", "end", values=row)

    tree.after(1000, actualizar_tabla, tree)  # Repite la actualización cada segundo.

# Actualiza el gráfico de Gantt en la interfaz gráfica.
def actualizar_grafico(fig, ax, canvas):
    if not queue_grafico.empty():  # Si hay datos en la cola del gráfico.
        datos = queue_grafico.get()
        if datos is None:  # Si no hay más datos, detiene la actualización.
            return

        procesos_actuales, _ = datos
        y_labels = [f"{p['id']} (P{p['prioridad']})" for p in procesos_actuales]  # Etiquetas de procesos.
        start_times = [p.get("tc", 0) for p in procesos_actuales]  # Tiempos de comienzo.
        durations = [p["rafaga"] for p in procesos_actuales]  # Duraciones de ráfagas.

        ax.clear()  # Limpia el gráfico.
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Procesos")
        ax.set_title("Diagrama de Gantt con Prioridades")
        ax.grid(axis='x', linestyle='--', alpha=0.7)  # Agrega una cuadrícula.
        ax.barh(y_labels, durations, left=start_times, color='purple', edgecolor='black')  # Dibuja las barras.

        # Agrega etiquetas con los tiempos finales.
        for i, proceso in enumerate(procesos_actuales):
            if "tc" in proceso:
                ax.text(proceso["tc"] + proceso["rafaga"] / 2, i, str(proceso["tf"]), 
                        ha='center', va='center', color='black')

        canvas.draw()  # Redibuja el gráfico.

    canvas.get_tk_widget().after(1000, actualizar_grafico, fig, ax, canvas)  # Repite cada segundo.

# Función principal.
def main():
    root = tk.Tk()
    root.title("Prioridades")

    # Configuración de la tabla.
    frame_tabla = ttk.Frame(root)
    frame_tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    columns = ["Nombre", "T.Llegada", "Ráfaga", "Prioridad", "T.Comienzo", "T.Final", "T.Retorno", "T.Espera", "Estado"]
    tree = ttk.Treeview(frame_tabla, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill=tk.BOTH, expand=True)

    # Configuración del gráfico.
    frame_grafico = ttk.Frame(root)
    frame_grafico.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Hilos para generación y cálculo de procesos.
    thread_generador = threading.Thread(target=generar_procesos)
    thread_calculo = threading.Thread(target=calcular_tiempos)

    thread_generador.start()
    thread_calculo.start()

    # Inicia las actualizaciones de la tabla y el gráfico.
    actualizar_tabla(tree)
    actualizar_grafico(fig, ax, canvas)

    root.mainloop()  # Inicia la interfaz gráfica.

    thread_generador.join()  # Espera a que termine el hilo de generación.
    thread_calculo.join()  # Espera a que termine el hilo de cálculo.

# Ejecuta la aplicación.
if __name__ == "__main__":
    main()
