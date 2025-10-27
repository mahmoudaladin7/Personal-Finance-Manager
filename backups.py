from __future__ import annotations

import io
import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Dict, Any, List, Optional, Tuple
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo


def _now_stamp()-> str:
     return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

def _sha256_bytes(data: bytes) -> str:
   
    return hashlib.sha256(data).hexdigest()

def _sha256_file(path: Path) -> str:

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class BackupSpec:
   
    backup_dir: Path
    files: List[Path]

def create_backup(spec: BackupSpec) -> Path:
    
    spec.backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = _now_stamp()
    zip_path = spec.backup_dir / f"backup-{stamp}.zip"

    # Read files → compute checksums/sizes → write to zip
    manifest: Dict[str, Dict[str, Any]] = {"files": {}}
    memory_files: List[Tuple[str, bytes]] = []

    for p in spec.files:
        if not p.exists():
            continue
        data = p.read_bytes()
        memory_files.append((p.name, data))
        manifest["files"][p.name] = {
            "size": len(data),
            "sha256": _sha256_bytes(data),
        }

    # Write ZIP
    with ZipFile(zip_path, mode="w", compression=ZIP_DEFLATED) as zf:
        # Add data files
        for arcname, data in memory_files:
            zf.writestr(arcname, data)

        # Add manifest last (not hashed inside itself)
        manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
        zf.writestr("manifest.json", manifest_bytes)

    return zip_path

def list_backups(backup_dir: Path) -> List[Path]:
   
    if not backup_dir.exists():
        return []
    zips = [p for p in backup_dir.iterdir() if p.is_file() and p.name.startswith("backup-") and p.suffix == ".zip"]
    return sorted(zips, key=lambda p: p.name, reverse=True)

def verify_backup(zip_path: Path) -> Tuple[bool, List[str]]:
  
    errors: List[str] = []
    with ZipFile(zip_path, "r") as zf:
        # Load manifest
        try:
            manifest_bytes = zf.read("manifest.json")
        except KeyError:
            return False, ["manifest.json missing in ZIP"]

        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except Exception:
            return False, ["manifest.json is not valid JSON"]

        meta: Dict[str, Dict[str, Any]] = manifest.get("files", {})
        # Verify each file referenced by manifest
        for fname, info in meta.items():
            try:
                data = zf.read(fname)
            except KeyError:
                errors.append(f"{fname}: not found in ZIP")
                continue
            size_ok = len(data) == int(info.get("size", -1))
            hash_ok = _sha256_bytes(data) == info.get("sha256", "")
            if not size_ok:
                errors.append(f"{fname}: size mismatch")
            if not hash_ok:
                errors.append(f"{fname}: SHA-256 mismatch")

        # Optionally: warn about extra files not in manifest
        zip_names = set(zf.namelist()) - {"manifest.json"}
        manifest_names = set(meta.keys())
        extra = zip_names - manifest_names
        if extra:
            errors.append(f"Extra files not declared in manifest: {sorted(extra)}")

    return (len(errors) == 0), errors

def restore_backup(zip_path: Path, dest_dir: Path, *, overwrite: bool = False) -> List[Path]:
    
    restored: List[Path] = []
    allowed = {"users.json", "transactions.csv"}

    dest_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name == "manifest.json":
                continue
            if name not in allowed:
                continue
            target = dest_dir / name
            if target.exists() and not overwrite:
                raise FileExistsError(f"Target exists: {target} (use overwrite=True)")
            data = zf.read(name)
            target.write_bytes(data)
            restored.append(target)

    return restored