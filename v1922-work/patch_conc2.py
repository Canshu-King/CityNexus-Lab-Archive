from pathlib import Path
P = Path("D:/moodle/CityNexus/backend/app/main.py")
s = P.read_text(encoding="utf-8")
s = s.replace("from sqlalchemy.exc import OperationalError", "from sqlalchemy.exc import IntegrityError, OperationalError", 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
