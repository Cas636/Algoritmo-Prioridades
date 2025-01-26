import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import queue
import time
import random

# Lista inicial de procesos
procesos = []
queue_tabla = queue.Queue()
queue_grafico = queue.Queue()
lock = threading.Lock()

def generar_procesos():
    ids = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    tll_actual = 0

    for i in range(len(ids)):
        with lock:
            procesos.append({
                "id": ids[i],
                "tll": tll_actual,
                "rafaga": random.randint(2, 10),
                "prioridad": random.randint(1, 4),
                "estado": "Nuevo"
            })
        tll_actual += random.randint(1, 3)
        time.sleep(random.uniform(1, 2))

def calcular_tiempos():
    tiempo_actual = 0

    while True:
        with lock:
            if not procesos:
                queue_grafico.put(None)
                queue_tabla.put(None)
                break

            procesos_ordenados = sorted(procesos, key=lambda x: (x["prioridad"], x["tll"]))

        for proceso in procesos_ordenados:
            if proceso["estado"] == "Nuevo":
                proceso["tc"] = max(tiempo_actual, proceso["tll"])
                proceso["tf"] = proceso["tc"] + proceso["rafaga"]
                proceso["tr"] = proceso["tf"] - proceso["tll"]
                proceso["te"] = proceso["tr"] - proceso["rafaga"]
                proceso["estado"] = "Ejecución"

                tiempo_actual = proceso["tf"]

                if random.random() < 0.3:
                    proceso["estado"] = "Bloqueado"
                    time.sleep(2)

                if proceso["estado"] != "Bloqueado":
                    proceso["estado"] = "Terminado"

                tabla = [[
                    p["id"], p["tll"], p["rafaga"], p.get("tc", ""), 
                    p.get("tf", ""), p.get("tr", ""), p.get("te", ""), 
                    p["prioridad"], p["estado"]
                ] for p in procesos_ordenados]

                queue_tabla.put(tabla)
                queue_grafico.put((procesos_ordenados, tabla))
                time.sleep(2)

def actualizar_tabla(tree):
    if not queue_tabla.empty():
        tabla = queue_tabla.get()
        if tabla is None:
            return

        for row in tree.get_children():
            tree.delete(row)

        for row in tabla:
            tree.insert("", "end", values=row)

    tree.after(1000, actualizar_tabla, tree)

def actualizar_grafico(fig, ax, canvas):
    if not queue_grafico.empty():
        datos = queue_grafico.get()
        if datos is None:
            return

        procesos_actuales, _ = datos
        y_labels = [f"{p['id']} (P{p['prioridad']})" for p in procesos_actuales]
        start_times = [p.get("tc", 0) for p in procesos_actuales]
        durations = [p["rafaga"] for p in procesos_actuales]

        ax.clear()
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Procesos")
        ax.set_title("Diagrama de Gantt con Prioridades")
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        ax.barh(y_labels, durations, left=start_times, color='skyblue', edgecolor='black')

        for i, proceso in enumerate(procesos_actuales):
            if "tc" in proceso:
                ax.text(proceso["tc"] + proceso["rafaga"] / 2, i, str(proceso["tf"]), 
                        ha='center', va='center', color='black')

        canvas.draw()

    canvas.get_tk_widget().after(1000, actualizar_grafico, fig, ax, canvas)

def main():
    root = tk.Tk()
    root.title("Simulación de Procesos con Prioridades")

    frame_tabla = ttk.Frame(root)
    frame_tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    columns = ["Proceso", "TLL", "Ráfaga", "TC", "TF", "TR", "TE", "Prioridad", "Estado"]
    tree = ttk.Treeview(frame_tabla, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill=tk.BOTH, expand=True)

    frame_grafico = ttk.Frame(root)
    frame_grafico.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    thread_generador = threading.Thread(target=generar_procesos)
    thread_calculo = threading.Thread(target=calcular_tiempos)

    thread_generador.start()
    thread_calculo.start()

    actualizar_tabla(tree)
    actualizar_grafico(fig, ax, canvas)

    root.mainloop()

    thread_generador.join()
    thread_calculo.join()

if __name__ == "__main__":
    main()
