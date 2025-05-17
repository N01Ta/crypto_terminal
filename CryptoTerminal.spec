# CryptoTerminal.spec (или proj.spec)
# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Функция для получения корректного пути к ресурсам (для режима onefile)
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Если запускается не из PyInstaller bundle (например, в режиме разработки)
        # Используем SPECPATH для определения пути к директории .spec файла
        base_path = SPECPATH # <--- ИЗМЕНЕНИЕ ЗДЕСЬ
    return os.path.join(base_path, relative_path)

# Определяем базовый путь к проекту (где лежит .spec файл)
# Используем переменную SPECPATH, предоставляемую PyInstaller
BASE_DIR = SPECPATH  # <--- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ

# Список данных для включения в сборку: (исходный_путь, путь_внутри_распакованного_exe)
added_datas = [
    (os.path.join(BASE_DIR, '.env'), '.')
]

# Скрытые импорты
hidden_imports_list = [
    'pyqt5.sip',
    'dotenv',
    'pkg_resources.py2_warn',
    # 'pandas', 'numpy', # Если нужны
]

a = Analysis(
    [os.path.join(BASE_DIR, 'src', 'main_app.py')],
    pathex=[os.path.join(BASE_DIR, 'src'), BASE_DIR],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports_list,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CryptoTerminal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # Попробуйте False, если UPX вызывает проблемы
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)