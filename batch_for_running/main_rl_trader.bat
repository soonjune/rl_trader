@Echo off
call "C:\Users\Twoyak-1\anaconda3\Scripts\activate.bat" py37_64
call python "%~dp0\..\main_rl_trader.py" %1 %2
