import time
import psutil
from pathlib import Path
import re


STEAM_PATH = Path("D:/Steam")   # Здесь находится наш путь (в данном случае мой)
STEAM_LOG_PATH = STEAM_PATH / "logs" / "content_log.txt"

INTERVAL = 60
CHECKS_COUNT = 5

STEAM_PROCESS_NAME = "steam.exe"


def find_steam_process():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and STEAM_PROCESS_NAME.lower() in proc.info['name'].lower():
            return proc
    return None


def read_last_lines(path, n=80):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()[-n:]


def get_appid_from_logs(lines):
    for line in reversed(lines):
        match = re.search(r'AppID\s+(\d+)', line)
        if match:
            return match.group(1)
    return None


def get_game_name(app_id):
    manifest_path = STEAM_PATH / "steamapps" / f"appmanifest_{app_id}.acf"

    if not manifest_path.exists():
        return None

    with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if '"name"' in line:
                return line.split('"')[3]

    return None


def get_io(process):
    io = process.io_counters()
    return io.read_bytes + io.write_bytes


def main():
    steam_proc = find_steam_process()

    if not steam_proc:
        print("Steam не запущен")
        return

    print("Происходит мониторинг загрузок Steam\n")

    previous_io = get_io(steam_proc)

    for minute in range(1, CHECKS_COUNT + 1):
        time.sleep(INTERVAL)

        current_io = get_io(steam_proc)
        diff_mb = (current_io - previous_io) / (1024 * 1024)
        speed_mb_s = diff_mb / INTERVAL
        speed_mb_min = diff_mb
        previous_io = current_io

        log_lines = read_last_lines(STEAM_LOG_PATH)
        app_id = get_appid_from_logs(log_lines)

        game_name = None
        if app_id:
            game_name = get_game_name(app_id)

        if diff_mb > 1:
            status = "Загрузка активна"
        else:
            status = "Загрузка неактивна или на паузе"

        print("------")
        print(f"Минута {minute}")
        print(f"Передано данных: {diff_mb:.2f} МБ")
        print(f"Скорость загрузки: {speed_mb_s:.2f} МБ/с ({speed_mb_min:.2f} МБ/мин)")

        if app_id:
            if game_name:
                print(f"Игра: {game_name} (AppID: {app_id})")
            else:
                print(f"Игра: AppID {app_id} (название не найдено локально)")
        else:
            print("Игра не определена")

        print(f"Статус: {status}")

    print("\nМониторинг завершён.")


if __name__ == "__main__":
    main()