'''
PyInstaller spec file for Local Automator (onefile build)
'''

import os

# The directory containing this spec file, which is the project root.
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))

a = Analysis(
    [os.path.join(spec_dir, 'src', 'main.py')],
    pathex=[spec_dir],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'src.actions.file_actions',
        'src.actions.command_actions',
        'src.actions.variable_actions',
        'src.actions.condition_actions',
        'src.actions.trigger_actions',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# For a one-file build, all dependencies are bundled into the EXE object.
# There is no COLLECT object.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='LocalAutomator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,  # Create a windowed (GUI) app
    icon=None,
)
