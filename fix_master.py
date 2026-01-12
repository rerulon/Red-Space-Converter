import hashlib
import os
import sys
import subprocess

INPUT_FILE = "MASTER.SCN"
OUTPUT_FILE = "MASTER.FIX"
#MD5 оригинального файла для проверки
EXPECTED_MD5 = "691ddb7fd2f68fbbaf624544d9818479"
ENCODING = "cp1251"

def calculate_md5(filepath):
    """Считаем хешник"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def apply_fixes():
    if not os.path.exists(INPUT_FILE):
        print(f"Файл {INPUT_FILE} не найден!")
        return
        
    print("===ПРОСТОЙ СОВЕТСКИЙ ИСПРАВЛЯТЕЛЬ V.1.0===")
    print("===Ну да. Сначала патчим оригинальный код.===")
    print(f"Проверка целостности {INPUT_FILE}...")
    current_md5 = calculate_md5(INPUT_FILE)

    if current_md5 != EXPECTED_MD5:
        print("ВНИМАНИЕ!!!")
        print(f"MD5 файла не совпадает с оригинальным!")
        print(f"Ожидалось: {EXPECTED_MD5}")
        print(f"Получено:  {current_md5}")
        print("Возможно, файл уже был изменен или это другая версия.")
        choice = input("Всё равно продолжить? (y/n): ")
        if choice.lower() != 'y':
            return
    else:
        print("MD5 совпадает. Файл оригинальный.")

    print("Применяем патчи...")
    
    try:
        with open(INPUT_FILE, "r", encoding=ENCODING) as f:
            lines = f.readlines()

        #2016: run2_ medblok2 -> run2_medblok2
        idx = 2016 - 1
        if idx < len(lines) and "run2_ medblok2" in lines[idx]:
            lines[idx] = lines[idx].replace("run2_ medblok2", "run2_medblok2")
            print(f"[OK] Строка 2016 исправлена")

        #2113: run2_ robot2 -> run2_robot2
        idx = 2113 - 1
        if idx < len(lines) and "run2_ robot2" in lines[idx]:
            lines[idx] = lines[idx].replace("run2_ robot2", "run2_robot2")
            print(f"[OK] Строка 2113 исправлена")

        #2143: scene run2_ robot2 -> scene run2_robot2
        idx = 2143 - 1
        if idx < len(lines) and "scene run2_ robot2" in lines[idx]:
            lines[idx] = lines[idx].replace("scene run2_ robot2", "scene run2_robot2")
            print(f"[OK] Строка 2143 исправлена")

        #v-префикс
        vars_to_fix = [
            (4059, "set trigger 11_necro=1", "set trigger v11_necro=1"),
            (11284, "set trigger 12_necro=1", "set trigger v12_necro=1"),
            (18012, "set trigger 13_necro=1", "set trigger v13_necro=1")
        ]
        for line_num, old_str, new_str in vars_to_fix:
            idx = line_num - 1
            if idx < len(lines) and old_str in lines[idx]:
                lines[idx] = lines[idx].replace(old_str, new_str)
                print(f"[OK] Строка {line_num} исправлена: переменная v*_necro")

        #z-префикс
        z_renames = [
            (5726,  "scene s1111_6", "scene zs1111_6"),
            (22361, "scene s1331_6", "scene zs1331_6"),
            (9418,  "scene s1121_3", "scene zs1121_3"),
            (14464, "scene s1222_2", "scene zs1222_2"),
            (14803, "scene s1222_6", "scene zs1222_6"),
            (22734, "scene s1332_2", "scene zs1332_2"),
            (23116, "scene s1332_4", "scene zs1332_4"),
            (22874, "scene s1332_5", "scene zs1332_5")
        ]
        
        for line_num, old_str, new_str in z_renames:
            idx = line_num - 1
            if idx < len(lines) and old_str in lines[idx]:
                lines[idx] = lines[idx].replace(old_str, new_str)
                print(f"[OK] Строка {line_num} переименована: {old_str} -> {new_str}")

        #6028: s1112_2 -> s1112_1
        idx = 6028 - 1
        if idx < len(lines) and "scene s1112_2" in lines[idx]:
            lines[idx] = lines[idx].replace("scene s1112_2", "scene s1112_1")
            print(f"[OK] Строка 6028 исправлена")

        #правки логики переходов 1
        replacements_ss = [
            (18060, "1xxx_run4_medblok1", "1xxxSS_run4_medblok1"),
            (18061, "1xxx_run4_medblok2", "1xxxSS_run4_medblok2"),
            (18082, "1xxx_run4_medblok2", "1xxxSS_run4_medblok2")
        ]
        for line_num, old_str, new_str in replacements_ss:
            idx = line_num - 1
            if idx < len(lines) and old_str in lines[idx]:
                lines[idx] = lines[idx].replace(old_str, new_str)
                print(f"[OK] Строка {line_num} исправлена: {old_str} -> {new_str}")

        #правки логики переходов 2
        replacements_other = [
            (2811, "1xxx_run3_robot1", "1xxx_run3_robot2"),
            (11332, "1xxx_run3_medblok1", "12xx_run4_medblok1"),
            (11333, "1xxx_run3_medblok2", "12xx_run4_medblok2")
        ]
        for line_num, old_str, new_str in replacements_other:
            idx = line_num - 1
            if idx < len(lines) and old_str in lines[idx]:
                lines[idx] = lines[idx].replace(old_str, new_str)
                print(f"[OK] Строка {line_num} исправлена: {old_str} -> {new_str}")


        #сохранялка
        with open(OUTPUT_FILE, "w", encoding=ENCODING) as f:
            f.writelines(lines)
        
        print(f"\nГотово! Исправленный файл сохранен как: {OUTPUT_FILE}")

        #запуск конвертера
        convert_script = "convert.py"
        if os.path.exists(convert_script):
            print(f"\n=== Запуск {convert_script} ===")
            try:
                subprocess.run([sys.executable, convert_script], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Ошибка при выполнении {convert_script}: {e}")
        else:
            print(f"ВНИМАНИЕ: Файл {convert_script} не найден. Конвертация не запущена.")

    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    apply_fixes()