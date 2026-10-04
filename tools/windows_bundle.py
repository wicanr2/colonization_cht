"""規格042：Windows ZIP組裝與共用啟動旗標。"""

import copy
import hashlib
import io
import json
import shlex
import stat
import zipfile
from pathlib import PurePosixPath


def windows_launcher(source):
    tokens = shlex.split(source.split('\nexec ', 1)[1].replace('\\\n', ' '))
    if tokens[0] != '$here/bin/colonization-window' or tokens[-1] != '${args[@]}':
        raise ValueError('Linux啟動器的命令結構已改變')
    required = {'--window', '--play', '--all-menu', '--dialog-a', '--string-a', '--audio', '--sb-digital'}
    if not required <= set(tokens):
        raise ValueError('完整中文或音訊旗標缺失')
    replacements = {'$here/bin/colonization-window': '%here%bin/colonization-window.exe',
                    '$game': '%game%', '$save': '%save%', '$m': '%m%', '$t': '%t%'}
    command = []
    for token in tokens[:-1]:
        original = token
        for old, new in replacements.items():
            token = token.replace(old, new)
        if '$' in token or '"' in token or '\n' in token:
            raise ValueError('Windows啟動參數無法安全轉換：' + original)
        if original.startswith('$'):
            token = token.replace('/', '\\')
        token.encode('ascii')
        command.append('"' + token + '"')
    native = ' ^\n  '.join(command) + ' %args%\n'
    script = '''@echo off
setlocal DisableDelayedExpansion
set "here=%~dp0"
set "game="
set "args="
:parse
if "%~1"=="" goto ready
if /i "%~1"=="--game" goto game_value
if /i "%~1"=="--help" goto help
if /i "%~1"=="-h" goto help
if /i "%~2"=="false" goto false_value
if /i "%~2"=="true" goto true_value
set args=%args% %1
shift
goto parse
:false_value
set args=%args% "%~1=false"
shift
shift
goto parse
:true_value
set args=%args% "%~1=true"
shift
shift
goto parse
:game_value
if "%~2"=="" goto missing_game
set "game=%~2"
shift
shift
goto parse
:ready
if not defined game goto missing_game
if not exist "%game%\\VICEROY.EXE" goto missing_game
set "save=%COLONIZATION_CHT_SAVE%"
if defined save goto save_ready
if not defined LOCALAPPDATA goto missing_profile
set "save=%LOCALAPPDATA%\\colonization-cht\\save"
:save_ready
if exist "%save%\\" goto invoke
mkdir "%save%"
if errorlevel 1 exit /b 1
:invoke
set "m=%here%masks"
set "t=%here%text"
@COMMAND@
set "status=%errorlevel%"
exit /b %status%
:missing_game
echo Use --game with the original COLONIZE directory containing VICEROY.EXE. 1>&2
exit /b 2
:missing_profile
echo Set COLONIZATION_CHT_SAVE or LOCALAPPDATA to a writable directory. 1>&2
exit /b 2
:help
echo Usage: colonization-cht.bat --game "C:\\path\\COLONIZE" [frontend arguments]
echo See README.txt for Traditional Chinese instructions and save locations.
exit /b 0
'''.replace('@COMMAND@\n', native)
    return script.replace('\n', '\r\n').encode('ascii')


def build_windows_zip(files, manifest, top, linux_launcher):
    payload = dict(files)
    payload.pop('MANIFEST.json', None)
    payload.pop('colonization-cht.sh', None)
    payload['colonization-cht.bat'] = (windows_launcher(linux_launcher), 0o755)
    readme = payload['README.txt'][0].decode('utf-8-sig').replace('\r\n', '\n')
    payload['README.txt'] = (readme.replace('\n', '\r\n').encode('utf-8-sig'), 0o644)
    bundled = copy.deepcopy(manifest)
    bundled['format'] = 'Windows-ZIP'
    bundled['launcher_source_sha256'] = hashlib.sha256(linux_launcher.encode()).hexdigest()
    bundled['zip_timestamp'] = '1980-01-01T00:00:00'
    bundled['files'] = {name: {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                        for name, (data, mode) in sorted(payload.items())}
    payload['MANIFEST.json'] = ((json.dumps(bundled, ensure_ascii=False, indent=1, sort_keys=True) + '\n').encode(), 0o644)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, (data, mode) in sorted(payload.items()):
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('非法包內路徑：' + name)
            entry = zipfile.ZipInfo(top + '/' + name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | mode) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data, compresslevel=9)
    return output.getvalue(), bundled
