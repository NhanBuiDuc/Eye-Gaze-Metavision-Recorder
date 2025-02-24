from PyInstaller.__main__ import run
args = [
    '--clean',
    '--noconfirm',
    '--onedir',
    '--paths', r'D:\Prophesee\Prophesee\lib\python3\site-packages',
    '--add-data', r'D:\Prophesee\Prophesee\bin\*.dll;.',
    '--add-data', r'D:\Prophesee\Prophesee\lib\*.dll;.',
    '--hidden-import', 'metavision_core',
    '--hidden-import', 'metavision_sdk_base',
    '--hidden-import', 'metavision_sdk_ui',
    '--hidden-import', 'metavision_sdk_core',
    '--hidden-import', 'metavision_hal',
    '--hidden-import', 'metavision_API',
    '--hidden-import', 'cv2',
    '--hidden-import', 'numpy',
    '--hidden-import', 'pandas',
    'main.py'
]
run(args)
