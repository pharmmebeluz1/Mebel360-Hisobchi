# -*- coding: utf-8 -*-
"""Mebel360 Hisobchi server layer.

Adds:
- real login/session roles
- server database for projects/catalog state
- automatic project snapshots/backups
- CBU exchange-rate service with last-known cache
- warehouse stock + purchase preview
- Mebel360 ERP outbound queue/connector
- project validation API
- security gate for AI and 2D-PLACE mutation endpoints

The existing calculator/2D-PLACE routes remain in bridge_app.py.
"""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any

import requests
from flask import Response, jsonify, request, send_from_directory, session
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

from bridge_app import APP_DIR, app


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------- App/session security ----------
app.secret_key = os.getenv("SECRET_KEY", "") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "1" if os.getenv("RENDER") else "0") == "1",
)


# ---------- Database ----------
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="constructor")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    customer: Mapped[str] = mapped_column(String(180), default="")
    status: Mapped[str] = mapped_column(String(80), default="")
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ClientState(Base):
    __tablename__ = "client_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    state_key: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    __table_args__ = (UniqueConstraint("user_id", "state_key", name="uq_client_state_user_key"),)


class WarehouseItem(Base):
    __tablename__ = "warehouse_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    category: Mapped[str] = mapped_column(String(80), default="material")
    thickness: Mapped[str] = mapped_column(String(40), default="")
    color: Mapped[str] = mapped_column(String(120), default="")
    unit: Mapped[str] = mapped_column(String(40), default="list")
    qty: Mapped[float] = mapped_column(Float, default=0)
    reserved_qty: Mapped[float] = mapped_column(Float, default=0)
    price_currency: Mapped[str] = mapped_column(String(8), default="UZS")
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    rate_uzs: Mapped[float] = mapped_column(Float, default=1)
    unit_price_uzs: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Backup(Base):
    __tablename__ = "backups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(80), index=True)
    reference: Mapped[str] = mapped_column(String(120), default="")
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ErpQueue(Base):
    __tablename__ = "erp_queue"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_code: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Audit(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=0)
    action: Mapped[str] = mapped_column(String(100))
    entity: Mapped[str] = mapped_column(String(80), default="")
    entity_id: Mapped[str] = mapped_column(String(100), default="")
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


DB_URL = os.getenv("DATABASE_URL", "").strip()
if not DB_URL:
    DB_URL = "sqlite:///" + str((APP_DIR / "mebel360_server.db").resolve()).replace("\\", "/")
if DB_URL.startswith("postgres://"):
    DB_URL = "postgresql+psycopg://" + DB_URL[len("postgres://"):]
elif DB_URL.startswith("postgresql://") and "+psycopg" not in DB_URL:
    DB_URL = "postgresql+psycopg://" + DB_URL[len("postgresql://"):]

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, pool_pre_ping=True, future=True, connect_args=connect_args)
DB = sessionmaker(bind=engine, expire_on_commit=False, future=True)
Base.metadata.create_all(engine)


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_loads(value: str, fallback: Any = None) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return fallback


def audit(action: str, entity: str = "", entity_id: str = "", details: Any = None) -> None:
    try:
        with DB() as db:
            db.add(Audit(
                user_id=int(session.get("user_id") or 0), action=action, entity=entity,
                entity_id=str(entity_id or ""), details=json_dumps(details) if details is not None else "",
            ))
            db.commit()
    except Exception:
        pass


def setting_get(key: str, default: Any = None) -> Any:
    with DB() as db:
        row = db.get(Setting, key)
        return json_loads(row.value, default) if row else default


def setting_set(key: str, value: Any) -> None:
    with DB() as db:
        row = db.get(Setting, key)
        if row:
            row.value = json_dumps(value)
            row.updated_at = utcnow()
        else:
            db.add(Setting(key=key, value=json_dumps(value)))
        db.commit()


def bootstrap_admin() -> None:
    username = os.getenv("ADMIN_USER", "admin").strip() or "admin"
    password = os.getenv("ADMIN_PASSWORD", "Mebel360-360")
    with DB() as db:
        exists = db.scalar(select(User).where(User.username == username))
        if not exists:
            db.add(User(username=username, password_hash=generate_password_hash(password), role="admin", active=True))
            db.commit()


bootstrap_admin()


# ---------- Auth helpers ----------
def current_user() -> User | None:
    uid = session.get("user_id")
    if not uid:
        return None
    with DB() as db:
        user = db.get(User, int(uid))
        return user if user and user.active else None


def auth_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify(ok=False, error="Avval tizimga kiring", auth_required=True), 401
        return fn(*args, **kwargs)
    return wrapped


def roles_required(*roles: str):
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify(ok=False, error="Avval tizimga kiring", auth_required=True), 401
            if user.role not in roles:
                return jsonify(ok=False, error="Bu amal uchun ruxsat yo‘q"), 403
            return fn(*args, **kwargs)
        return wrapped
    return deco


@app.before_request
def protect_sensitive_api():
    path = request.path
    if not path.startswith("/api/"):
        return None
    public_prefixes = ("/api/auth/", "/api/cbu/", "/api/health")
    if path.startswith(public_prefixes):
        return None
    # Protect AI key/use, 2D bridge and all server data APIs.
    if path.startswith(("/api/ai/", "/api/2dplace/", "/api/export-2dplace", "/api/projects", "/api/state/", "/api/warehouse", "/api/erp", "/api/backup", "/api/validation")):
        if not current_user():
            return jsonify(ok=False, error="Avval tizimga kiring", auth_required=True), 401
    return None


@app.after_request
def secure_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(self), camera=(), microphone=()")
    return response


# ---------- Health/auth ----------
@app.get("/api/health")
def health():
    return jsonify(ok=True, app="Mebel360 Hisobchi", db="connected", time=utcnow().isoformat())


@app.get("/api/auth/me")
def auth_me():
    user = current_user()
    if not user:
        return jsonify(ok=False, authenticated=False), 401
    return jsonify(ok=True, authenticated=True, user={"id": user.id, "username": user.username, "role": user.role})


@app.post("/api/auth/login")
def auth_login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    with DB() as db:
        user = db.scalar(select(User).where(User.username == username))
        if not user or not user.active or not check_password_hash(user.password_hash, password):
            return jsonify(ok=False, error="Login yoki parol noto‘g‘ri"), 401
        session.clear()
        session["user_id"] = user.id
        session["role"] = user.role
        session.permanent = True
    audit("login", "user", username)
    return jsonify(ok=True, user={"username": username, "role": session["role"]}, default_password=(password == "Mebel360-360"))


@app.post("/api/auth/logout")
def auth_logout():
    audit("logout", "user", str(session.get("user_id") or ""))
    session.clear()
    return jsonify(ok=True)


@app.post("/api/auth/change-password")
@auth_required
def change_password():
    data = request.get_json(silent=True) or {}
    old = str(data.get("old_password", ""))
    new = str(data.get("new_password", ""))
    if len(new) < 8:
        return jsonify(ok=False, error="Yangi parol kamida 8 ta belgidan iborat bo‘lsin"), 400
    user = current_user()
    assert user
    with DB() as db:
        row = db.get(User, user.id)
        if not row or not check_password_hash(row.password_hash, old):
            return jsonify(ok=False, error="Eski parol noto‘g‘ri"), 400
        row.password_hash = generate_password_hash(new)
        db.commit()
    audit("change_password", "user", str(user.id))
    return jsonify(ok=True)


@app.post("/api/auth/users")
@roles_required("admin")
def create_user():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    role = str(data.get("role", "constructor")).strip().lower()
    if role not in {"admin", "rahbar", "constructor", "worker", "viewer"}:
        role = "constructor"
    if len(username) < 3 or len(password) < 8:
        return jsonify(ok=False, error="Login 3+, parol 8+ belgi bo‘lsin"), 400
    with DB() as db:
        if db.scalar(select(User).where(User.username == username)):
            return jsonify(ok=False, error="Bu login band"), 409
        db.add(User(username=username, password_hash=generate_password_hash(password), role=role))
        db.commit()
    audit("create_user", "user", username, {"role": role})
    return jsonify(ok=True)


# ---------- Validation ----------
def n(form: dict[str, Any], key: str, default: float = 0) -> float:
    try:
        return float(form.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def validate_project_payload(payload: dict[str, Any]) -> dict[str, list[str]]:
    form = payload.get("form") if isinstance(payload.get("form"), dict) else {}
    errors: list[str] = []
    warnings: list[str] = []
    h, w, d, t = n(form, "h"), n(form, "w"), n(form, "d"), n(form, "t", 16)
    sections = max(1, int(n(form, "sections", 1)))
    if h <= 0 or w <= 0 or d <= 0:
        errors.append("Balandlik, eni va chuqurlik 0 dan katta bo‘lishi kerak.")
    if h and h < 300: warnings.append("Balandlik 300 mm dan kichik — o‘lchamni tekshiring.")
    if w and w < 200: warnings.append("Mebel eni 200 mm dan kichik — o‘lchamni tekshiring.")
    if d and d < 150: warnings.append("Chuqurlik 150 mm dan kichik — furnitura sig‘ishini tekshiring.")
    if t < 8 or t > 40: warnings.append("Material qalinligi odatiy 8–40 mm oralig‘idan tashqarida.")
    clear = w - (sections + 1) * t if w else 0
    if clear <= 0:
        errors.append("Bo‘limlar va vertikal detallar uchun ichki eni yetarli emas.")
    elif clear / sections < 120:
        warnings.append("Har bir bo‘lim ichki eni 120 mm dan kichik bo‘lib qolmoqda.")
    widths = payload.get("customWidths") if isinstance(payload.get("customWidths"), list) else []
    if widths and clear > 0:
        total = sum(float(x or 0) for x in widths)
        if abs(total - clear) > 3:
            warnings.append(f"Erkin bo‘limlar jami {total:.0f} mm, hisoblangan ichki eni {clear:.0f} mm. Farqni tekshiring.")
    parts = ((payload.get("twoDPlace") or {}).get("parts") or []) if isinstance(payload.get("twoDPlace"), dict) else []
    zero_parts = [p.get("name", "Detal") for p in parts if float(p.get("length") or 0) <= 0 or float(p.get("width") or 0) <= 0]
    if zero_parts:
        errors.append("0 o‘lchamli detallar bor: " + ", ".join(map(str, zero_parts[:5])))
    # Common collision risk hints, not hard claims.
    shelves = int(n(form, "shelves", 0))
    doors = int(n(form, "doors", 0))
    drawers = int(n(form, "drawers", 0))
    if shelves >= 8 and h and h < 1600:
        warnings.append("Tokcha soni balandlikka nisbatan ko‘p — tokcha oralig‘ini tekshiring.")
    if drawers >= 5 and h and h < 1100:
        warnings.append("Tortma soni balandlikka nisbatan ko‘p — mexanizm va fasad to‘qnashuvini tekshiring.")
    if doors >= 4 and w and w < 1200:
        warnings.append("Eshik soni umumiy eniga nisbatan ko‘p — fasad enlarini tekshiring.")
    return {"errors": errors, "warnings": warnings}


@app.post("/api/validation/project")
@auth_required
def validate_project_api():
    payload = request.get_json(silent=True) or {}
    result = validate_project_payload(payload)
    return jsonify(ok=not bool(result["errors"]), **result)


# ---------- Project DB + backups ----------
def project_to_dict(row: Project) -> dict[str, Any]:
    data = json_loads(row.payload, {}) or {}
    data["code"] = row.code
    data.setdefault("meta", {})["code"] = row.code
    data["serverUpdatedAt"] = row.updated_at.isoformat() if row.updated_at else None
    return data


@app.get("/api/projects")
@auth_required
def projects_list():
    with DB() as db:
        rows = db.scalars(select(Project).order_by(Project.updated_at.desc())).all()
        return jsonify(ok=True, projects=[project_to_dict(x) for x in rows])


@app.get("/api/projects/<code>")
@auth_required
def project_get(code: str):
    with DB() as db:
        row = db.scalar(select(Project).where(Project.code == code))
        if not row:
            return jsonify(ok=False, error="Loyiha topilmadi"), 404
        return jsonify(ok=True, project=project_to_dict(row))


@app.post("/api/projects")
@auth_required
def project_upsert():
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code") or (payload.get("meta") or {}).get("code") or "").strip()
    if not code:
        return jsonify(ok=False, error="Buyurtma kodi yo‘q"), 400
    result = validate_project_payload(payload)
    if result["errors"]:
        return jsonify(ok=False, error="Loyiha validatsiyadan o‘tmadi", **result), 422
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    with DB() as db:
        row = db.scalar(select(Project).where(Project.code == code))
        if row:
            # Snapshot before update.
            db.add(Backup(kind="project_before_update", reference=code, payload=row.payload))
            row.customer = str(meta.get("customer", ""))
            row.status = str(meta.get("status", ""))
            row.payload = json_dumps(payload)
            row.updated_at = utcnow()
        else:
            row = Project(code=code, customer=str(meta.get("customer", "")), status=str(meta.get("status", "")), payload=json_dumps(payload))
            db.add(row)
        db.add(Backup(kind="project_saved", reference=code, payload=json_dumps(payload)))
        db.commit()
    audit("project_save", "project", code, {"warnings": result["warnings"]})
    return jsonify(ok=True, code=code, warnings=result["warnings"])


@app.delete("/api/projects/<code>")
@auth_required
def project_delete(code: str):
    with DB() as db:
        row = db.scalar(select(Project).where(Project.code == code))
        if not row:
            return jsonify(ok=True)
        db.add(Backup(kind="project_deleted", reference=code, payload=row.payload))
        db.delete(row)
        db.commit()
    audit("project_delete", "project", code)
    return jsonify(ok=True)


# ---------- Client state sync ----------
STATE_KEYS = {"m360_materials_v1", "m360_hardware_v1", "m360_offcuts_v1", "m360_production_queue_v1"}


@app.get("/api/state/<state_key>")
@auth_required
def state_get(state_key: str):
    if state_key not in STATE_KEYS:
        return jsonify(ok=False, error="Noma’lum state kaliti"), 404
    user = current_user(); assert user
    with DB() as db:
        row = db.scalar(select(ClientState).where(ClientState.user_id == user.id, ClientState.state_key == state_key))
        return jsonify(ok=True, key=state_key, value=json_loads(row.payload, []) if row else [], updatedAt=row.updated_at.isoformat() if row else None)


@app.post("/api/state/<state_key>")
@auth_required
def state_save(state_key: str):
    if state_key not in STATE_KEYS:
        return jsonify(ok=False, error="Noma’lum state kaliti"), 404
    user = current_user(); assert user
    data = request.get_json(silent=True)
    value = data.get("value") if isinstance(data, dict) and "value" in data else data
    if not isinstance(value, list):
        return jsonify(ok=False, error="State array bo‘lishi kerak"), 400
    with DB() as db:
        row = db.scalar(select(ClientState).where(ClientState.user_id == user.id, ClientState.state_key == state_key))
        if row:
            db.add(Backup(kind="state_before_update", reference=state_key, payload=row.payload))
            row.payload = json_dumps(value); row.updated_at = utcnow()
        else:
            db.add(ClientState(user_id=user.id, state_key=state_key, payload=json_dumps(value)))
        db.commit()
    return jsonify(ok=True)


# ---------- CBU currency ----------
CBU_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"


def cbu_rate(ccy: str) -> tuple[float, str, str]:
    ccy = ccy.upper()
    if ccy == "UZS":
        return 1.0, datetime.now().strftime("%d.%m.%Y"), "base"
    try:
        response = requests.get(CBU_URL, timeout=8, headers={"User-Agent": "Mebel360-Hisobchi/2.0"})
        response.raise_for_status()
        for item in response.json():
            if str(item.get("Ccy", "")).upper() == ccy:
                rate = float(str(item.get("Rate", "0")).replace(",", "."))
                date = str(item.get("Date", ""))
                if rate > 0:
                    setting_set("cbu_" + ccy, {"rate": rate, "date": date, "savedAt": utcnow().isoformat()})
                    return rate, date, "cbu"
    except Exception:
        pass
    cached = setting_get("cbu_" + ccy, {}) or {}
    if float(cached.get("rate") or 0) > 0:
        return float(cached["rate"]), str(cached.get("date") or ""), "cache"
    raise RuntimeError(f"{ccy} kursini Markaziy bankdan olib bo‘lmadi")


@app.get("/api/cbu/rates")
def cbu_rates():
    ccy = str(request.args.get("ccy", "USD")).upper()
    if ccy not in {"USD", "EUR", "RUB", "CNY", "UZS"}:
        return jsonify(ok=False, error="Valyuta qo‘llab-quvvatlanmaydi"), 400
    try:
        rate, date, source = cbu_rate(ccy)
        return jsonify(ok=True, ccy=ccy, rate=rate, date=date, source=source)
    except RuntimeError as exc:
        return jsonify(ok=False, error=str(exc)), 503


@app.post("/api/cbu/convert")
def cbu_convert():
    data = request.get_json(silent=True) or {}
    ccy = str(data.get("ccy", "USD")).upper()
    try:
        unit_price = float(data.get("unit_price") or 0); qty = float(data.get("qty") or 0)
        rate, date, source = cbu_rate(ccy)
    except (ValueError, RuntimeError) as exc:
        return jsonify(ok=False, error=str(exc)), 400
    total_foreign = unit_price * qty
    return jsonify(ok=True, ccy=ccy, unit_price=unit_price, qty=qty, total_foreign=total_foreign,
                   rate=rate, rate_date=date, source=source, total_uzs=round(total_foreign * rate, 2), unit_price_uzs=round(unit_price * rate, 2))


# ---------- Warehouse ----------
def warehouse_to_dict(row: WarehouseItem) -> dict[str, Any]:
    return {
        "id": row.id, "sku": row.sku, "name": row.name, "category": row.category, "thickness": row.thickness,
        "color": row.color, "unit": row.unit, "qty": row.qty, "reserved_qty": row.reserved_qty,
        "available_qty": max(0, row.qty - row.reserved_qty), "price_currency": row.price_currency,
        "unit_price": row.unit_price, "rate_uzs": row.rate_uzs, "unit_price_uzs": row.unit_price_uzs,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
    }


@app.get("/api/warehouse/items")
@auth_required
def warehouse_list():
    q = str(request.args.get("q", "")).strip().lower()
    with DB() as db:
        rows = db.scalars(select(WarehouseItem).order_by(WarehouseItem.name.asc())).all()
        if q:
            rows = [x for x in rows if q in (x.name + " " + x.sku + " " + x.color + " " + x.thickness).lower()]
        return jsonify(ok=True, items=[warehouse_to_dict(x) for x in rows])


@app.post("/api/warehouse/items")
@auth_required
def warehouse_upsert():
    data = request.get_json(silent=True) or {}
    sku = str(data.get("sku", "")).strip()
    name = str(data.get("name", "")).strip()
    if not sku or not name:
        return jsonify(ok=False, error="SKU va nom majburiy"), 400
    currency = str(data.get("price_currency", "UZS")).upper()
    try:
        qty = float(data.get("qty") or 0); reserved = float(data.get("reserved_qty") or 0); unit_price = float(data.get("unit_price") or 0)
    except ValueError:
        return jsonify(ok=False, error="Soni/narxi raqam bo‘lishi kerak"), 400
    rate = 1.0
    if currency != "UZS" and unit_price:
        try: rate, _, _ = cbu_rate(currency)
        except RuntimeError: rate = float(data.get("rate_uzs") or 0) or 1.0
    with DB() as db:
        row = db.scalar(select(WarehouseItem).where(WarehouseItem.sku == sku))
        if not row:
            row = WarehouseItem(sku=sku, name=name); db.add(row)
        row.name = name; row.category = str(data.get("category", "material")); row.thickness = str(data.get("thickness", "")); row.color = str(data.get("color", "")); row.unit = str(data.get("unit", "list")); row.qty = qty; row.reserved_qty = reserved; row.price_currency = currency; row.unit_price = unit_price; row.rate_uzs = rate; row.unit_price_uzs = unit_price * rate; row.updated_at = utcnow(); db.commit()
        out = warehouse_to_dict(row)
    audit("warehouse_upsert", "warehouse", sku, out)
    return jsonify(ok=True, item=out)


@app.post("/api/warehouse/check")
@auth_required
def warehouse_check():
    data = request.get_json(silent=True) or {}
    reqs = data.get("requirements") or []
    if not isinstance(reqs, list):
        return jsonify(ok=False, error="requirements array bo‘lsin"), 400
    result = []
    with DB() as db:
        rows = db.scalars(select(WarehouseItem)).all()
        for req in reqs:
            sku = str(req.get("sku", "")).strip(); name = str(req.get("name", "")).strip().lower(); need = float(req.get("qty") or 0)
            row = next((x for x in rows if (sku and x.sku == sku) or (name and name in x.name.lower())), None)
            available = max(0, (row.qty - row.reserved_qty)) if row else 0
            result.append({"sku": sku or (row.sku if row else ""), "name": req.get("name") or (row.name if row else ""), "need": need, "available": available, "shortage": max(0, need - available), "ok": available >= need})
    return jsonify(ok=all(x["ok"] for x in result), result=result)


@app.post("/api/warehouse/purchase-preview")
@auth_required
def purchase_preview():
    data = request.get_json(silent=True) or {}
    ccy = str(data.get("ccy", "USD")).upper(); unit_price = float(data.get("unit_price") or 0); qty = float(data.get("qty") or 0)
    try: rate, date, source = cbu_rate(ccy)
    except RuntimeError as exc: return jsonify(ok=False, error=str(exc)), 503
    return jsonify(ok=True, ccy=ccy, unit_price=unit_price, qty=qty, total_foreign=unit_price*qty, rate=rate, rate_date=date, rate_source=source, total_uzs=round(unit_price*qty*rate, 2))


# ---------- ERP connector ----------
def erp_config() -> dict[str, str]:
    return {"url": os.getenv("MEBEL360_ERP_URL", "").strip().rstrip("/"), "token": os.getenv("MEBEL360_ERP_TOKEN", "").strip()}


def push_to_erp(payload: dict[str, Any]) -> tuple[bool, str]:
    cfg = erp_config()
    if not cfg["url"]:
        return False, "MEBEL360_ERP_URL sozlanmagan"
    endpoint = cfg["url"] + "/api/hisobchi/import"
    headers = {"Content-Type": "application/json", "User-Agent": "Mebel360-Hisobchi/2.0"}
    if cfg["token"]: headers["Authorization"] = "Bearer " + cfg["token"]
    try:
        r = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        if 200 <= r.status_code < 300: return True, "ERP qabul qildi"
        return False, f"ERP HTTP {r.status_code}: {r.text[:300]}"
    except Exception as exc:
        return False, f"ERP bilan aloqa bo‘lmadi: {exc}"


@app.get("/api/erp/status")
@auth_required
def erp_status():
    cfg = erp_config()
    with DB() as db:
        queued = len(db.scalars(select(ErpQueue).where(ErpQueue.status == "queued")).all())
        failed = len(db.scalars(select(ErpQueue).where(ErpQueue.status == "failed")).all())
    return jsonify(ok=True, configured=bool(cfg["url"]), url=cfg["url"], queued=queued, failed=failed)


@app.post("/api/erp/projects")
@auth_required
def erp_send_project():
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code") or (payload.get("meta") or {}).get("code") or "NOMA-LUM")
    valid = validate_project_payload(payload)
    if valid["errors"]:
        return jsonify(ok=False, error="Loyihada xato bor", **valid), 422
    ok, message = push_to_erp(payload)
    with DB() as db:
        q = ErpQueue(project_code=code, payload=json_dumps(payload), status="sent" if ok else "queued", error="" if ok else message)
        db.add(q); db.commit()
    audit("erp_send", "project", code, {"sent": ok, "message": message})
    return jsonify(ok=ok, queued=not ok, message=message, warnings=valid["warnings"]), (200 if ok else 202)


@app.post("/api/erp/retry")
@auth_required
def erp_retry():
    sent = 0; failed = 0
    with DB() as db:
        rows = db.scalars(select(ErpQueue).where(ErpQueue.status.in_(["queued", "failed"])).order_by(ErpQueue.created_at.asc())).all()
        for row in rows[:50]:
            payload = json_loads(row.payload, {}) or {}
            ok, msg = push_to_erp(payload)
            row.status = "sent" if ok else "failed"; row.error = "" if ok else msg; row.updated_at = utcnow()
            sent += int(ok); failed += int(not ok)
        db.commit()
    return jsonify(ok=True, sent=sent, failed=failed)


# ---------- Backups ----------
@app.get("/api/backup/export")
@auth_required
def backup_export():
    with DB() as db:
        projects = [project_to_dict(x) for x in db.scalars(select(Project).order_by(Project.updated_at.desc())).all()]
        warehouse = [warehouse_to_dict(x) for x in db.scalars(select(WarehouseItem).order_by(WarehouseItem.name.asc())).all()]
        user = current_user(); assert user
        states = {}
        for row in db.scalars(select(ClientState).where(ClientState.user_id == user.id)).all():
            states[row.state_key] = json_loads(row.payload, [])
    payload = {"version": "Mebel360-Hisobchi-Server-2", "exportedAt": utcnow().isoformat(), "projects": projects, "warehouse": warehouse, "states": states}
    audit("backup_export")
    return Response(json.dumps(payload, ensure_ascii=False, indent=2), mimetype="application/json", headers={"Content-Disposition": f"attachment; filename=Mebel360_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"})


@app.get("/api/backup/history")
@roles_required("admin", "rahbar")
def backup_history():
    with DB() as db:
        rows = db.scalars(select(Backup).order_by(Backup.created_at.desc()).limit(100)).all()
        return jsonify(ok=True, backups=[{"id": x.id, "kind": x.kind, "reference": x.reference, "createdAt": x.created_at.isoformat()} for x in rows])


# ---------- Static files and startup ----------
@app.get("/assets/<path:filename>")
def assets(filename: str):
    return send_from_directory(APP_DIR / "assets", filename)


@app.get("/<path:filename>")
def root_files(filename: str):
    # Keep API routes out; Flask chooses exact /api routes first, but this adds a final guard.
    if filename.startswith("api/"):
        return jsonify(ok=False, error="API topilmadi"), 404
    path = APP_DIR / filename
    if path.is_file():
        return send_from_directory(APP_DIR, filename)
    return send_from_directory(APP_DIR, "index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5067"))
    app.run(host="0.0.0.0", port=port, debug=False)
