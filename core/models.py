from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.fields import JSONField

# Create your models here.


class Media(models.Model):
	file = models.FileField()
	alive = models.BooleanField(null=False, default=True)

	def __str__(self):
		return self.file.url


class Category(models.Model):
	name = models.TextField()
	visible = models.BooleanField(null=False, default=True)
	alive = models.BooleanField(null=False, default=True)

	def __str__(self):
		return self.name


class Tag(models.Model):
	name = models.TextField()
	alive = models.BooleanField(null=False, default=True)

	def __str__(self):
		return self.name


class Post(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	created = models.DateField(auto_now_add=True, blank=True)
	name = models.TextField()
	description = models.TextField()
	category = models.ForeignKey(Category, on_delete=models.CASCADE)
	body = models.TextField()
	media = models.ManyToManyField(Media, blank=True)
	data = JSONField(null=True)
	views = models.IntegerField(null=True, default=0)
	share = models.IntegerField(null=True, default=0)
	likes = models.IntegerField(null=True, default=0)
	tag = models.ManyToManyField(Tag, blank=True)
	visible = models.BooleanField(null=False, default=True)
	search = SearchVectorField(null=True)
	alive = models.BooleanField(null=False, default=True)

	def __str__(self):
		return self.name
