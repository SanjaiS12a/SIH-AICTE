from django.core.cache import caches
cache = caches['dashboard']
from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from .models import Complaint,OverlapCandidate,Institution,Bureau

@receiver(post_save,sender=Complaint)
@receiver(post_save,sender=OverlapCandidate)
@receiver(post_save,sender=Institution)
@receiver(post_save,sender=Bureau)
@receiver(post_delete,sender=Complaint)
def invalidate_dashboard(sender,**kwargs):
 cache.clear()
