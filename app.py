import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
import os
import redis
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "notes")
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(64), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
        }


app = Flask(__name__)
app.json.ensure_ascii = False

@app.get("/")
def hello():
    return "Hello"


@app.post("/note")
def add_note():
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()

    if not content:
        return jsonify({"error": "Поле 'content' обязательно"}), 400
    if len(content) > 64:
        return jsonify({"error": "Длина строки не должна превышать 64 символа"}), 400

    with SessionLocal() as session:
        note = Note(content=content)
        session.add(note)
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            return jsonify({"error": str(e)}), 500

        try:
            total = redis_client.incr("notes_count")
        except redis.RedisError:
            total = None

        response = note.to_dict()
        if total is not None:
            response["notes_count"] = total
        return jsonify(response), 201


@app.get("/notes")
def get_all_notes():
    with SessionLocal() as session:
        notes = session.query(Note).all()
        return jsonify([el.to_dict() for el in notes])


@app.get("/note/<int:note_id>")
def get_note(note_id: int):
    with SessionLocal() as session:
        note = session.get(Note, note_id)
        if note:
            return jsonify(note.to_dict())
        return jsonify({"error": f"Нет заметки с id = {note_id}"}), 404


@app.get("/notes_count")
def stats():
    try:
        total = redis_client.get("notes_count")
        return jsonify({"notes_count": int(total) if total else 0})
    except redis.RedisError as e:
        return jsonify({"error": f"Redis недоступен: {e}"}), 503


@app.get("/health")
def health():
    result = {"status": "ok", "db": "ok", "redis": "ok"}
    status_code = 200
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as e:
        result["db"] = f"error: {e}"
        result["status"] = "degraded"
        status_code = 503
    try:
        redis_client.ping()
    except redis.RedisError as e:
        result["redis"] = f"error: {e}"
        result["status"] = "degraded"
        status_code = 503

    return jsonify(result), status_code


def init_count():
    with SessionLocal() as session:
        count = session.query(Note).count()
        redis_client.set("notes_count", count)


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)