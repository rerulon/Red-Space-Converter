import os
import sys
import subprocess

INPUT_DIR = "converted_scripts"  #откуда
OUTPUT_DIR = "game_scripts"      #куда
CONFIG_FILE = "merge.config"     #конфиг
PATCHER_SCRIPT = "patcher.py"    #патчер разрезаного

def parse_config(config_path):
    """
    Парсит файл конфигурации формата:
    [
    file1.rpy
    file2.rpy
    ]=output.rpy
    """
    tasks = []
    current_inputs = []
    is_collecting = False

    if not os.path.exists(config_path):
        print(f"ОШИБКА: Не найден файл конфигурации {config_path}")
        return []

    with open(config_path, "r", encoding="utf-8") as f:
        #читаем и выкидываем CRы-LRы
        lines = [line.strip() for line in f if line.strip()]

    for line in lines:
        if line == "[":
            current_inputs = []
            is_collecting = True
        elif line.startswith("]="):
            if is_collecting:
                output_filename = line.replace("]=", "").strip()
                tasks.append({
                    "output": output_filename,
                    "inputs": current_inputs
                })
                is_collecting = False
        else:
            if is_collecting:
                current_inputs.append(line)

    return tasks

def merge_files():
    print("===ПРОСТОЙ СОВЕТСКИЙ КЛЕЙ V.1.0===")
    print("===Этим клеем на соседнем заводе, лопасти вертолетов склеивают.===")

    #запускаем простой советский патчер до процесса обрезания
    if os.path.exists(PATCHER_SCRIPT):
        print(f"\n=== Запуск {PATCHER_SCRIPT} ===")
        try:
            subprocess.run([sys.executable, PATCHER_SCRIPT], check=True)
            print("===ПАТЧИ ПРИМЕНЕНЫ. ПУПУПУ. ===\n")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при выполнении патчера: {e}")
    else:
        print(f"ВНИМАНИЕ: {PATCHER_SCRIPT} не найден, пропускаем этап правки.")

    #нюхоем папки
    if not os.path.exists(INPUT_DIR):
        print(f"Папка {INPUT_DIR} не найдена!")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    #читаем конфиг
    tasks = parse_config(CONFIG_FILE)
    if not tasks:
        print("Задач на объединение не найдено или конфиг пуст.")
        return

    print(f"Загружено {len(tasks)} групп для объединения из {CONFIG_FILE}.")

    #сборка
    total_files_merged = 0
    
    for task in tasks:
        output_name = task['output']
        input_files = task['inputs']
        
        output_path = os.path.join(OUTPUT_DIR, output_name)
        merged_content = []

        print(f"Собираем {output_name} ({len(input_files)} файлов)...")

        for filename in input_files:
            input_path = os.path.join(INPUT_DIR, filename)
            
            if os.path.exists(input_path):
                try:
                    with open(input_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        #источник кода, пометка в теле скриптов
                        header = f"\n# {'='*20} SOURCE: {filename} {'='*20}\n"
                        merged_content.append(header + content)
                        total_files_merged += 1
                except Exception as e:
                    print(f"  -> Ошибка чтения {filename}: {e}")
            else:
                print(f"  -> ВНИМАНИЕ: Файл {filename} не найден в {INPUT_DIR} (пропущен)")

        # Записываем итоговый файл
        if merged_content:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(merged_content))
            except Exception as e:
                print(f"  -> Ошибка записи {output_name}: {e}")

    print(f"\nГотово! Объединено {total_files_merged} фрагментов в {len(tasks)} файлов.")
    print(f"Результат в папке: {OUTPUT_DIR}")

if __name__ == "__main__":
    merge_files()