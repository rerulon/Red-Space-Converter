import os

print("===ПРОСТОЙ СОВЕТСКИЙ ПАТЧЕР V.1.0===")
print("===РАБОТАЕМ. ПАТЧИМ. СТРУЯЧИМ.===")

#Папка, где лежат нарезанные файлы
TARGET_DIR = "converted_scripts"

#Список патчей: (Имя файла, Что заменить, На что заменить)
PATCHES = [
    (
        "239_v1xxx_run3_medblok2.rpy",          # Файл
        "label v1xxx_run3_medblok2:",           # Старая строка
        "label v1xxx_run3_medblok2s:"           # Новая строка
    ),
]

def apply_patches():
    if not os.path.exists(TARGET_DIR):
        print(f"Папка {TARGET_DIR} не найдена. Нечего патчить.")
        return

    count = 0
    for filename, old_str, new_str in PATCHES:
        filepath = os.path.join(TARGET_DIR, filename)
        
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if old_str in content:
                    new_content = content.replace(old_str, new_str)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"[OK] Патч применен: {filename}")
                    count += 1
                else:
                    #Проверяем, есть ли исправления
                    if new_str in content:
                        print(f"[SKIP] Уже исправлено: {filename}")
                    else:
                        print(f"[FAIL] Строка не найдена в {filename}")
            except Exception as e:
                print(f"[ERR] Ошибка при чтении {filename}: {e}")
        else:
            print(f"[MISS] Файл не найден: {filename}")

    print(f"Патчинг завершен. Применено правок: {count}")

if __name__ == "__main__":
    apply_patches()