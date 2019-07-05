from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.fields import JSONField


# Create your models here.


class Media(models.Model):
	image = models.FileField()
	alive = models.BooleanField(null=False, default=True)

	def __str__(self):
		return self.image.url


class Category(models.Model):
	name = models.TextField()
	alive = models.BooleanField(null=False, default=True)

	def __str__(self):
		return self.name


class Blog(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	created = models.DateField()
	name = models.TextField()
	category = models.ForeignKey(Category, on_delete=models.CASCADE)
	media = models.ManyToManyField(Media, blank=True)
	data = JSONField()
	search = SearchVectorField(null=True)
	alive = models.BooleanField(null=False, default=True)

	def __str__(self):
		return self.created
