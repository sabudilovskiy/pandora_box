import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import numpy as np
import os
import traceback

# Константы террейнов
DIRT = '🟫'
SAND = '🟨'
GRASS = '🟩'
SNOW = '⬜'
SWAMP = '🟪'
ROCKS = '🟡'
DUNGEON = '⬛'
LAVA = '🟥'
HIGHLANDS = '🟢'
WASTELAND = '🟧'
WATER = '🟦'
VOID = '⬛'
MOUNTAIN = '🔺'
MISSING = '⚫'

# Цвета террейнов (RGB)
TERRAIN_COLORS = {
    DIRT: (217, 218, 211),
    SAND: (245, 240, 229),
    GRASS: (178, 237, 202),
    SNOW: (255, 255, 255),
    SWAMP: (120, 120, 120),
    ROCKS: (200, 200, 170),
    DUNGEON: (30, 30, 30),
    LAVA: (255, 69, 0),
    HIGHLANDS: (200, 243, 218),
    WASTELAND: (255, 165, 0),
    WATER: (138, 216, 236),
    VOID: (20, 20, 20)
}


def classify_terrain(rgb):
    min_dist = float('inf')
    closest_terrain = MISSING
    for terrain, color in TERRAIN_COLORS.items():
        dist = np.linalg.norm(np.array(rgb) - np.array(color))
        if dist < min_dist:
            min_dist = dist
            closest_terrain = terrain
    return closest_terrain


def generate_map(image_path, output_size=32, smooth=False):
    try:
        img = Image.open(image_path)
        img = img.resize((output_size, output_size), Image.ANTIALIAS if smooth else Image.NEAREST)
        img_array = np.array(img)

        terrain_map = ''
        for row in img_array:
            for pixel in row:
                terrain_map += classify_terrain(pixel[:3])
            terrain_map += '\n'

        base_path = os.path.splitext(image_path)[0]
        map_path = base_path + "_map.txt"

        with open(map_path, "w", encoding="utf-8") as f:
            f.write(terrain_map)

        return map_path
    except Exception as e:
        error_log_path = "error_log.txt"
        with open(error_log_path, "a", encoding="utf-8") as log_file:
            log_file.write("❌ Ошибка при генерации карты:\n")
            log_file.write(traceback.format_exc())
            log_file.write("\n---\n")
        raise e


def browse_file():
    filename = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    if filename:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, filename)


def run_generator():
    image_path = file_entry.get()
    if not os.path.isfile(image_path):
        messagebox.showerror("Ошибка", "Файл не найден.")
        return

    try:
        size = int(size_entry.get())
    except ValueError:
        size = 32

    smooth = smooth_var.get()

    try:
        result_path = generate_map(image_path, size, smooth)
        messagebox.showinfo("Готово", f"Карта сохранена в:\n{result_path}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сгенерировать карту.\nПодробнее в error_log.txt")

# --- GUI setup ---
root = tk.Tk()
root.title("🗺️ Генератор эмодзи-карты")

tk.Label(root, text="Файл PNG:").grid(row=0, column=0, sticky="e")
file_entry = tk.Entry(root, width=40)
file_entry.grid(row=0, column=1)
tk.Button(root, text="Выбрать...", command=browse_file).grid(row=0, column=2)

tk.Label(root, text="Размер карты:").grid(row=1, column=0, sticky="e")
size_entry = tk.Entry(root)
size_entry.insert(0, "32")
size_entry.grid(row=1, column=1, sticky="w")

smooth_var = tk.BooleanVar()
tk.Checkbutton(root, text="Сглаживание", variable=smooth_var).grid(row=2, column=1, sticky="w")

tk.Button(root, text="Сгенерировать карту", command=run_generator).grid(row=3, column=1, pady=10)

root.mainloop()
