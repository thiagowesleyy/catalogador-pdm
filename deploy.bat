@echo off
echo ========================================
echo   CATALOGADOR-PDM — Deploy para GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo [0/5] Removendo .git anterior corrompido...
rmdir /s /q .git 2>nul
echo     OK

echo [1/5] Inicializando git...
git init -b main
echo     OK

echo [2/5] Configurando usuario...
git config user.name "thiagowesleyy"
git config user.email "thiagowesleyy@gmail.com"
echo     OK

echo [3/5] Adicionando arquivos...
git add .
echo     OK

echo [4/5] Criando commit...
git commit -m "feat: inicial - catalogador PDM"
echo     OK

echo [5/5] Enviando para GitHub...
git remote add origin https://github.com/thiagowesleyy/catalogador-pdm.git
git push -u origin main
echo     OK

echo.
echo ========================================
echo   Concluido! Verifique acima se deu OK.
echo ========================================
pause
