"""Deterministic strict-whitelist source packaging; never recursively include outputs."""
import argparse
import hashlib
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parent
FILES=(
    '.gitignore','LICENSE','README.md','THIRD_PARTY_NOTICES.md','VERIFICATION.md',
    'requirements.txt','requirements-lock.txt','config.json','render.py','runtime.py',
    'effects.py','timeline.py','high_fidelity_hook.py','long_film.py','score_long.py',
    'preview.py','build_source_zip.py','tests/test_engine.py',
    'camera_film.py','dynamic_film.py','branding.py','tests/test_dynamic.py',
    'data/official_20261102_04.csv','data/official_archive_20261001_16.csv',
    'data/official_open_data_latest.json','data/october_provenance.json',
    'data/verified_milestones.json','licenses/Pillow-13.0.0-LICENSE.txt',
)


def build(output):
    content={name:(ROOT/name).read_bytes() for name in FILES}
    # Detect absolute machine paths in code/config, not legitimate public URL paths.
    for name,data in content.items():
        if name.endswith(('.py','.json')):
            if re.search(rb'''["']/(?:t[m]p|work[s]pace|ho[m]e)/''',data):
                raise ValueError(f'Unexpected machine-specific path in {name}')
            if re.search(rb'sk-[A-Za-z0-9_-]{20,}',data):
                raise ValueError(f'Potential credential in {name}')
    sums=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(content.items()))
    content['SHA256SUMS']=sums.encode()
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in sorted(content.items()):
            info=zipfile.ZipInfo('taiex_cinematic/'+name,date_time=(2026,11,5,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,data)
    with zipfile.ZipFile(output) as archive:
        expected={'taiex_cinematic/'+name for name in content}
        if set(archive.namelist())!=expected or archive.testzip():raise RuntimeError('Archive integrity or whitelist check failed')
    return hashlib.sha256(output.read_bytes()).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='taiex_cinematic_source.zip');args=parser.parse_args()
    print(build(args.output)+'  '+args.output)
