# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from tagging.fields import TagField


class Document(models.Model):

    hash_md5 = models.CharField(max_length=32, unique=True)
    hash_ssdeep = models.TextField()
    mime_type = models.CharField(max_length=64)
    content = models.TextField()
    document_path = models.CharField(max_length=128)
    document_size = models.PositiveIntegerField()
    thumbnail_path = models.CharField(max_length=128)
    language_code = models.CharField(max_length=2)
    tags = TagField()
    owner = models.ForeignKey(User)
