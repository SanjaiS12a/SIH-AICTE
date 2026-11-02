from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('cases', '0017_core_evidence_protection')]
    operations = [
        migrations.AddField(model_name='importjob', name='category_mapping', field=models.JSONField(default=dict)),
        migrations.AlterField(model_name='complaint', name='category', field=models.CharField(max_length=30, choices=[
            ('admissions','Admissions'),('refunds','Refunds'),('documents','Documents'),('facilities','Facilities'),
            ('scholarships','Scholarships'),('administration','Administration'),('other','Other'),('needs_categorization','Needs categorization')])),
    ]
