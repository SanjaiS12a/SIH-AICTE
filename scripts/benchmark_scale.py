"""Create and remove only this run's disposable scale-test database."""
import subprocess,uuid,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
name='coordination_scale_'+uuid.uuid4().hex[:12]
def run(*args,**kwargs):return subprocess.run(['docker','compose',*args],cwd=ROOT,check=True,**kwargs)
# Name is generated locally and constrained before passing to database utilities.
assert name.startswith('coordination_scale_') and name.replace('_','').isalnum()
created=False
try:
 run('exec','-T','db','createdb','-U','coordination',name);created=True
 run('run','--rm','--no-deps','-e','POSTGRES_DB='+name,'api','python','manage.py','migrate','--noinput')
 run('run','--rm','--no-deps','-e','POSTGRES_DB='+name,'api','python','manage.py','benchmark_scale',*sys.argv[1:])
finally:
 if created:run('exec','-T','db','dropdb','-U','coordination',name)
