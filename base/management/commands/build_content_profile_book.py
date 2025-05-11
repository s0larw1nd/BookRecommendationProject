from django.core.management.base import BaseCommand
from base.models import Book, UserRatingExplicit, UserContentProfile, BookContentProfile
from sklearn.preprocessing import OneHotEncoder
from django.db.models import Max, Min, Avg, Q
from django.contrib.auth.models import User
import numpy as np
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix, vstack

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        publishers = set()
        enc_publishers = OneHotEncoder(handle_unknown='ignore')
        authors = set()
        enc_authors = OneHotEncoder(handle_unknown='ignore')

        for book in Book.objects.all():
            publishers.add(book.publisher)
            authors.add(book.author)

        enc_publishers.fit([[i] for i in publishers])
        enc_authors.fit([[i] for i in authors])

        query = Book.objects.filter(Q(publication_year__lt=2020) & Q(publication_year__gt=1900)).aggregate(Max('publication_year'), Min('publication_year'))
        max_year = int(query['publication_year__max'])
        min_year = int(query['publication_year__min'])
        
        avg_year = int((max_year + min_year) / 2)

        book_profiles = None

        for book in Book.objects.all():
            author_vector = enc_authors.transform([[book.author]]).toarray().tolist()[0]
            publisher_vector = enc_publishers.transform([[book.publisher]]).toarray().tolist()[0]

            if 1900 < int(book.publication_year) < 2020:
                year_value = (int(book.publication_year) - min_year)/(max_year - min_year)
            else:
                year_value = avg_year

            book_vector = np.array([year_value] + author_vector + publisher_vector)

            if book_profiles is None:
                book_profiles = csr_matrix(np.array([book_vector]))
            else:
                book_profiles = vstack([book_profiles, book_vector])

        svd = TruncatedSVD(n_components=100, random_state=42)
        book_profiles = svd.fit_transform(book_profiles)

        BookContentProfile.objects.all().delete()

        for i, book in enumerate(Book.objects.all(), start=0):
            BookContentProfile.objects.update_or_create(
                book = book,
                vector = book_profiles[i]
            )