from django.db import models


class RagLegal(models.Model):
    prefix = models.CharField(max_length=255, primary_key=True)
    key = models.CharField(max_length=255)
    value = models.JSONField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        db_table = "store"
        managed = False

 
    def __str__(self):
        return f"RagLegal {self.key}"
