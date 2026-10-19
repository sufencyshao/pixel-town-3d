#!/usr/bin/env python3
"""Restore allowlisted release assets without overwriting a working tree."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'sufencyshao/pixel-town-3d'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Use an existing full source ZIP')
    parser.add_argument('--dry-run', action='store_true', help='Verify ZIP and plan without writing assets')
    args = parser.parse_args()
    spec = json.loads((ROOT / 'catalog/restore-assets.json').read_text(encoding='utf-8'))
    archive = args.archive
    if archive is None:
        archive = ROOT / '.cache' / spec['archive']
        if not archive.exists():
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not shutil.which('gh'):
                parser.error('Install and sign in to GitHub CLI, or pass --archive PATH.')
            subprocess.run(['gh', 'release', 'download', spec['tag'], '--repo', REPOSITORY,
                            '--pattern', spec['archive'], '--dir', str(archive.parent)], check=True)
    archive = archive.resolve()
    print('Checking full source ZIP SHA-256...', flush=True)
    if digest(archive) != spec['sha256']:
        raise SystemExit('Archive checksum does not match this checkout; no assets changed.')
    restored = skipped = conflicts = 0
    with zipfile.ZipFile(archive) as source:
        plan = []
        for row in spec['files']:
            relative = PurePosixPath(row['file'])
            if relative.is_absolute() or '..' in relative.parts or '\\' in row['file']:
                raise SystemExit('Unsafe manifest path.')
            dest = ROOT.joinpath(*relative.parts)
            if not dest.resolve().is_relative_to(ROOT):
                raise SystemExit('Asset destination escapes repository (including symlink).')
            if dest.exists():
                if dest.is_file() and dest.stat().st_size == row['bytes'] and digest(dest) == row['sha256']:
                    skipped += 1
                    continue
                print('Keep modified file:', row['file'])
                conflicts += 1
                continue
            info = source.getinfo(spec['prefix'] + row['file'])
            if info.file_size != row['bytes'] or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise SystemExit('Unexpected ZIP entry: ' + row['file'])
            plan.append((row, dest, info))
        # Check conflicts before any writes, so a conflict leaves the tree unchanged.
        if conflicts:
            raise SystemExit(f'{conflicts} existing files differ; no assets restored. Resolve them and retry.')
        if args.dry_run:
            print(f'ZIP verified. Would restore {len(plan)} files; {skipped} already correct.')
            return
        for row, dest, info in plan:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = None
            try:
                with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as output:
                    tmp = Path(output.name)
                    with source.open(info) as src:
                        shutil.copyfileobj(src, output, length=1024 * 1024)
                if digest(tmp) != row['sha256']:
                    raise SystemExit('Asset checksum mismatch: ' + row['file'])
                if os.name == 'posix' and (info.external_attr >> 16) & 0o111:
                    os.chmod(tmp, 0o755)
                # Atomic no-overwrite installation. A concurrent edit is preserved.
                os.link(tmp, dest)
                restored += 1
            finally:
                if tmp and tmp.exists():
                    tmp.unlink()
    print(f'Restored and verified {restored} files; {skipped} already correct.')


if __name__ == '__main__':
    main()
