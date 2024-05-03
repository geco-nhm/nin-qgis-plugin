chcp 65001
REM Endrer codepage for å vise norske tegn som æ, ø og å.
REM http://home.hit.no/programmering/start/dos.php
REM http://ss64.com/nt/chcp.html

REM Setlocal EnableDelayedExpansion

@echo off
REM http://www.qgistutorials.com/en/docs/running_qgis_jobs.html
REM call "C:\OSGeo4W\bin"\o4w_env.bat
REM NB Med dette oppsettet kjøres Python 3.9
SET OSGEO4W_ROOT=C:\OSGeo4W
SET QGISNAME=qgis
SET QGIS=%OSGEO4W_ROOT%\apps\%QGISNAME%
REM REM Gdal Setup
set GDAL_DATA=%OSGEO4W_ROOT%\share\gdal\
REM REM To find proj.db
REM set PROJ_LIB=%OSGEO4W_ROOT%\share\proj\
REM Python Setup
set PATH=%OSGEO4W_ROOT%\bin;%QGIS%\bin;%PATH%
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python39
set PYTHONPATH=%QGIS%\python;%PYTHONPATH%
REM REM REM For riktig PyQt med dll-er
REM REM call C:\OSGeo4W\bin\qt5_env.bat
SET PGCLIENTENCODING=utf-8

if exist fugleregistrering.gpkg del fugleregistrering.gpkg
if exist ..\kode\fugl_feltarbeidere_inf.csv del ..\kode\fugl_feltarbeidere_inf.csv

REM echo 1 Lager n5hoyde-tabell for flatene som skal besøkes
REM call psql -h db04.int.nibio.no -d sl -U sl_ban -f .\kode\create_table_fugler_n5hoyder.sql
REM echo:
REM echo 2 Lager 3qflater-tabell for flatene som skal besøkes (BRUKES IKKE)
REM call psql -h db04.int.nibio.no -d sl -U sl_ban -f .\kode\create_table_fugler_3qflater.sql
REM echo:

REM ".\" is a sub-folder of the current working directory
REM ".." is one level higher
REM https://ss64.com/nt/rd.html
REM Bruker "%%a" for å få med flere flater f.eks 2171 2127
echo 1 Lager fugleregistrering.gpkg
call python ..\kode\create_gpkg.py
echo:
REM input i sql er antall feltarbeider = antall tilfeldige tall mellom 1000 og 1000 som skal genereres
echo 2 Lager tabell med informasjon om feltarbeidere og deres flater
call psql -h db04.int.nibio.no -U org_treqbm -d sl -f ..\kode\create_table_fugl_kode_feltarbeidere.sql -v ant=3
echo
echo 3 Lager QGIS-prosjekt
for /F "tokens=4,6 delims=; skip=1" %%a in (..\kode\fugl_feltarbeidere_inf.csv) do (
  echo flater er %%a  
  echo bruker er %%b  
  python ..\kode\create_project.py "%%a" %%b
)

pause