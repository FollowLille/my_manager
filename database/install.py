import sqlite3 as sq
import os

# инициализируем базу и запускаем все скрипты
default_scripts = os.listdir(r'./scripts')
conn = sq.connect('test_db.db')
for script_name in default_scripts:
    with open(r'./scripts/' + script_name) as file:
        script = file.read()
        conn.cursor().execute(script)
        conn.commit()
conn.close()
