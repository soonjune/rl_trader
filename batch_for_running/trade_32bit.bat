@Echo off
@Echo trade_32bit Start
set x=0
call "C:\Users\Twoyak-1\anaconda3\Scripts\activate.bat" py37_32

:repeat
@tasklist | find "python.exe" /c > NUL

start python "%~dp0\..\trade_32bit.py"
timeout 5 > NUL
goto repeat
