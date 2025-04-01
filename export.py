import os
import shutil

source_root = '.'  # текущая директория
destination_folder = 'chatgpt'

# Создаём папку chatgpt, если её ещё нет
os.makedirs(destination_folder, exist_ok=True)

for root, dirs, files in os.walk(source_root):
    # Пропускаем папку экспорта
    if os.path.abspath(root).startswith(os.path.abspath(destination_folder)):
        continue

    for file in files:
        if file.endswith('.md'):
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, source_root)

            # Если файл в корне, имя не меняем
            if root == source_root:
                output_name = file
            else:
                no_ext_path = os.path.splitext(relative_path)[0]
                output_name = no_ext_path.replace(os.sep, '_') + '.md'

            output_path = os.path.join(destination_folder, output_name)
            shutil.copy2(full_path, output_path)

print("✅ Все .md файлы скопированы в папку chatgpt с корректными именами.")
