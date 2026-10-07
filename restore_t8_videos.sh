#!/bin/bash

GAME_ROOT="$HOME/games/Games/TEKKEN 8/TEKKEN 8"
PAK_DIR="$GAME_ROOT/Polaris/Content/Paks"
UNPACKED_MOVIES_DIR="$GAME_ROOT/Polaris/Content/Movies/usm"

BACKUP_DIR="$PAK_DIR/backup_original"
UNPACKED_BACKUP="/home/dis/games/Games/TEKKEN 8/backup_original_usm"
log_info() { echo -e "\e[34m[RESTORE]\e[0m $1"; }
log_warn() { echo -e "\e[33m[WARN]\e[0m $1"; }
log_error() { echo -e "\e[31m[ERROR]\e[0m $1" >&2; }

echo "=== Запуск точечного восстановления по карте оригинала ==="

# 1. Восстановление внешних .usm файлов из плоского бэкапа
if [ -d "$UNPACKED_BACKUP" ]; then
    log_info "Сканирование структуры игры для восстановления внешних видео..."
    
    # Рекурсивно ищем все файлы .usm в игровом каталоге (включая все подпапки)
    while IFS= read -r -d '' target_file; do
        [ -z "$target_file" ] && continue
        
        # Пропускаем файлы, которые находятся внутри самой папки бэкапа
        [[ "$target_file" == */backup_original_usm/* ]] && continue
        
        filename=$(basename "$target_file")
        backup_file="$UNPACKED_BACKUP/$filename"
        
        # Если такой файл существует в плоском бэкапе, восстанавливаем его
        if [ -f "$backup_file" ]; then
            log_info "   Восстановление в подпапку: ${target_file#$UNPACKED_MOVIES_DIR/}"
            
            # Удаляем заглушку и перемещаем оригинал на его законное место в структуре
            rm -f "$target_file"
            mv "$backup_file" "$target_file"
        fi
    done < <(find "$UNPACKED_MOVIES_DIR" -type f -name "*.usm" -print0 2>/dev/null)
    
    # Удаляем папку бэкапа, если она опустела
    #rm -rf "$UNPACKED_BACKUP" 2>/dev/null
    log_info "Внешние видео успешно возвращены в свои папки."
else
    log_warn "Папка плоского бэкапа внешних видео (.usm) не обнаружена."
fi

# 2. Восстановление оригинальных контейнеров .pak
if [ -d "$BACKUP_DIR" ]; then
    log_info "--------------------------------------------------"
    log_info "Возврат оригинальных .pak контейнеров..."
    
    while IFS= read -r -d '' pak_backup; do
        [ -z "$pak_backup" ] && continue
        base_name=$(basename "${pak_backup%.*}")
        
        if [ -f "$BACKUP_DIR/$base_name.ucas" ]; then
            log_info "   Восстановление контейнера: $base_name"
            rm -f "$PAK_DIR/$base_name.pak" "$PAK_DIR/$base_name.ucas" "$PAK_DIR/$base_name.utoc"
            mv "$BACKUP_DIR/$base_name."* "$PAK_DIR/" 2>/dev/null
        fi
    done < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name "*.pak" -print0 2>/dev/null)
    
    #rm -rf "$BACKUP_DIR" 2>/dev/null
    log_info "Оригинальные контейнеры паков восстановлены."
fi

echo "=== Восстановление полностью завершено! ==="
