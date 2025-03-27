import pyautogui
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
import keyboard
from tkinter import ttk
import json
import os
import sys

# === Настройки (по умолчанию) ===
STEP_X = 11
STEP_Y = 11
KEY_DELAY = 0.1
MOVE_DELAY = 0.05
RECT_WIDTH = 10
RECT_HEIGHT = 10

CONFIG_FILE = os.path.splitext(os.path.basename(sys.argv[0]))[0] + ".json"

EMOJI_TO_KEY = {
    '🟫': '1', '🟨': '2', '🟩': '3', '⬜': '4', '🟪': '5', '🟡': '6',
    '⬛': '7', '🟥': '8', '🟢': '9', '🟧': '0', '🟦': '-', '⚫': '=', '🔺': '='
}

positions = {
    "start": None,
    "scroll_up": None,
    "scroll_down": None,
    "scroll_left": None,
    "scroll_right": None
}

map_file = None
root = None
stop_flag = False
pause_flag = False
current_capture = None

mini_mode = False
mini_window = None
progress_var = None
status_var = None
coord_var = None

def click_scroll(name):
    pos = positions.get(name)
    if pos:
        pyautogui.click(pos)
        time.sleep(0.2)

def format_remaining_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if hours > 0:
        parts.append(f"{hours} час{'ов' if hours != 1 else ''}")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes} минут{'а' if minutes == 1 else '' if 2 <= minutes <= 4 else ''}")
    parts.append(f"{secs} секунд{'а' if secs == 1 else '' if 2 <= secs <= 4 else ''}")
    return ", ".join(parts)


def start_drawing():
    global stop_flag, pause_flag
    if not map_file:
        messagebox.showerror("Ошибка", "Файл карты не выбран")
        return
    for k in positions:
        if not positions[k]:
            messagebox.showerror("Ошибка", f"Позиция не установлена: {k}")
            return
    try:
        with open(map_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            tile_map = [list(line) for line in lines]
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить карту: {e}")
        return

    stop_flag = False
    pause_flag = False
    total_rows = len(tile_map)
    total_cols = max(len(row) for row in tile_map)
    total = total_rows * total_cols
    done = 0
    if mini_mode:
        status_var.set("В работе")

    px, py = positions['start']
    blocks_y = (total_rows + RECT_HEIGHT - 1) // RECT_HEIGHT
    blocks_x = (total_cols + RECT_WIDTH - 1) // RECT_WIDTH

    start_time = time.time()

    for by in range(blocks_y):
        for bx in range(blocks_x):
            if by > 0:
                click_scroll("scroll_down")
            if bx > 0:
                click_scroll("scroll_right")

            for y in range(RECT_HEIGHT):
                map_y = by * RECT_HEIGHT + y
                if map_y >= total_rows:
                    continue
                for x in range(RECT_WIDTH):
                    map_x = bx * RECT_WIDTH + x
                    if map_x >= len(tile_map[map_y]):
                        continue
                    if stop_flag:
                        if mini_mode:
                            status_var.set("Остановлено")
                        return
                    while pause_flag:
                        time.sleep(0.1)

                    key = EMOJI_TO_KEY.get(tile_map[map_y][map_x], '=')
                    pyautogui.press(key)
                    time.sleep(KEY_DELAY)
                    pyautogui.click(px + x * STEP_X, py + y * STEP_Y)
                    time.sleep(MOVE_DELAY)

                    done += 1

                    if mini_mode:
                        percent = (done / total) * 100
                        elapsed = time.time() - start_time
                        avg_time = elapsed / done if done > 0 else 0
                        remaining_time = avg_time * (total - done)
                        human_time = format_remaining_time(remaining_time)

                        progress_var.set(percent)
                        status_var.set(f"{done}/{total} клеток ({percent:.1f}%)")
                        time_var.set(f"Осталось: {human_time}")
                        coord_var.set(f"Координаты: {map_y},{map_x}")

    if mini_mode:
        status_var.set("Готово")

def toggle_mini_mode():
    global mini_mode, mini_window, progress_var, status_var, coord_var, time_var
    if mini_mode:
        if mini_window:
            mini_window.destroy()
        mini_mode = False
    else:
        mini_window = tk.Toplevel()
        mini_window.title("H3 Printer Status")
        mini_window.attributes("-topmost", True)
        mini_window.resizable(True, True)

        font_small = ("Arial", 9)

        progress_var = tk.DoubleVar()
        status_var = tk.StringVar(value="Не запущено")
        coord_var = tk.StringVar(value="Координаты: -")
        time_var = tk.StringVar(value="Осталось: -")

        ttk.Progressbar(mini_window, variable=progress_var, maximum=100).pack(fill="x", padx=10, pady=5)

        tk.Label(mini_window, textvariable=coord_var, font=font_small, anchor="w").pack(fill="x", padx=10)
        tk.Label(mini_window, textvariable=status_var, font=font_small, fg="blue", anchor="w").pack(fill="x", padx=10)
        tk.Label(mini_window, textvariable=time_var, font=font_small, fg="blue", anchor="w").pack(fill="x", padx=10)

        mini_window.update_idletasks()
        req_width = max(300, mini_window.winfo_reqwidth())
        mini_window.geometry(f"{req_width}x120")

        mini_mode = True


def capture_position():
    global current_capture
    if current_capture:
        x, y = pyautogui.position()
        pixel = pyautogui.screenshot().getpixel((x, y))
        color = '#%02x%02x%02x' % pixel
        positions[current_capture] = (x, y)
        lbl_positions[current_capture].config(text=f"{current_capture}: {x}, {y} | {color}")
        current_capture = None
        save_config()

def set_capture(name):
    global current_capture
    current_capture = name
    lbl_info.config(text=f"Наведи на {name} и нажми Enter")

def choose_file():
    global map_file
    path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if path:
        map_file = path
        lbl_file.config(text=f"Файл: {path}")

def load_config():
    global positions, KEY_DELAY, MOVE_DELAY, STEP_X, STEP_Y, RECT_WIDTH, RECT_HEIGHT
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            positions.update(config.get("positions", {}))
            KEY_DELAY = config.get("key_delay", KEY_DELAY)
            MOVE_DELAY = config.get("move_delay", MOVE_DELAY)
            STEP_X = config.get("step_x", STEP_X)
            STEP_Y = config.get("step_y", STEP_Y)
            RECT_WIDTH = config.get("rect_width", RECT_WIDTH)
            RECT_HEIGHT = config.get("rect_height", RECT_HEIGHT)

def save_config():
    global KEY_DELAY, MOVE_DELAY, STEP_X, STEP_Y, RECT_WIDTH, RECT_HEIGHT
    try:
        KEY_DELAY = float(entry_key_delay.get())
        MOVE_DELAY = float(entry_move_delay.get())
        STEP_X = int(entry_step_x.get())
        STEP_Y = int(entry_step_y.get())
        RECT_WIDTH = int(entry_rect_width.get())
        RECT_HEIGHT = int(entry_rect_height.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректные значения в полях настроек")
        return
    config = {
        "positions": positions,
        "key_delay": KEY_DELAY,
        "move_delay": MOVE_DELAY,
        "step_x": STEP_X,
        "step_y": STEP_Y,
        "rect_width": RECT_WIDTH,
        "rect_height": RECT_HEIGHT
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    messagebox.showinfo("Сохранение", "Настройки сохранены в конфиг")

def monitor_hotkeys():
    keyboard.add_hotkey('esc', lambda: setattr(sys.modules[__name__], 'stop_flag', True))
    keyboard.add_hotkey('f4', lambda: setattr(sys.modules[__name__], 'stop_flag', True))
    keyboard.add_hotkey('space', lambda: setattr(sys.modules[__name__], 'pause_flag', not pause_flag))
    keyboard.add_hotkey('enter', capture_position)
    keyboard.add_hotkey('ctrl+m', toggle_mini_mode)
    keyboard.add_hotkey('f5', lambda: Thread(target=start_drawing).start())

root = tk.Tk()
root.title("Генератор карты HoMM3")
root.geometry("520x700")
root.attributes("-topmost", True)
root.resizable(True, True)

load_config()

lbl_info = tk.Label(root, text="Нажми кнопку для выбора позиции")
lbl_info.pack()

lbl_positions = {}
for key in positions:
    btn = tk.Button(root, text=f"Установить {key}", command=lambda k=key: set_capture(k))
    btn.pack(pady=2)
    lbl = tk.Label(root, text=f"{key}: {positions[key] if positions[key] else 'не выбрано'}")
    lbl.pack()
    lbl_positions[key] = lbl

btn_file = tk.Button(root, text="Выбрать файл карты", command=choose_file)
btn_file.pack(pady=5)

lbl_file = tk.Label(root, text="Файл: не выбран")
lbl_file.pack()

frame_delays = tk.Frame(root)
frame_delays.pack(pady=5)

tk.Label(frame_delays, text="Задержка клавиши (сек):").grid(row=0, column=0, sticky='e')
entry_key_delay = tk.Entry(frame_delays, width=5)
entry_key_delay.insert(0, str(KEY_DELAY))
entry_key_delay.grid(row=0, column=1)

tk.Label(frame_delays, text="Задержка мыши (сек):").grid(row=1, column=0, sticky='e')
entry_move_delay = tk.Entry(frame_delays, width=5)
entry_move_delay.insert(0, str(MOVE_DELAY))
entry_move_delay.grid(row=1, column=1)

frame_steps = tk.Frame(root)
frame_steps.pack(pady=5)

tk.Label(frame_steps, text="Шаг X (пикс):").grid(row=0, column=0, sticky='e')
entry_step_x = tk.Entry(frame_steps, width=5)
entry_step_x.insert(0, str(STEP_X))
entry_step_x.grid(row=0, column=1)

tk.Label(frame_steps, text="Шаг Y (пикс):").grid(row=1, column=0, sticky='e')
entry_step_y = tk.Entry(frame_steps, width=5)
entry_step_y.insert(0, str(STEP_Y))
entry_step_y.grid(row=1, column=1)

frame_rect = tk.Frame(root)
frame_rect.pack(pady=5)

tk.Label(frame_rect, text="Ширина блока:").grid(row=0, column=0, sticky='e')
entry_rect_width = tk.Entry(frame_rect, width=5)
entry_rect_width.insert(0, str(RECT_WIDTH))
entry_rect_width.grid(row=0, column=1)

tk.Label(frame_rect, text="Высота блока:").grid(row=1, column=0, sticky='e')
entry_rect_height = tk.Entry(frame_rect, width=5)
entry_rect_height.insert(0, str(RECT_HEIGHT))
entry_rect_height.grid(row=1, column=1)

btn_save = tk.Button(root, text="Сохранить настройки", command=save_config)
btn_save.pack(pady=5)

btn_start = tk.Button(root, text="Старт", command=lambda: Thread(target=start_drawing).start(), bg='green', fg='white')
btn_start.pack(pady=10)

Thread(target=monitor_hotkeys, daemon=True).start()

if __name__ == "__main__":
    try:
        root.mainloop()
    except Exception as e:
        print("Ошибка:", e)
        input("Нажми Enter, чтобы закрыть...")
