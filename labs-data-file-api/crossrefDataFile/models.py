import re

from django.db import models


class DataIndex(models.Model):
    doi = models.TextField(db_index=True)
    file_name = models.TextField()

    def __str__(self):
        return 'Data index for {} in {}'.format(self.doi, self.file_name)


class DataIndexWithLocation(models.Model):
    doi = models.TextField(db_index=True)
    file_name = models.TextField()
    location = models.IntegerField()

    def __str__(self):
        return 'Data index for {} in {} at offset {}'.format(self.doi,
                                                             self.file_name,
                                                             self.location)

