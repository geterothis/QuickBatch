#!/usr/bin/env python3
"""
Video Renamer Script
Переименовывает видео файлы в формат: customname_90s_en_1080x1920.mp4
и сортирует их по языковым папкам (EN, RU, etc.)
"""

import os
import re
import subprocess
import shutil
import sys
import tempfile
from pathlib import Path
from moviepy.editor import VideoFileClip


def get_video_metadata(file_path):
    """
    Получает метаданные видео: разрешение и длительность
    
    Args:
        file_path (str): Путь к видео файлу
        
    Returns:
        tuple: (resolution_str, duration_seconds) или (None, None) при ошибке
    """
    try:
        with VideoFileClip(file_path) as clip:
            width = int(clip.w)
            height = int(clip.h)
            duration = int(clip.duration)
            
            resolution = f"{width}x{height}"
            return resolution, duration
    except Exception as e:
        print(f"Ошибка при получении метаданных {file_path}: {e}")
        return None, None


def extract_language_prefix(filename):
    """
    Извлекает языковой префикс из имени файла.
    Поддерживает два формата:
    1. XX_filename.mp4 (две буквы + подчеркивание в начале)  
    2. customname_30s_en_1920x1080.mp4 (язык между длительностью и разрешением)
    Приоритет: сначала проверяем формат 2, потом формат 1
    Если не найден, возвращает "en" (английский по умолчанию)
    
    Args:
        filename (str): Имя файла
        
    Returns:
        str: Языковой код в нижнем регистре
    """
    name_without_ext = Path(filename).stem
    
    # Формат 2: Сначала ищем паттерн customname_30s_en_1920x1080 
    # (длительность_язык_разрешение в конце имени)
    match_middle = re.search(r'_(\d+s)_([a-zA-Z]{2})_(\d+x\d+)$', name_without_ext)
    if match_middle:
        return match_middle.group(2).lower()  # Возвращаем языковой код
    
    # Формат 1: Только если не найден формат 2, ищем две буквы + подчеркивание в начале
    match_prefix = re.match(r'^([a-zA-Z]{2})_', name_without_ext)
    if match_prefix:
        return match_prefix.group(1).lower()
    
    # Если ни один паттерн не найден, используем английский по умолчанию
    return "en"


def format_duration(seconds):
    """
    Форматирует длительность в секундах как строку
    
    Args:
        seconds (int): Длительность в секундах
        
    Returns:
        str: Форматированная длительность (например, "90s")
    """
    return f"{seconds}s"


def generate_new_filename(custom_name, duration, lang_code, resolution):
    """
    Генерирует новое имя файла в формате: customname_90s_en_1080x1920.mp4
    
    Args:
        custom_name (str): Пользовательское имя
        duration (int): Длительность в секундах
        lang_code (str): Языковой код (строчными)
        resolution (str): Разрешение в формате "1920x1080"
        
    Returns:
        str: Новое имя файла
    """
    duration_str = format_duration(duration)
    new_name = f"{custom_name}_{duration_str}_{lang_code}_{resolution}.mp4"
    return new_name


def handle_duplicate_names(target_path):
    """
    Обрабатывает дубликаты имен, добавляя суффикс _1, _2, etc.
    
    Args:
        target_path (Path): Целевой путь файла
        
    Returns:
        Path: Уникальный путь файла
    """
    if not target_path.exists():
        return target_path
    
    base_name = target_path.stem
    extension = target_path.suffix
    parent_dir = target_path.parent
    
    counter = 1
    while True:
        new_name = f"{base_name}_{counter}{extension}"
        new_path = parent_dir / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def create_language_folder(lang_code):
    """
    Создает папку для языка (заглавными буквами)
    
    Args:
        lang_code (str): Языковой код
        
    Returns:
        Path: Путь к созданной папке
    """
    folder_name = lang_code.upper()
    folder_path = Path.cwd() / folder_name
    folder_path.mkdir(exist_ok=True)
    return folder_path


def organize_by_language(file_path, lang_code):
    """
    Перемещает файл в соответствующую языковую папку
    
    Args:
        file_path (Path): Путь к файлу
        lang_code (str): Языковой код
        
    Returns:
        Path: Новый путь файла
    """
    lang_folder = create_language_folder(lang_code)
    target_path = lang_folder / file_path.name
    target_path = handle_duplicate_names(target_path)
    
    file_path.rename(target_path)
    return target_path


def extract_duration_from_audio_name(filename):
    """
    Извлекает длительность из имени аудио файла
    Поддерживает форматы: 9s, 30s, 45sec, 90sec
    
    Args:
        filename (str): Имя аудио файла
        
    Returns:
        str или None: Маркер длительности или None если не найден
    """
    name_without_ext = Path(filename).stem
    # Ищем паттерн: цифры + s или sec
    match = re.search(r'(\d+(?:s|sec))', name_without_ext, re.IGNORECASE)
    
    if match:
        duration = match.group(1).lower()
        # Нормализуем формат (sec -> s)
        if duration.endswith('sec'):
            duration = duration.replace('sec', 's')
        return duration
    return None


def extract_duration_from_video_name(filename):
    """
    Извлекает длительность из имени видео файла
    
    Args:
        filename (str): Имя видео файла
        
    Returns:
        str или None: Маркер длительности или None если не найден
    """
    name_without_ext = Path(filename).stem
    # Ищем паттерн: цифры + s в имени видео
    match = re.search(r'(\d+s)', name_without_ext)
    
    if match:
        return match.group(1)
    return None


def find_audio_files():
    """
    Находит все .wav файлы в текущей папке и извлекает их длительности
    
    Returns:
        dict: {duration: [audio_files_list]} или {None: [audio_files_list]}
    """
    current_dir = Path.cwd()
    wav_files = list(current_dir.glob("*.wav"))
    
    audio_by_duration = {}
    
    for wav_file in wav_files:
        duration = extract_duration_from_audio_name(wav_file.name)
        
        if duration not in audio_by_duration:
            audio_by_duration[duration] = []
        audio_by_duration[duration].append(wav_file)
    
    return audio_by_duration


def find_video_files_in_subfolders():
    """
    Находит все видео файлы в подпапках и группирует по длительности
    
    Returns:
        dict: {duration: [video_files_list]} или {None: [video_files_list]}
    """
    current_dir = Path.cwd()
    video_files = []
    
    # Ищем .mp4 файлы во всех подпапках
    for subfolder in current_dir.iterdir():
        if subfolder.is_dir():
            video_files.extend(list(subfolder.glob("*.mp4")))
    
    video_by_duration = {}
    
    for video_file in video_files:
        duration = extract_duration_from_video_name(video_file.name)
        
        if duration not in video_by_duration:
            video_by_duration[duration] = []
        video_by_duration[duration].append(video_file)
    
    return video_by_duration


def check_ffmpeg():
    """
    Проверяет наличие ffmpeg в системе
    
    Returns:
        bool: True если ffmpeg доступен, False иначе
    """
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def create_backup_folder(video_path):
    """
    Создает структуру папок backup на уровень выше языковых папок
    
    Args:
        video_path (Path): Путь к видео файлу
        
    Returns:
        Path: Путь к соответствующей папке в backup
    """
    # Определяем основную папку (где находятся языковые папки)
    main_dir = video_path.parent.parent  # Если видео в EN/, то main_dir = testfield/
    lang_folder_name = video_path.parent.name  # Название языковой папки (EN, RU, etc.)
    
    # Создаем структуру backup/EN/, backup/RU/, etc.
    backup_main_dir = main_dir / "backup"
    backup_lang_dir = backup_main_dir / lang_folder_name
    
    backup_lang_dir.mkdir(parents=True, exist_ok=True)
    return backup_lang_dir


def merge_audio_video(video_path, audio_path):
    """
    Заменяет аудио в видео файле через FFmpeg (быстрее чем moviepy)
    Сохраняет оригинальный файл в папку backup, затем заменяет на новый
    
    Args:
        video_path (Path): Путь к видео файлу (будет заменен)
        audio_path (Path): Путь к аудио файлу  
        
    Returns:
        bool: True если успешно, False при ошибке
    """
    temp_path = None
    
    try:
        # Создаем временный файл в той же папке что и видео (на том же диске)
        video_dir = video_path.parent
        with tempfile.NamedTemporaryFile(suffix='.mp4', dir=str(video_dir), delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        # Команда ffmpeg для замены аудио в видео
        cmd = [
            'ffmpeg',
            '-i', str(video_path),      # Входное видео
            '-i', str(audio_path),      # Входное аудио
            '-c:v', 'copy',             # Копировать видео без перекодирования
            '-c:a', 'aac',              # Кодировать аудио в AAC
            '-map', '0:v:0',            # Взять видео из первого файла
            '-map', '1:a:0',            # Взять аудио из второго файла
            '-y',                       # Перезаписать выходной файл если существует
            str(temp_path)
        ]
        
        # Выполняем команду ffmpeg
        result = subprocess.run(cmd, 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL,
                              check=True)
        
        # Создаем соответствующую папку backup
        backup_dir = create_backup_folder(video_path)
        
        # Путь для backup
        backup_path = backup_dir / video_path.name
        
        # Если backup уже существует - НЕ ТРОГАЕМ его (сохраняем первый оригинал)
        if backup_path.exists():
            # Просто удаляем текущий файл и ставим новый
            video_path.unlink()
            shutil.move(str(temp_path), str(video_path))
        else:
            # Backup не существует - сохраняем оригинал
            shutil.move(str(video_path), str(backup_path))  # Оригинал в backup
            shutil.move(str(temp_path), str(video_path))     # Новый файл на место оригинала
        
        return True
        
    except subprocess.CalledProcessError as e:
        # Удаляем временный файл при ошибке
        if temp_path and temp_path.exists():
            temp_path.unlink()
        print(f"FFmpeg ошибка при обработке {video_path.name}")
        return False
    except Exception as e:
        # Удаляем временный файл при ошибке
        if temp_path and temp_path.exists():
            temp_path.unlink()
        print(f"Ошибка при обработке {video_path.name}: {e}")
        return False


def sound_merge_mode():
    """
    Режим сшивания звука с видео
    """
    print("=== Sound Merge - Сшивание звука с видео ===")
    
    # Проверяем наличие ffmpeg
    if not check_ffmpeg():
        print("❌ ОШИБКА: FFmpeg не найден в системе!")
        print("Установите FFmpeg и добавьте его в PATH:")
        print("https://ffmpeg.org/download.html")
        return
    
    print("✅ FFmpeg найден")
    print("Поиск .wav файлов в текущей папке...")
    print("Поиск .mp4 файлов в подпапках...\n")
    
    # Находим аудио и видео файлы
    audio_by_duration = find_audio_files()
    video_by_duration = find_video_files_in_subfolders()
    
    if not audio_by_duration:
        print("❌ Не найдено .wav файлов в текущей папке!")
        return
    
    if not video_by_duration:
        print("❌ Не найдено .mp4 файлов в подпапках!")
        return
    
    total_audio = sum(len(files) for files in audio_by_duration.values())
    total_video = sum(len(files) for files in video_by_duration.values())
    
    print(f"Найдено аудио файлов: {total_audio}")
    print(f"Найдено видео файлов: {total_video}")
    
    # Определяем логику сшивания
    audio_durations = [d for d in audio_by_duration.keys() if d is not None]
    
    processed_count = 0
    
    if len(audio_durations) == 0:
        # Все аудио без маркера длительности - сшиваем со всеми видео
        audio_files = audio_by_duration[None]
        all_videos = []
        for video_list in video_by_duration.values():
            all_videos.extend(video_list)
            
        for audio_file in audio_files:
            for video_file in all_videos:
                if merge_audio_video(video_file, audio_file):
                    processed_count += 1
                    
    elif len(audio_durations) == 1 and None not in audio_by_duration:
        # Один аудио с маркером - сшиваем с соответствующими видео + без маркера
        duration = audio_durations[0]
        audio_files = audio_by_duration[duration]
        
        target_videos = video_by_duration.get(duration, [])
        if None in video_by_duration:
            target_videos.extend(video_by_duration[None])
            
        for audio_file in audio_files:
            for video_file in target_videos:
                if merge_audio_video(video_file, audio_file):
                    processed_count += 1
                    
    else:
        # Множественные аудио с маркерами - строгое соответствие
        for duration in audio_durations:
            audio_files = audio_by_duration[duration]
            video_files = video_by_duration.get(duration, [])
            
            for audio_file in audio_files:
                for video_file in video_files:
                    if merge_audio_video(video_file, audio_file):
                        processed_count += 1
    
    print(f"\n=== ИТОГИ СШИВАНИЯ ===")
    print(f"✅ Заменено аудио в {processed_count} видео файлах")
    print("📦 Оригинальные файлы сохранены в папки backup/")
    print("🎵 Файлы обновлены с новым звуком!")
    print("Готово!")


def video_rename_mode():
    """
    Режим переименования видео файлов
    """
    print("=== Переименователь видео файлов ===")
    print("Формат: customname_90s_en_1080x1920.mp4")
    print("Сортировка по папкам: EN, RU, SC, KR, etc.\n")
    
    # Получаем пользовательское имя
    custom_name = input("Введите пользовательское имя для файлов: ").strip()
    if not custom_name:
        print("Ошибка: Необходимо ввести имя!")
        return
    
    # Находим все .mp4 файлы в текущей папке
    current_dir = Path.cwd()
    mp4_files = list(current_dir.glob("*.mp4"))
    
    if not mp4_files:
        print("В текущей папке не найдено .mp4 файлов!")
        return
    
    # Фильтруем файлы с WIP в имени
    filtered_files = []
    wip_count = 0
    
    for video_file in mp4_files:
        if "WIP" in video_file.name.upper():
            wip_count += 1
        else:
            filtered_files.append(video_file)
    
    print(f"Найдено {len(mp4_files)} .mp4 файлов")
    if wip_count > 0:
        print(f"⏸️  Пропущено WIP файлов: {wip_count}")
    print(f"К обработке: {len(filtered_files)} файлов")
    print("Обрабатываю файлы...")
    
    processed_count = 0
    error_count = 0
    languages_found = set()
    
    for video_file in filtered_files:
        # Извлекаем языковой префикс
        lang_code = extract_language_prefix(video_file.name)
        languages_found.add(lang_code.upper())
        
        # Получаем метаданные видео
        resolution, duration = get_video_metadata(str(video_file))
        
        if resolution is None or duration is None:
            error_count += 1
            continue
        
        # Генерируем новое имя
        new_filename = generate_new_filename(custom_name, duration, lang_code, resolution)
        
        # Переименовываем файл
        new_path = video_file.parent / new_filename
        new_path = handle_duplicate_names(new_path)
        
        try:
            video_file.rename(new_path)
            
            # Перемещаем в языковую папку
            final_path = organize_by_language(new_path, lang_code)
            
            processed_count += 1
            
        except Exception as e:
            error_count += 1
    
    print("\n=== ИТОГИ ОБРАБОТКИ ===")
    print(f"✅ Успешно обработано: {processed_count} файлов")
    if error_count > 0:
        print(f"❌ Ошибок: {error_count}")
    if languages_found:
        print(f"📁 Созданы папки: {', '.join(sorted(languages_found))}")
    print("Готово!")


def drag_drop_mode(files):
    """
    Режим drag & drop - быстрое сшивание звука с видео
    
    Args:
        files (list): Список путей к перетащенным файлам
    """
    print("=== DRAG & DROP MODE - Быстрое сшивание ===")
    
    # Проверяем наличие ffmpeg
    if not check_ffmpeg():
        print("❌ ОШИБКА: FFmpeg не найден в системе!")
        print("Установите FFmpeg и добавьте его в PATH:")
        print("https://ffmpeg.org/download.html")
        return
    
    # Разделяем файлы на аудио и видео
    audio_files = []
    video_files = []
    
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            print(f"⚠️ Файл не найден: {file_path}")
            continue
            
        if path.suffix.lower() == '.wav':
            audio_files.append(path)
        elif path.suffix.lower() == '.mp4':
            video_files.append(path)
        else:
            print(f"⚠️ Неподдерживаемый формат: {path.name}")
    
    print(f"Найдено аудио файлов: {len(audio_files)}")
    print(f"Найдено видео файлов: {len(video_files)}")
    
    # Проверяем условия drag & drop
    if len(audio_files) != 1:
        print("❌ ОШИБКА: Нужен ровно 1 аудио файл (.wav)")
        print("Перетащите ровно 1 .wav файл и 1 или более .mp4 файлов")
        return
    
    if len(video_files) < 1:
        print("❌ ОШИБКА: Нужен минимум 1 видео файл (.mp4)")  
        print("Перетащите ровно 1 .wav файл и 1 или более .mp4 файлов")
        return
    
    audio_file = audio_files[0]
    print(f"🎵 Аудио: {audio_file.name}")
    print(f"🎬 Видео файлов: {len(video_files)}")
    
    # Создаем папку sound в том же месте где аудио файл
    sound_dir = audio_file.parent / "sound"
    sound_dir.mkdir(exist_ok=True)
    print(f"📁 Создана папка: {sound_dir}")
    
    processed_count = 0
    
    for video_file in video_files:
        print(f"Обрабатываю: {video_file.name}")
        
        # Путь для результата в папке sound
        output_path = sound_dir / video_file.name
        output_path = handle_duplicate_names(output_path)
        
        try:
            # Команда ffmpeg для сшивания
            cmd = [
                'ffmpeg',
                '-i', str(video_file),      # Входное видео
                '-i', str(audio_file),      # Входное аудио
                '-c:v', 'copy',             # Копировать видео без перекодирования
                '-c:a', 'aac',              # Кодировать аудио в AAC
                '-map', '0:v:0',            # Взять видео из первого файла
                '-map', '1:a:0',            # Взять аудио из второго файла
                    '-y',                       # Перезаписать выходной файл если существует
                str(output_path)
            ]
            
            # Выполняем команду ffmpeg
            result = subprocess.run(cmd, 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL,
                                  check=True)
            
            processed_count += 1
            print(f"✅ {video_file.name} → sound/{output_path.name}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка при обработке {video_file.name}")
    
    print(f"\n=== ИТОГИ DRAG & DROP ===")
    print(f"✅ Успешно обработано: {processed_count} видео")
    print(f"📁 Результаты в папке: {sound_dir}")
    print("Готово!")


def main():
    """
    Главная функция с выбором режима работы
    """
    # Проверяем, есть ли аргументы командной строки (drag & drop через .bat файл)
    if len(sys.argv) > 1:
        # Режим drag & drop
        files = sys.argv[1:]  # Все аргументы кроме имени скрипта
        try:
            drag_drop_mode(files)
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            print("Детали ошибки:")
            import traceback
            traceback.print_exc()
        return
    
    # Обычный режим работы
    print("=== ВИДЕО УТИЛИТЫ ===")
    print("1. Переименователь видео файлов")
    print("2. Sound Merge - Сшивание звука с видео")
    print("💡 Для drag & drop используйте video_renamer.bat")
    
    while True:
        choice = input("\nВыберите функцию (1/2): ").strip()
        
        if choice == "1":
            video_rename_mode()
            break
        elif choice == "2":
            sound_merge_mode()
            break
        else:
            print("❌ Некорректный выбор. Введите 1 или 2.")


if __name__ == "__main__":
    main()