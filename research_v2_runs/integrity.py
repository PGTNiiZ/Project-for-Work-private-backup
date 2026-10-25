"""Sealed-resource boundary; contains no dataset-specific identifiers."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def require_committed(path):
    path = Path(path).resolve()
    root = Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=path.parent,text=True).strip())
    rel = path.relative_to(root).as_posix()
    try:
        content = subprocess.check_output(['git','show',f'HEAD:{rel}'],cwd=root,stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as exc:
        raise PermissionError('configuration is not committed') from exc
    if hashlib.sha256(content).hexdigest() != sha256(path):
        raise PermissionError('configuration changed after commit')
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()


def guarded_read(resource, *, final, config_id, lock, access_log):
    if not final:
        raise PermissionError('sealed test requires --final')
    if not lock or config_id not in lock['configs']:
        raise PermissionError('configuration not predeclared')
    root = Path(lock['root'])
    doc = root/lock['document']
    if sha256(doc) != lock['document_sha256']:
        raise PermissionError('final declaration hash changed')
    commit = require_committed(doc)
    for rel, expected in lock['configs'][config_id]['artifact_hashes'].items():
        if sha256(root/rel) != expected:
            raise PermissionError('frozen artifact changed')
    rel = Path(resource).resolve().relative_to(root.resolve()).as_posix()
    if rel not in lock['resource_hashes']:
        raise PermissionError('undeclared sealed resource')
    access_log = Path(access_log)
    if access_log.exists():
        for line in access_log.read_text().splitlines():
            event = json.loads(line)
            if event['config_id'] == config_id and event['resource'] == rel:
                raise PermissionError('configuration already opened sealed resource')
    access_log.parent.mkdir(parents=True,exist_ok=True)
    with access_log.open('a') as f:
        f.write(json.dumps({'config_id':config_id,'resource':rel,'timestamp':dt.datetime.now(dt.timezone.utc).isoformat(),'authorization_commit':commit,'event':'AUTHORIZED_FINAL_OPEN'})+'\n')
    data = Path(resource).read_bytes()
    if hashlib.sha256(data).hexdigest() != lock['resource_hashes'][rel]:
        raise PermissionError('sealed resource hash changed')
    return data
