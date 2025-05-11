from django.core.management.base import BaseCommand
from base.models import Book, UserRatingExplicit, UserContentProfile
from sklearn.preprocessing import OneHotEncoder
from django.db.models import Max, Min, Avg, Q
from django.contrib.auth.models import User
import numpy as np
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix, vstack

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("Начинаю обработку книг...")

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

        user_profiles = None

        for user in User.objects.all():
            vectors = []
            r = 0
            for ratings in UserRatingExplicit.objects.filter(user=user):
                book = ratings.isbn
                author_vector = enc_authors.transform([[book.author]]).toarray().tolist()[0]
                publisher_vector = enc_publishers.transform([[book.publisher]]).toarray().tolist()[0]
                if 1900 < int(book.publication_year) < 2020:
                    year_value = (int(book.publication_year) - min_year)/(max_year - min_year)
                else:
                    year_value = avg_year
                user_vector = [year_value] + author_vector + publisher_vector
                user_vector = np.array(user_vector) * ratings.rating
                
                vectors.append(user_vector)
                r += ratings.rating
            
            user_vector = np.array(vectors)
            if user_vector.size>0:
                user_profile = np.sum(user_vector, axis=0) / r
            else:
                user_profile = np.zeros(7455)
            
            if user_profiles is None:
                user_profiles = csr_matrix(np.array([user_profile]))
            else:
                user_profiles = vstack([user_profiles, user_profile])

        svd = TruncatedSVD(n_components=100, random_state=42)
        user_profiles = svd.fit_transform(user_profiles)

        UserContentProfile.objects.all().delete()

        for i, user in enumerate(User.objects.all(), start=0):
            UserContentProfile.objects.update_or_create(
                user = user,
                vector = user_profiles[i]
            )