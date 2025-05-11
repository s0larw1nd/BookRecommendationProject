from django.core.management.base import BaseCommand
import pandas as pd
from base.models import Book, UserRatingExplicit, BookSimilarity
from sklearn.metrics.pairwise import pairwise_distances
import numpy as np

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        ratings = UserRatingExplicit.objects.all().values('user_id', 'isbn_id', 'rating')
        df = pd.DataFrame.from_records(ratings)

        user_item_matrix = df.pivot_table(index='user_id', columns='isbn_id', values='rating')
        matrix_centered = user_item_matrix.sub(user_item_matrix.mean(axis=1), axis=0)
        item_matrix = matrix_centered.T.fillna(0)

        similarity = 1 - pairwise_distances(item_matrix, metric='cosine')
        similarity_df = pd.DataFrame(similarity, index=item_matrix.index, columns=item_matrix.index)

        BookSimilarity.objects.all().delete()
        records = []
        for book_isbn in similarity_df.columns:
            if book_isbn not in similarity_df.index:
                continue
            top_k = similarity_df[book_isbn].drop(book_isbn).sort_values(ascending=False).head(20)
            for similar_isbn, score in top_k.items():
                try:
                    book = Book.objects.get(isbn=book_isbn)
                    similar_book = Book.objects.get(isbn=similar_isbn)
                    records.append(BookSimilarity(book=book, similar_book=similar_book, similarity=score))
                except Book.DoesNotExist:
                    continue

        BookSimilarity.objects.bulk_create(records, batch_size=1000)