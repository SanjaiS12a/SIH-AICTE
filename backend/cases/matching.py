import json
import logging
import time
from functools import lru_cache
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from pgvector.django import CosineDistance
from rest_framework.exceptions import APIException
from .models import Complaint, OverlapCandidate, ModelRelease
from .evidence import build_evidence

logger = logging.getLogger(__name__)

class ModelUnavailable(APIException):
    status_code = 503
    default_detail = 'The local matching model is not ready. Run the model download step first.'

def runtime():
    active = ModelRelease.objects.filter(active=True).first()
    if active:
        return str(Path(settings.MODEL_PATH).parent / active.path), active.revision, active.threshold
    return baseline_runtime(str(settings.MODEL_PATH), settings.MATCH_THRESHOLD)


@lru_cache(maxsize=1)
def baseline_runtime(model_path, default_threshold):
    # Baseline files are immutable during serving; releases switch through the database.
    path = Path(model_path)
    manifest = path / 'revision.json'
    model_revision = json.loads(manifest.read_text())['revision'] if manifest.exists() else settings.MODEL_REVISION
    calibration = Path(__file__).parent.parent / 'calibration.json'
    cutoff = json.loads(calibration.read_text())['threshold'] if calibration.exists() else default_threshold
    return str(path), model_revision, cutoff


def tokenizer():
    return cached_tokenizer(runtime()[0])


@lru_cache(maxsize=1)
def cached_tokenizer(model_path):
    from tokenizers import Tokenizer
    try:
        result = Tokenizer.from_file(str(Path(model_path) / 'tokenizer.json'))
        result.no_truncation()
        result.no_padding()
        return result
    except Exception as exc:
        raise ModelUnavailable() from exc

def encoder():
    return cached_encoder(runtime()[0])


@lru_cache(maxsize=1)
def cached_encoder(model_path):
    from sentence_transformers import SentenceTransformer
    import torch
    torch.set_num_threads(2)
    return SentenceTransformer(model_path, device='cpu', local_files_only=True)

def revision():
    return runtime()[1]


def threshold():
    return runtime()[2]

def match_case(case_id, vector=None, encoded_revision=None):
    started = time.perf_counter()
    try:
        case = Complaint.objects.get(pk=case_id)
        queue_ms = max(0, (timezone.now() - case.created_at).total_seconds() * 1000)
        path, model, cutoff = runtime()
        if vector is None:
            encoded_revision = model
            vector = encoder().encode(case.summary, normalize_embeddings=True).tolist()
        elif encoded_revision is None:
            encoded_revision = model
        with transaction.atomic():
            # Serialize institution matching so simultaneous submissions see each other's vectors.
            from .models import Institution
            Institution.objects.select_for_update().get(pk=case.institution_id)
            case.refresh_from_db()
            if revision() != encoded_revision:
                raise RuntimeError('Model switched during encoding; retry with the active revision.')
            Complaint.objects.filter(pk=case_id).update(embedding=vector, model_revision=model)
            neighbors = (Complaint.objects.filter(institution=case.institution, embedding__isnull=False, model_revision=model)
                         .exclude(pk=case_id).annotate(distance=CosineDistance('embedding', vector))
                         .order_by('distance')[:5])
            suggestions = []
            for other in neighbors:
                score = 1 - float(other.distance)
                if score < cutoff:
                    continue
                left, right = sorted([case.id, other.id])
                other.institution = case.institution  # Retrieval already guarantees this canonical institution.
                ordered = (case, other) if left == case.id else (other, case)
                evidence = build_evidence(*ordered, score=score, model_revision=model)
                suggestions.append(OverlapCandidate(left_id=left, right_id=right, score=score, model_revision=model, evidence=evidence))
            if suggestions:
                from django.db.models import Q
                pairs = Q(pk__in=[])
                for suggestion in suggestions:
                    pairs |= Q(left_id=suggestion.left_id, right_id=suggestion.right_id)
                existing = {(c.left_id, c.right_id): c for c in OverlapCandidate.objects.filter(pairs)}
                OverlapCandidate.objects.bulk_create([c for c in suggestions if (c.left_id, c.right_id) not in existing], ignore_conflicts=True)
                updates = []
                for suggestion in suggestions:
                    old = existing.get((suggestion.left_id, suggestion.right_id))
                    if old and old.decision == 'pending' and (old.score, old.model_revision, old.evidence) != (suggestion.score, model, suggestion.evidence):
                        old.score, old.model_revision, old.evidence = suggestion.score, model, suggestion.evidence
                        old.version += 1
                        updates.append(old)
                if updates:
                    OverlapCandidate.objects.filter(decision='pending').bulk_update(updates, ['score', 'model_revision', 'evidence', 'version'])
            Complaint.objects.filter(pk=case_id).update(matching_state='complete', matching_error='', matched_at=timezone.now(),
                matching_duration_ms=(time.perf_counter()-started)*1000, matching_queue_ms=queue_ms)
    except Exception:
        Complaint.objects.filter(pk=case_id).update(matching_state='failed', matching_error='Matching failed. Coordinator can retry; see worker logs.')
        logger.exception('Matching failed for case %s', case_id)
        raise


def match_batch(case_ids):
    cases = list(Complaint.objects.filter(pk__in=case_ids, matching_state='pending'))
    if not cases:
        return
    try:
        encoded_revision = revision()
        missing = [case for case in cases if case.embedding is None or case.model_revision != encoded_revision]
        encoded = encoder().encode([case.summary for case in missing], normalize_embeddings=True, batch_size=32) if missing else []
        fresh = {case.pk: vector.tolist() for case, vector in zip(missing, encoded)}
        vectors = [fresh[case.pk] if case.pk in fresh else list(case.embedding) for case in cases]
    except Exception:
        Complaint.objects.filter(pk__in=[c.pk for c in cases]).update(matching_state='failed', matching_error='Batch encoding failed; retry after checking worker logs.')
        raise
    failures = []
    for case, vector in zip(cases, vectors):
        try:
            match_case(str(case.pk), vector, encoded_revision)
        except Exception:
            failures.append(str(case.pk))
    from django.core.cache import caches
    caches['dashboard'].clear()
    if failures:
        raise RuntimeError(f'{len(failures)} cases failed matching; successful cases retained.')
