pgrep "mpv" | xargs kill -9
mpv --idle --input-ipc-server=/tmp/mpvsocket &
LC_NUMERIC=C python3 ./start_boris.py
