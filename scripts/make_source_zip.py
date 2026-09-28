"""Build and verify a source-only handoff archive, without local secrets or runtimes."""
from datetime import datetime
from pathlib import Path
import os
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    '.git', '.venv', 'venv', 'node_modules', '.next', '.npm-cache',
    '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    'artifacts', 'releases', '.codex', '.agents', '.vercel',
}


def excluded_file(name):
    lower = name.lower()
    return (
        (lower.startswith('.env') and lower != '.env.example')
        or lower.endswith(('.db', '.sqlite', '.sqlite3', '.pyc', '.pyo', '.log', '.tsbuildinfo', '.zip', '.pem', '.key'))
        or '.db-' in lower or '.sqlite-' in lower or '.sqlite3-' in lower
    )


def main():
    output_dir = ROOT / 'releases'
    output_dir.mkdir(exist_ok=True)
    output = output_dir / f'priceactioner-source-{datetime.now():%Y%m%d-%H%M%S}.zip'
    count = 0
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for directory, dirs, files in os.walk(ROOT):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS
                             and (Path(directory) / d).resolve() != ROOT / 'backend' / 'data'
                             and not (Path(directory) / d).is_symlink())
            for name in sorted(files):
                path = Path(directory) / name
                if excluded_file(name) or path.is_symlink():
                    continue
                relative = path.relative_to(ROOT)
                archive.write(path, 'priceactioner/' + relative.as_posix())
                count += 1
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f'Archive CRC failed: {bad}')
        for name in archive.namelist():
            parts = Path(name).parts
            if any(part in EXCLUDED_DIRS for part in parts) or excluded_file(parts[-1]) or '/backend/data/' in name:
                raise RuntimeError(f'Unexpected private/generated file in archive: {name}')
        required = ['README.md', 'frontend/package-lock.json', 'backend/requirements.txt',
                    'backend/.env.example', 'docs/DEPLOYMENT.fa.md']
        for name in required:
            if 'priceactioner/' + name not in archive.namelist():
                raise RuntimeError(f'Missing required source file: {name}')
    print(f'Created: {output}')
    print(f'Files: {count}; size: {output.stat().st_size / 1024 / 1024:.2f} MiB; CRC verified.')
    print('Excluded: credentials, local database, installed dependencies, build output, caches and logs.')


if __name__ == '__main__':
    main()
