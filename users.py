from __future__ import annotations

import base64
import secrets
import string
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List

from storage import read_json, write_json


class UserAuthSpec:
    algo: str = "pbkdf2_sha256"
    iterations: int = 120_000
    dklen: int = 32
    salt_bytes: int = 16

AUTH_SPEC = UserAuthSpec()

def validate_username(name: str) -> str:
    if name is None:
        raise ValueError("Username is required.")
    name = name.strip()
    if not(2 <= len(name) <= 400):
        raise ValueError("Username length must be 2 and 40 charecters.")
    allowed = set(string.ascii_letters + string.digits + "_-")
    if any(ch not in allowed for ch in name):
        raise ValueError("Username contains invalid characters. Allowed: letters, digits, _ - and spaces.")
    return name

def validate_currency(code: str) -> str:
    if code is None:
        raise ValueError("Currency is required.")
    code = code.strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ValueError("Currency must be exactly 3 letters (e.g., USD, EUR, SAR).")
    return code

def validate_pin(pin: str) -> str:
      if pin is None:
        raise ValueError("PIN is required.")
        pin = pin.strip()
      if not (4 <= len(pin) <= 12):
            raise ValueError("PIN length must be between 4 and 12 digits.")
      if not pin.isdigit():
            raise ValueError("PIN must be numeric.")
      return pin
      

def load_users(path: Path)-> List[Dict[str,Any]]:
    return read_json(path)

def save_users(path:Path, users: List[Dict[str,Any]]) -> None:
    write_json(path, users)

def find_user_by_name(users: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    for u in users:
        if u.get("name") == name:
            return u
    return None

def _b64e(raw: bytes) -> str:
    
    return base64.b64encode(raw).decode("ascii")

def _b64d(txt: str) -> bytes:
   
    return base64.b64decode(txt.encode("ascii"))

def hash_pin(pin: str, spec: UserAuthSpec = AUTH_SPEC) -> Dict[str, Any]:
      if spec.algo != "pbkdf2_sha256":
        raise ValueError("Unsupported algorithm.") 
      salt = secrets.token_bytes(spec.salt_bytes)  
      dk = hashlib.pbkdf2_hmac(
        hash_name="sha256",          
        password=pin.encode("utf-8"), 
        salt=salt,                    
        iterations=spec.iterations,   
        dklen=spec.dklen,             
    )
      return {
        "algo": spec.algo,
        "iterations": spec.iterations,
        "salt_b64": _b64e(salt),
        "hash_b64": _b64e(dk),
    }

def verify_pin(pin: str, auth_blob: Dict[str, Any]) -> bool:
     if auth_blob.get("algo") != "pbkdf2_sha256":
        return False
     try:
        iterations = int(auth_blob["iterations"])
        salt = _b64d(auth_blob["salt_b64"])
        expected = _b64d(auth_blob["hash_b64"])
     except Exception:
        return False

     candidate = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=pin.encode("utf-8"),
        salt=salt,
        iterations=iterations,
        dklen=len(expected),
    )
     return secrets.compare_digest(candidate, expected)

def register_user(users_path: Path, name: str, currency: str, pin: str) -> Dict[str, Any]:
      name = validate_username(name)
      currency = validate_currency(currency)
      pin = validate_pin(pin)

      users = load_users(users_path)
      if find_user_by_name(users, name) is not None:
        raise ValueError("Username already exists. Choose a different name.")

   
      next_id_num = len(users) + 1
      user_id = f"U{next_id_num:03d}"

      record = {
        "user_id": user_id,
        "name": name,
        "currency": currency,
        "auth": hash_pin(pin),
    }
      users.append(record)
      save_users(users_path, users)
      return record

def authenticate(users_path: Path, name: str, pin: str) -> Optional[Dict[str, Any]]:
      name = validate_username(name)
      pin = validate_pin(pin)

      users = load_users(users_path)
      user = find_user_by_name(users, name)
      if user is None:
        return None
      ok = verify_pin(pin, user.get("auth", {}))
      return user if ok else None