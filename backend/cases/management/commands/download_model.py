import json
import os
import hashlib
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Download and verify MiniLM once for later offline operation.'
    def handle(self, *args, **options):
        from huggingface_hub import snapshot_download
        frozen = json.loads((settings.BASE_DIR / 'model-manifest.json').read_text())
        revision = frozen['revision']
        path = Path(settings.MODEL_PATH)
        snapshot_download(frozen['model'], revision=revision, local_dir=path,
            allow_patterns=['*.json','*.txt','LICENSE','*.safetensors','1_Pooling/*'], ignore_patterns=['onnx/*','openvino/*'])
        with (path/'model.safetensors').open('rb') as weights:
            actual = hashlib.file_digest(weights, 'sha256').hexdigest()
        if actual != frozen['weights_sha256']: raise CommandError('Downloaded weights do not match the frozen baseline.')
        (path/'revision.json').write_text(json.dumps(frozen),encoding='utf-8')
        from cases.matching import encoder, tokenizer
        assert len(encoder().encode('Local model verification.')) == 384
        assert len(tokenizer().encode('A short complaint.').ids) < 256
        self.stdout.write(self.style.SUCCESS(f'Model verified at {path}; revision {revision}'))
