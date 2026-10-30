from django.db import migrations
from django.core.management import call_command

def create_cache(apps,schema_editor):
 call_command('createcachetable','dashboard_cache',database=schema_editor.connection.alias,verbosity=0)

class Migration(migrations.Migration):
 dependencies=[('cases','0003_modelrelease')]
 operations=[migrations.RunPython(create_cache,migrations.RunPython.noop)]
