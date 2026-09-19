import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), "tests"))
import test_v9_real_trip_operations as T
from app.db.models import Activity, Commitment
from app.db.session import SessionLocal
from sqlalchemy import select
# rerun the happy path but stop before select
client = T.client
