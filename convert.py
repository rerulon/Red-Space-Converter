import re
import os
import sys
import subprocess
import time

print("===ПРОСТОЙ СОВЕТСКИЙ КОНВЕРТЕР V1.0===")
print("Переводит код из непонятного в понятный")

#стираем все дубли строк
class DedupFileWriter:
    def __init__(self, file_obj):
        self.file = file_obj
        self.last_written = ""

    def _get_hide_target(self, text):
        if not text: return None
        stripped = text.strip()
        if stripped.startswith("hide "):
            remainder = stripped[5:]
            parts = remainder.split()
            if parts:
                return parts[0]
        return None

    def write(self, text):
        if text == self.last_written:
            return

        curr_target = self._get_hide_target(text)
        if curr_target:
            prev_target = self._get_hide_target(self.last_written)
            if prev_target and prev_target == curr_target:
                return
        
        self.file.write(text)
        self.last_written = text

    def close(self):
        self.file.close()

#конфиг
INPUT_FILE = "MASTER.FIX"   
OUTPUT_DIR = "converted_scripts"
INPUT_ENCODING = "cp1251" 

OBJECT_NAMES_MAPPING = {
    "journal1": "bg_journal1",
}

#глобалки
active_layers = {} 
active_objects = set()
scene_index = 1 

def parse_attributes(line_content):
    parts = line_content.split()
    attrs = {}
    for part in parts:
        if "=" in part:
            try:
                k, v = part.split("=", 1)
                attrs[k] = v
            except ValueError:
                pass
    return attrs

def convert_line(line, current_file, line_num_debug):
    global active_layers, active_objects, scene_index
    
    #Спасибо ТАОТА
    line = re.sub(r'\s+', ' ', line)
    line = re.sub(r'\s*=\s*', '=', line)
    line = line.strip()
    
    if not line:
        if current_file: current_file.write("\n")
        return current_file 

    if line.startswith("-"):
        if current_file: current_file.write(f"    # {line.lstrip('-')}\n")
        return current_file

    #Режем по сценам. С умом.
    if line.startswith("scene "):
        parts = line.split()
        if len(parts) > 1:
            scene_name = parts[1]
            if current_file: current_file.close()
            
            active_layers = {} 
            active_objects = set()
            
            if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
            
            filename = f"{scene_index:03d}_v{scene_name}.rpy"
            scene_index += 1
            
            new_path = os.path.join(OUTPUT_DIR, filename)
            
            raw_file = open(new_path, "w", encoding="utf-8")
            f = DedupFileWriter(raw_file)
            
            f.write(f"label v{scene_name}:\n")
            return f 
    
    if not current_file: return None

    #панорамки в свой трансформер
    if line.startswith("qmove"):
        attrs = parse_attributes(line)
        start_raw = attrs.get("start", "")
        finish_raw = attrs.get("finish", "")
        obj_raw = attrs.get("object")
        
        try:
            s_parts = start_raw.split(":")
            f_parts = finish_raw.split(":")
            
            if len(s_parts) >= 3 and len(f_parts) >= 3 and obj_raw:
                sx = int(s_parts[1])
                sy = int(s_parts[2])
                fx = int(f_parts[1])
                fy = int(f_parts[2])
                
                obj_renpy = OBJECT_NAMES_MAPPING.get(obj_raw, obj_raw)
                transform_name = None
                
                if sy != fy:
                    if sy > fy: transform_name = "scroll_up_to_down"
                    else: transform_name = "scroll_down_to_up"
                elif sx != fx:
                    if sx < fx: transform_name = "scroll_right_to_left"
                    else: transform_name = "scroll_left_to_right"
                
                if transform_name:
                    current_file.write(f"    show {obj_renpy} at {transform_name}\n")
                    #синхра для линейного перемещения в трансформере
                    current_file.write("    with Pause(5.0)\n")
                else:
                    current_file.write(f"    # QMOVE STATIC: {line}\n")
            else:
                 current_file.write(f"    # QMOVE PARSE ERROR: {line}\n")
        except ValueError:
            current_file.write(f"    # QMOVE VALUE ERROR: {line}\n")
        return current_file

    #меняем прозрачность
    if line.startswith("set opacity"):
        parts = line.split()
        op_part = parts[1] if len(parts) > 1 else ""
        attrs = parse_attributes(line)
        obj_raw = attrs.get("object") or attrs.get("character")
        if obj_raw and ":" in op_part:
            obj_renpy = OBJECT_NAMES_MAPPING.get(obj_raw, obj_raw)
            vals = op_part.split(":")
            if len(vals) >= 3:
                try:
                    start_op = int(vals[1])
                    end_op = int(vals[2])
                    if start_op > 0 and end_op == 0:
                        current_file.write(f"    hide {obj_renpy} with dissolve\n")
                    elif start_op == 0 and end_op > 0:
                        current_file.write(f"    show {obj_renpy} with dissolve\n")
                    else:
                        current_file.write(f"    # TODO: Opacity change {start_op}->{end_op} for {obj_renpy}\n")
                except ValueError: pass
        return current_file

    #тряска на впанчи
    if line.startswith("quake"):
        current_file.write("    with vpunch\n")
        return current_file

    #все что запечено как объекты
    if line.startswith("set object"):
        attrs = parse_attributes(line)
        obj_raw = attrs.get("object")
        if obj_raw:
            obj_renpy = OBJECT_NAMES_MAPPING.get(obj_raw, obj_raw)
            current_file.write(f"    show {obj_renpy} with dissolve\n")
        return current_file

    #удаляем delete. lol.
    if line.startswith("delete "):
        obj_raw = line.split()[1]
        obj_renpy = OBJECT_NAMES_MAPPING.get(obj_raw, obj_raw)
        current_file.write(f"    hide {obj_renpy} with dissolve\n")
        return current_file

    #триггеры в булеву
    if line.startswith("set trigger"):
        content = line[11:].strip()
        if "=" in content:
            try:
                var_name, val = content.split("=", 1)
                var_name = var_name.strip()
                val = val.lower()
                if val == "yes": py_val = "True"
                elif val == "no": py_val = "False"
                elif val.isdigit(): py_val = val
                else: py_val = f"'{val}'"
                current_file.write(f"    $ {var_name} = {py_val}\n")
            except ValueError:
                current_file.write(f"    # ERROR PARSING TIGGER: {line}\n")
        return current_file

    #bg to scene
    if line.startswith("set bg"):
        attrs = parse_attributes(line)
        bg_name = attrs.get("bg")
        if bg_name:
            current_file.write(f"    scene {bg_name}\n")
        return current_file

    #black
    if line == "clear all":
        current_file.write("    scene black\n")
        active_layers = {}
        return current_file

    #chara
    if line.startswith("set character"):
        attrs = parse_attributes(line)
        char_name = attrs.get("character")
        level = attrs.get("level")
        align = attrs.get("align", "center") 
        
        if align == ":0:0" or align == ":30:0": 
            align = "right"

        if char_name:
            if level: active_layers[level] = char_name
            effect = "dissolve" if "opacity" in line else None
            renpy_cmd = f"    show {char_name} at {align}"
            if effect: renpy_cmd += " with dissolve"
            current_file.write(renpy_cmd + "\n")
        return current_file

    #clear shit
    if line.startswith("clear level="):
        try:
            level = line.split("=")[1]
            char_to_hide = active_layers.get(level)
            if char_to_hide:
                current_file.write(f"    hide {char_to_hide}\n")
                del active_layers[level]
        except IndexError: pass
        return current_file

    #обработка текста персов
    if line.startswith("set text"):
        parts = line.split("text=", 1)
        if len(parts) == 2:
            meta_part = parts[0]
            content_text = parts[1]
            
            attrs = parse_attributes(meta_part)
            voice_file = attrs.get("voice")
            name = attrs.get("name")
            font = attrs.get("font", "")
            
            content_text = content_text.replace("/vname1/", "[captain_name]")
            if name == "/vname1/":
                name = "[captain_name]"

            if "set text default" in line:
                if voice_file:
                    voice_path = "audio/voice/" + voice_file.replace(".wav", ".ogg")
                    current_file.write(f'    voice "{voice_path}"\n')
                
                renpy_name = f"'{name}'" if name else ""
                content_text = content_text.replace('"', '\\"')
                current_file.write(f'    {renpy_name} "{content_text}"\n')
            else:
                voice_path = ""
                if voice_file:
                    voice_path = "audio/voice/" + voice_file.replace(".wav", ".ogg")
                
                speaker_arg = '"journal"'
                if "Verdana" in font:
                    speaker_arg = '"subtitle"'
                elif name:
                    speaker_arg = f'"{name}"'

                code = f'    $ play_line(\n        """{content_text}""",\n        "{voice_path}",\n        {speaker_arg}\n    )\n'
                current_file.write(code)
        return current_file

    #goto 2 jump
    if line.startswith("goto "):
        try:
            label = line.split()[1]
            current_file.write(f"    jump v{label}\n")
        except IndexError:
            current_file.write(f"    # ERROR GOTO: {line}\n")
        return current_file

    #if else with отступы :3
    if line.startswith("if "):
        if " goto " in line:
            try:
                cond_part, label_part = line.split(" goto ", 1)
                label_part = label_part.strip()
                cond_part = cond_part.replace("=", "==")
                #новая строка + отступ
                current_file.write(f"    {cond_part}:\n        jump v{label_part}\n")
            except ValueError:
                current_file.write(f"    # ERROR IF-GOTO: {line}\n")
            return current_file

        if " set trigger " in line:
            try:
                cond_part, action_part = line.split(" set trigger ", 1)
                cond_part = cond_part.replace("=", "==")
                if "=" in action_part:
                    var, val = action_part.split("=", 1)
                    var = var.strip()
                    val = val.strip().lower()
                    if val == "yes": py_val = "True"
                    elif val == "no": py_val = "False"
                    elif val.isdigit(): py_val = val
                    else: py_val = f"'{val}'"
                    #новая строка + отступ
                    current_file.write(f"    {cond_part}:\n        $ {var} = {py_val}\n")
            except ValueError:
                current_file.write(f"    # ERROR IF-TRIGGER: {line}\n")
            return current_file

        print(f"[Line {line_num_debug}] WARNING: Нестандартный IF: {line}")
        renpy_line = line.replace("=", "==")
        current_file.write(f"    # TODO CHECK INDENT: {renpy_line}\n")
        return current_file

    #обработка пауз
    if line.startswith("set delay="):
        try:
            ms = int(line.split("=")[1])
            sec = ms / 1000.0
            current_file.write(f"    with Pause({sec})\n")
        except (IndexError, ValueError): pass
        return current_file
        
    #обработка жестких пауз
    if line.startswith("set pause"):
        # ЗАМЕНА НА ЖЕСТКУЮ ПАУЗУ 3 СЕКУНДЫ (БЛОКИРОВКА КЛИКА)
        current_file.write("    $ renpy.pause(3.0, hard=True)\n")
        return current_file

    #обработка некоторых меню
    if line.startswith("set section menu="):
        try:
            menu_name = line.split("=")[1]
            if menu_name == "cards1": 
                current_file.write("    jump vdurgame2\n")
            elif menu_name.startswith("necro"): 
                current_file.write("    jump vnecro\n")
            else: 
                current_file.write(f"    call screen v{menu_name}\n")
        except IndexError: pass
        return current_file

    #в помоечку
    
    if "set interface" in line:
        return current_file

    if "set enter name" in line:
        current_file.write(f"    # SKIPPED: {line}\n")
        return current_file

    current_file.write(f"    # UNPARSED: {line}\n")
    return current_file

#стартуем

if not os.path.exists(INPUT_FILE):
    print(f"!!! ОШИБКА: Файл {INPUT_FILE} не найден!")
    print("Сначала запусти fix_master.py")
    input("Нажми Enter чтобы выйти...")
    sys.exit()

print(f"Файл {INPUT_FILE} найден. Начинаем обработку...")

try:
    current_f = None
    with open(INPUT_FILE, "r", encoding=INPUT_ENCODING) as f: 
        for line_num, line_raw in enumerate(f):
            try:
                current_f = convert_line(line_raw, current_f, line_num + 1)
            except Exception as e:
                print(f"КРИТИЧЕСКАЯ ОШИБКА в строке {line_num}: {e}")
                print(f"Текст строки: {line_raw}")
                
    if current_f: current_f.close()
    print(f"Нарезка завершена! Обработано сцен: {scene_index-1}.")
    
    #вызов патчера
    patcher_script = "patcher.py"
    if os.path.exists(patcher_script):
        print(f"\n=== Запуск {patcher_script} ===")
        try:
            subprocess.run([sys.executable, patcher_script], check=True)
            print("Патчер завершил работу.")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при выполнении патчера: {e}")

    #заливаем клеем
    merge_script = "merge.py"
    if os.path.exists(merge_script):
        print(f"\n=== Запуск {merge_script} ===")
        try:
            subprocess.run([sys.executable, merge_script], check=True)
            print("Объединение завершено успешно.")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при выполнении merge.py: {e}")
    else:
        print(f"\nВНИМАНИЕ: Файл {merge_script} не найден.")

except LookupError:
    print(f"ОШИБКА КОДИРОВКИ: {INPUT_ENCODING} не поддерживается.")
except Exception as e:
    print(f"НЕИЗВЕСТНАЯ ОШИБКА: {e}")

input("\nГотово. Нажми Enter чтобы закрыть окно...")