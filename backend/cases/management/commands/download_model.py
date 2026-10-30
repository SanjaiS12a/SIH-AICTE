import json
import os
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Download and verify MiniLM once for later offline operation.'
    def handle(self, *args, **options):
        from huggingface_hub import snapshot_download, HfApi
        revision = HfApi().model_info(settings.MODEL_REVISION).sha
        path = Path(settings.MODEL_PATH)
        snapshot_download(settings.MODEL_REVISION, revision=revision, local_dir=path,
            allow_patterns=['*.json','*.txt','*.safetensors','1_Pooling/*'], ignore_patterns=['onnx/*','openvino/*'])
        (path/'revision.json').write_text(json.dumps({'model':settings.MODEL_REVISION,'revision':revision}),encoding='utf-8')
        from cases.matching import encoder, tokenizer
        assert len(encoder().encode('Local model verification.')) == 384
        assert len(tokenizer().encode('A short complaint.').ids) < 256
        self.stdout.write(self.style.SUCCESS(f'Model verified at {path}; revision {revision}'))
