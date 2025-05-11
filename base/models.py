from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField

# Create your models here.
class Book(models.Model):
    isbn = models.TextField(unique=True)
    title = models.TextField(null=True)
    author = models.TextField(null=True)
    publication_year = models.TextField(null=True)
    publisher = models.TextField(null=True)
    image_s = models.TextField(null=True)
    image_m = models.TextField(null=True)
    image_l = models.TextField(null=True)

    def __str__(self):
        return self.title

class UserAge(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    age = models.IntegerField(null=True)

    def __str__(self):
        return str(self.age)

class UserLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    city = models.TextField(null=True)
    region = models.TextField(null=True)
    country = models.TextField(null=True)

    def __str__(self):
        return f"{self.city},{self.region},{self.country}"
    
class UserRatingImplicit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    isbn = models.ForeignKey(Book, to_field='isbn', on_delete=models.CASCADE)

class UserRatingExplicit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    isbn = models.ForeignKey(Book, to_field='isbn', on_delete=models.CASCADE)
    rating = models.IntegerField()

class UserComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    isbn = models.ForeignKey(Book, to_field='isbn', on_delete=models.CASCADE)
    comment = models.TextField(null=True)

class UserContentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    vector = VectorField(null=True)

class BookContentProfile(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, primary_key=True)
    vector = VectorField(null=True)

class BookSimilarity(models.Model):
    book = models.ForeignKey(Book, related_name='similarities', on_delete=models.CASCADE)
    similar_book = models.ForeignKey(Book, related_name='similar_to', on_delete=models.CASCADE)
    similarity = models.FloatField()

    class Meta:
        unique_together = ('book', 'similar_book')
        indexes = [
            models.Index(fields=['book']),
            models.Index(fields=['similar_book']),
        ]

class UserSimilarity(models.Model):
    user = models.ForeignKey(User, related_name='similarities', on_delete=models.CASCADE)
    similar_user = models.ForeignKey(User, related_name='similar_to', on_delete=models.CASCADE)
    similarity = models.FloatField()

    class Meta:
        unique_together = ('user', 'similar_user')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['similar_user']),
        ]

class UserFactors(models.Model):
    user_id = models.IntegerField(unique=True)
    bias = models.FloatField()
    factors = VectorField(dimensions=40)

class BookFactors(models.Model):
    isbn = models.CharField(max_length=20, unique=True)
    bias = models.FloatField()
    factors = VectorField(dimensions=40)
    implicit = VectorField(dimensions=40)