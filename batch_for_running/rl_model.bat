@Echo off
call "%HOMEPATH%\Anaconda3\Scripts\activate.bat" py37_64
call python "%~dp0/../main_rl_trader.py" %1 %2
