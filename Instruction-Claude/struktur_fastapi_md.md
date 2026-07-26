# CLAUDE.md — Panduan Pengembangan FastAPI (Referensi: tuturkata-api)

File ini menjadi referensi utama untuk membuat project FastAPI baru mengikuti konvensi yang sama dengan `tuturkata-api`. Baca file ini sebelum mulai coding — tidak perlu buka folder `tuturkata-api` lagi.

---

## Daftar Isi
1. [Struktur Folder Project](#struktur-folder-project)
2. [Urutan Setup Project Baru](#urutan-setup-project-baru)
3. [Urutan Pembuatan Endpoint Baru](#urutan-pembuatan-endpoint-baru)
4. [Pola Kode: Config](#pola-kode-config)
5. [Pola Kode: Model (SQLAlchemy ORM)](#pola-kode-model-sqlalchemy-orm)
6. [Pola Kode: Alembic Migration](#pola-kode-alembic-migration)
7. [Pola Kode: Schemas (Pydantic)](#pola-kode-schemas-pydantic)
8. [Pola Kode: Service (Business Logic)](#pola-kode-service-business-logic)
9. [Pola Kode: Auth Service](#pola-kode-auth-service)
10. [Pola Kode: Router](#pola-kode-router)
11. [Pola Kode: Seeder](#pola-kode-seeder)
12. [Pola Kode: main.py](#pola-kode-mainpy)
13. [Konvensi Umum](#konvensi-umum)

---

## Struktur Folder Project

```
nama-project-api/
├── app/                          # Kode utama aplikasi
│   ├── config/
│   │   ├── config.py            # Environment variables (DB, JWT, dll)
│   │   └── database.py          # SQLAlchemy engine, session, Base, get_db
│   ├── model/                   # SQLAlchemy ORM models (1 file per tabel)
│   │   └── user.py
│   ├── schemas/                 # Pydantic request/response models (1 file per domain)
│   │   └── user.py
│   ├── service/                 # Business logic (1 file per domain)
│   │   ├── auth.py             # JWT + password hashing + get_current_user
│   │   └── user_service.py
│   ├── router/                  # FastAPI route handlers (1 file per domain)
│   │   └── router_user.py
│   ├── utils/
│   │   └── time.py             # wib_now() — waktu WIB (UTC+7)
│   └── main.py                  # FastAPI app init, CORS, router includes
├── alembic/
│   ├── env.py                   # Konfigurasi alembic (baca .env, import Base)
│   └── versions/                # File-file migrasi database
│       └── xxxx_create_xxx_table.py
├── seeder/                      # Script pengisian data awal
│   ├── __init__.py
│   ├── seed_all.py             # Master seeder (jalankan semua seeder)
│   └── seed_xxx.py             # Seeder per domain
├── media/                       # File statis (audio upload, TTS output)
│   ├── uploads/
│   └── tts/
├── alembic.ini                  # Konfigurasi alembic
├── requirement.txt              # Python dependencies
├── .env                         # Environment variables (tidak di-commit)
└── .gitignore
```

**Aturan nama file:**
- Model: `app/model/nama_entitas.py` (snake_case)
- Schema: `app/schemas/nama_entitas.py`
- Service: `app/service/nama_entitas_service.py`
- Router: `app/router/router_nama_entitas.py`
- Seeder: `seeder/seed_nama_entitas.py`

---

## Urutan Setup Project Baru

### 1. Buat Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```bash
pip install "fastapi[all]"
pip install sqlalchemy
pip install alembic
pip install psycopg2
pip install python-dotenv
pip install passlib[bcrypt]
pip install python-jose[cryptography]
```

### 3. Buat file `.env`
```
SQLALCHEMY_DATABASE_URL=postgresql://postgres:admin@localhost:5433/fastapi_namaproject_api
DB_PASS=admin
DB_NAME=fastapi_namaproject_api
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=ganti_ini_dengan_secret_panjang
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 4. Buat `app/config/config.py` dan `app/config/database.py`
(Lihat seksi [Pola Kode: Config](#pola-kode-config))

### 5. Buat `app/utils/time.py`
(Lihat seksi [Konvensi Umum](#konvensi-umum))

### 6. Init Alembic
```bash
alembic init alembic
```

### 7. Edit `alembic.ini`
Cukup pastikan baris `sqlalchemy.url` ada (nilainya akan di-override oleh `env.py`):
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

### 8. Edit `alembic/env.py`
(Lihat seksi [Pola Kode: Alembic Migration](#pola-kode-alembic-migration))

### 9. Buat `app/main.py`
(Lihat seksi [Pola Kode: main.py](#pola-kode-mainpy))

### 10. Jalankan server
```bash
uvicorn app.main:app --reload
```

---

## Urutan Pembuatan Endpoint Baru

Untuk setiap fitur baru, ikuti urutan ini:

```
1. model/         → Definisi tabel (SQLAlchemy ORM)
2. alembic/       → Buat migration file, lalu alembic upgrade head
3. schemas/       → Pydantic Base/Create/Update/Out
4. service/       → Business logic (CRUD + validasi)
5. router/        → FastAPI endpoints (gunakan service)
6. main.py        → Import dan daftarkan router baru
7. seeder/        → (opsional) Data awal untuk testing
```

---

## Pola Kode: Config

### `app/config/config.py`
```python
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DB_USER = "postgres"
DB_PASS = quote_plus(os.getenv("DB_PASS", "admin"))
DB_NAME = os.getenv("DB_NAME", "fastapi_namaproject_api")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")

DB_POOLSIZE = 50
DB_MAXOVERFLOW = 25
DB_POOLTIMEOUT = 30
DB_POOLRECYCLE = 1800

SECRET_KEY = os.getenv("SECRET_KEY", "change_me_in_env")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
```

### `app/config/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from ..config.config import *

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable",
    pool_pre_ping=True,
    pool_size=DB_POOLSIZE,
    max_overflow=DB_MAXOVERFLOW,
    pool_timeout=DB_POOLTIMEOUT,
    pool_recycle=DB_POOLRECYCLE,
)

def get_db():
    with DBContext() as db:
        try:
            yield db
        except:
            db.rollback()
            raise
        else:
            db.commit()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
metadata = Base.metadata

class DBContext:
    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self.db

    def __exit__(self, et, ev, traceback):
        self.db.close()
```

**Aturan penting:**
- Selalu gunakan `get_db()` sebagai dependency di router — auto commit/rollback
- `DBContext` dipakai untuk session manual (misal di seeder)
- Database: PostgreSQL, BUKAN SQLite

---

## Pola Kode: Model (SQLAlchemy ORM)

### Template model sederhana
```python
import uuid
from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID

from ..config.database import Base


class NamaModel(Base):
    __tablename__ = "nama_tabel"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama_kolom = Column(String(100), nullable=False)
    deskripsi = Column(Text, nullable=True)
    urutan = Column(Integer, nullable=False)
```

### Template model dengan timestamp WIB
```python
import uuid
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from ..config.database import Base
from ..utils.time import wib_now


class NamaModel(Base):
    __tablename__ = "nama_tabel"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=wib_now)
    updated_at = Column(DateTime, nullable=False, default=wib_now, onupdate=wib_now)

    @property
    def created_at_formatted(self):
        return self.created_at.strftime("%Y-%m-%d") if self.created_at else None

    @property
    def updated_at_formatted(self):
        return self.updated_at.strftime("%Y-%m-%d") if self.updated_at else None
```

### Template model dengan foreign key & camelCase alias
```python
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from ..config.database import Base
from ..utils.time import wib_now


class NamaModel(Base):
    __tablename__ = "nama_tabel"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("parent.id", ondelete="SET NULL"), nullable=True)
    # Kolom boolean dengan alias camelCase di database
    is_completed = Column("isCompleted", Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, nullable=False, default=wib_now, onupdate=wib_now)

    # Expose camelCase property agar serializer bisa akses
    @property
    def isCompleted(self):
        return self.is_completed

    @property
    def updated_at_formatted(self):
        return self.updated_at.strftime("%Y-%m-%d") if self.updated_at else None
```

**Aturan model:**
- Primary key selalu `UUID(as_uuid=True)` dengan `default=uuid.uuid4`
- Timestamp disimpan dalam WIB menggunakan `default=wib_now`
- Kolom `is_completed` di Python → `"isCompleted"` sebagai nama kolom DB (string pertama di Column)
- Tambahkan `@property` untuk expose nama camelCase yang dibutuhkan serializer
- Foreign key: `ondelete="CASCADE"` untuk relasi wajib, `ondelete="SET NULL"` untuk opsional
- Import semua dari `..config.database` dan `..utils.time`

---

## Pola Kode: Alembic Migration

### `alembic/env.py` (edit setelah `alembic init`)
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

SQLALCHEMY_DATABASE_URL = os.environ.get("SQLALCHEMY_DATABASE_URL")

config = context.config
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Base SETELAH set URL
from app.config.database import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Template file migrasi
```python
"""create nama_tabel table

Revision ID: xxxxxxxxxxxx
Revises: yyyyyyyyyyyy
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "xxxxxxxxxxxx"
down_revision: Union[str, Sequence[str], None] = "yyyyyyyyyyyy"  # None jika migrasi pertama
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nama_tabel",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nama", sa.String(100), nullable=False),
        sa.Column("deskripsi", sa.Text, nullable=True),
        sa.Column("urutan", sa.Integer, nullable=False),
        sa.Column("isCompleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("nama_tabel")
```

**Perintah alembic:**
```bash
# Buat file migrasi baru
alembic revision -m "create nama_tabel table"

# Jalankan migrasi ke versi terbaru
alembic upgrade head

# Rollback semua migrasi
alembic downgrade base

# Rollback 1 langkah
alembic downgrade -1
```

**Aturan migrasi:**
- `down_revision` harus menunjuk ke revision ID migrasi sebelumnya
- Migrasi pertama: `down_revision = None`
- Selalu sediakan `downgrade()` yang reverses `upgrade()`
- Gunakan `sa.UUID` (bukan `UUID(as_uuid=True)`) di file migrasi
- Nama kolom DB harus konsisten dengan nama di model (termasuk camelCase alias)

---

## Pola Kode: Schemas (Pydantic)

### Template schema lengkap
```python
from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_serializer


# Shared fields
class NamaBase(BaseModel):
    nama: str
    deskripsi: Optional[str] = None
    urutan: int


# Untuk POST (create)
class NamaCreate(NamaBase):
    pass


# Untuk PUT (update) — semua field opsional
class NamaUpdate(BaseModel):
    nama: Optional[str] = None
    deskripsi: Optional[str] = None
    urutan: Optional[int] = None


# Untuk response
class NamaOut(BaseModel):
    id: UUID
    nama: str
    deskripsi: Optional[str] = None
    urutan: int

    class Config:
        from_attributes = True  # Wajib untuk SQLAlchemy ORM objects
```

### Schema dengan datetime serializer
```python
class NamaOut(BaseModel):
    id: UUID
    nama: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer("created_at", when_used="json")
    def serialize_created_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d")

    @field_serializer("updated_at", when_used="json")
    def serialize_updated_at(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d")
```

### Schema dengan camelCase alias
```python
class NamaOut(BaseModel):
    id: UUID
    isCompleted: bool          # nama property dari model ORM
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer("updated_at", when_used="json")
    def serialize_updated_at(self, value: Optional[datetime]) -> Optional[str]:
        return value.strftime("%Y-%m-%d") if value else None
```

### Schema dengan foreign key field
```python
class NamaCreate(BaseModel):
    parent_id: UUID            # UUID field untuk FK
    nama: str
```

**Aturan schema:**
- Gunakan Pydantic v2 — `@field_serializer` bukan `@validator`
- `from_attributes = True` wajib di semua `Out` schema yang menggunakan ORM object
- Pisahkan: `Base` (shared), `Create` (POST), `Update` (PUT, semua opsional), `Out` (response)
- Format datetime output: `"%Y-%m-%d"` (bukan ISO 8601 penuh)
- Field boolean camelCase (misal `isCompleted`) ditulis langsung di schema, diambil dari `@property` model

---

## Pola Kode: Service (Business Logic)

### Template service CRUD dasar
```python
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..model.nama_model import NamaModel
from ..schemas.nama_schema import NamaCreate, NamaUpdate


def get_by_id(db: Session, item_id: str) -> Optional[NamaModel]:
    return db.query(NamaModel).filter(NamaModel.id == item_id).first()


def get_all(db: Session) -> List[NamaModel]:
    return db.query(NamaModel).order_by(NamaModel.urutan.asc()).all()


def create_item(db: Session, payload: NamaCreate) -> NamaModel:
    item = NamaModel(
        id=uuid.uuid4(),
        nama=payload.nama,
        deskripsi=payload.deskripsi,
        urutan=payload.urutan,
    )
    db.add(item)
    db.flush()  # flush untuk dapat generated values tanpa commit
    return item


def update_item(db: Session, item_id: str, payload: NamaUpdate) -> Optional[NamaModel]:
    item = get_by_id(db, item_id)
    if not item:
        return None
    if payload.nama is not None:
        item.nama = payload.nama
    if payload.deskripsi is not None:
        item.deskripsi = payload.deskripsi
    if payload.urutan is not None:
        item.urutan = payload.urutan
    db.flush()
    return item


def delete_item(db: Session, item_id: str) -> bool:
    item = get_by_id(db, item_id)
    if not item:
        return False
    db.delete(item)
    return True
```

### Service dengan validasi & relasi
```python
def create_item(db: Session, payload: NamaCreate, current_user) -> NamaModel:
    # Validasi parent exists
    parent = db.query(ParentModel).filter(ParentModel.id == str(payload.parent_id)).first()
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found")

    # Validasi duplikasi
    existing = db.query(NamaModel).filter(
        NamaModel.user_id == str(current_user.id),
        NamaModel.parent_id == str(payload.parent_id)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item already exists")

    item = NamaModel(
        id=uuid.uuid4(),
        user_id=str(current_user.id),
        parent_id=str(payload.parent_id),
        nama=payload.nama,
    )
    db.add(item)
    db.flush()
    return item
```

**Aturan service:**
- Semua business logic ada di service, BUKAN di router
- Gunakan `db.flush()` setelah `db.add()` — jangan `db.commit()` (commit dihandle `get_db()`)
- Raise `HTTPException` langsung dari service jika perlu (tidak perlu try-catch di router untuk ini)
- Kembalikan `None` dari update/delete jika tidak ditemukan (router yang raise 404)
- Kembalikan `False` dari delete jika tidak ditemukan
- Query menggunakan `str()` untuk UUID comparison: `Model.id == str(some_uuid)`

---

## Pola Kode: Auth Service

### `app/service/auth.py`
```python
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config.config import SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from ..config.database import get_db
from ..model.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire_delta = expires_minutes or JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.utcnow() + timedelta(minutes=expire_delta)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials if credentials else None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
```

**Aturan auth:**
- `HTTPBearer` scheme (bukan `OAuth2PasswordBearer`) — Swagger hanya minta token, bukan username/password
- Token payload: `{"sub": user_id_string, "exp": datetime}`
- `get_current_user` dipakai sebagai Depends di semua endpoint yang butuh auth
- bcrypt membatasi password max 72 byte — validasi di service sebelum hash
- Encode `user.id` sebagai `str` saat buat token: `create_access_token(subject=str(user.id))`

---

## Pola Kode: Router

### Template router CRUD standar
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..config.database import get_db
from ..schemas.nama_schema import NamaCreate, NamaUpdate, NamaOut
from ..service.nama_service import (
    create_item,
    get_by_id,
    get_all,
    update_item,
    delete_item,
)
from ..service.auth import get_current_user
from ..model.user import User


router_nama = APIRouter(prefix="/api/nama-entitas", tags=["Nama Entitas"])


@router_nama.post("/", response_model=NamaOut, status_code=status.HTTP_201_CREATED)
def create_endpoint(
    payload: NamaCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),   # _ jika user tidak dipakai di logic
):
    return create_item(db, payload)


@router_nama.get("/", response_model=List[NamaOut])
def list_endpoint(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_all(db)


@router_nama.get("/{item_id}", response_model=NamaOut)
def read_endpoint(
    item_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = get_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router_nama.put("/{item_id}", response_model=NamaOut)
def update_endpoint(
    item_id: str,
    payload: NamaUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = update_item(db, item_id, payload)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router_nama.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_endpoint(
    item_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    deleted = delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return None  # 204 No Content — wajib return None
```

### Router yang butuh current_user di service
```python
@router_nama.post("/", response_model=NamaOut, status_code=status.HTTP_201_CREATED)
def create_endpoint(
    payload: NamaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # pakai current_user jika diteruskan ke service
):
    return create_item(db, payload, current_user)
```

**Aturan router:**
- Router hanya handle HTTP: parsing request, manggil service, return response
- TIDAK ada business logic di router
- Prefix format: `/api/nama-entitas` (kebab-case)
- Tags: `["Nama Entitas"]` (Title Case dengan spasi)
- `_: User = Depends(get_current_user)` jika user tidak diperlukan (hanya untuk auth check)
- `current_user: User = Depends(get_current_user)` jika user diteruskan ke service
- Status codes: `201` (create), `204` (delete), `400` (bad request), `401` (unauth), `404` (not found)
- DELETE endpoint: `return None` untuk 204 No Content
- Semua endpoint WAJIB `Depends(get_current_user)` kecuali: `/register`, `/login`

---

## Pola Kode: Seeder

### Template seeder per domain
```python
import uuid
from sqlalchemy.orm import Session

from app.model.nama_model import NamaModel


def seed_nama(db: Session) -> None:
    samples = [
        {"nama": "Item Pertama", "deskripsi": "Deskripsi pertama", "urutan": 1},
        {"nama": "Item Kedua", "deskripsi": "Deskripsi kedua", "urutan": 2},
    ]

    for s in samples:
        # Cek duplikasi berdasarkan field unik (biasanya nama/title)
        exists = db.query(NamaModel).filter(NamaModel.nama == s["nama"]).first()
        if exists:
            # Update jika ada perubahan data
            if exists.urutan != s["urutan"]:
                exists.urutan = s["urutan"]
            continue

        item = NamaModel(
            id=uuid.uuid4(),
            nama=s["nama"],
            deskripsi=s.get("deskripsi"),
            urutan=s["urutan"],
        )
        db.add(item)


if __name__ == "__main__":
    from app.config.database import SessionLocal

    db = SessionLocal()
    try:
        seed_nama(db)
        db.commit()
        print("Seed nama selesai.")
    except Exception as e:
        db.rollback()
        print(f"Seed nama gagal: {e}")
        raise
    finally:
        db.close()
```

### Seeder yang return data (untuk dipakai seeder lain)
```python
from typing import Dict

def seed_nama(db: Session) -> Dict[str, NamaModel]:
    # ... seed logic ...
    by_nama: Dict[str, NamaModel] = {}
    for s in samples:
        # ... create or find ...
        by_nama[s["nama"]] = item
    return by_nama  # dict keyed by natural ID untuk dipakai seeder child
```

### `seeder/seed_all.py`
```python
from app.config.database import SessionLocal
from .seed_xxx import seed_xxx
from .seed_yyy import seed_yyy
from .seed_zzz import seed_zzz


def run() -> None:
    db = SessionLocal()
    try:
        # Seed parent dulu, kemudian child
        parents = seed_xxx(db)
        db.commit()

        seed_yyy(db, parents)
        seed_zzz(db)
        db.commit()

        print("Seeding selesai.")
    except Exception as e:
        db.rollback()
        print(f"Seeding gagal: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
```

**Jalankan seeder:**
```bash
python -m seeder.seed_all
# atau seeder individual:
python -m seeder.seed_nama
```

**Aturan seeder:**
- Seeder bersifat **idempotent** — aman dijalankan berulang kali
- Selalu cek `exists` sebelum insert
- Jika ada perubahan data (misal `urutan`), update value yang berbeda
- Gunakan `DBContext` dari `SessionLocal()` di seeder, bukan `get_db()` (karena bukan FastAPI dependency)
- Commit manual di `seed_all.py`, seeder individual tidak commit sendiri kecuali dijalankan sebagai `__main__`
- Urutan seed harus mengikuti dependency: parent sebelum child

---

## Pola Kode: main.py

```python
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Import semua router
from .router.router_user import router_user
from .router.router_nama import router_nama

load_dotenv(find_dotenv())

app = FastAPI(
    title="Nama Project API",
    description="API untuk aplikasi Nama Project",
    version="0.1.0",
)

# CORS — izinkan semua origin (sesuaikan di production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root redirect ke Swagger docs
@app.get("/", response_class=RedirectResponse, include_in_schema=False)
def docs():
    return RedirectResponse(url="/docs")

# Serve file media (audio upload, TTS output)
app.mount("/media", StaticFiles(directory="media"), name="media")

# Daftarkan semua router
app.include_router(router_user)
app.include_router(router_nama)
```

**Aturan main.py:**
- `load_dotenv(find_dotenv())` dipanggil di awal sebelum import apapun yang perlu env
- CORS menggunakan `allow_origins=["*"]` untuk development
- Root endpoint (`/`) redirect ke `/docs` (Swagger UI)
- `StaticFiles` untuk serve media — buat folder `media/` sebelum run jika ada file upload
- Urutan `include_router` tidak kritis, tapi urutkan sesuai dependency (user dulu)

---

## Konvensi Umum

### `app/utils/time.py`
```python
from datetime import datetime, timedelta


def wib_now() -> datetime:
    """Return current time in WIB (UTC+7), naive datetime."""
    return datetime.utcnow() + timedelta(hours=7)
```

### UUID
- Semua primary key menggunakan UUID, bukan integer auto-increment
- UUID di-generate di aplikasi: `id=uuid.uuid4()`
- Di model: `Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`
- Di migration: `sa.Column("id", sa.UUID, primary_key=True)`
- Di service saat query: selalu cast ke `str()` — `Model.id == str(some_uuid)`

### Timezone
- Semua timestamp disimpan dalam **WIB (UTC+7)** menggunakan `wib_now()`
- TIDAK menggunakan `datetime.now()` atau `datetime.utcnow()` langsung
- TIDAK menggunakan timezone-aware datetime (selalu naive datetime)

### Naming conventions
| Jenis | Konvensi | Contoh |
|-------|----------|--------|
| File Python | snake_case | `user_service.py` |
| Class model | PascalCase | `UserExercise` |
| Nama tabel DB | snake_case | `user_exercise` |
| Kolom DB | snake_case | `exercise_id` |
| Kolom DB boolean | camelCase | `isCompleted` |
| Router prefix | kebab-case | `/api/user-exercises` |
| Router tags | Title Case | `["User Exercises"]` |
| Variable/function | snake_case | `get_user_by_id` |

### HTTP Status Codes
| Situasi | Kode |
|---------|------|
| GET berhasil | 200 |
| POST create berhasil | 201 |
| DELETE berhasil | 204 (return None) |
| Validasi gagal / duplikasi | 400 |
| Token tidak valid / belum login | 401 |
| Resource tidak ditemukan | 404 |

### Dependencies (requirement.txt template)
```
alembic==1.17.0
fastapi==0.119.1
pydantic==2.12.3
pydantic-extra-types==2.10.6
python-dotenv==1.1.1
python-multipart==0.0.20
email-validator==2.3.0
sqlalchemy==2.0.44
psycopg2==2.9.11
uvicorn==0.38.0
gunicorn==21.2.0
passlib==1.7.4
python-jose==3.3.0
bcrypt==4.2.0
```

### Checklist saat tambah endpoint baru
- [ ] Model dibuat di `app/model/`
- [ ] Model di-import di `alembic/env.py` (agar Alembic mendeteksi tabel)
- [ ] Migration dibuat dan dijalankan: `alembic revision -m "..."` → `alembic upgrade head`
- [ ] Schema dibuat di `app/schemas/` (Base, Create, Update, Out)
- [ ] Service dibuat di `app/service/` (fungsi CRUD + validasi)
- [ ] Router dibuat di `app/router/` (endpoint memanggil service)
- [ ] Router di-import dan di-include di `app/main.py`
- [ ] Seeder dibuat di `seeder/` jika butuh data awal
- [ ] Seeder didaftarkan di `seeder/seed_all.py`
