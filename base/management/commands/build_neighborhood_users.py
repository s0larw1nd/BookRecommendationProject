from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import pandas as pd
from base.models import UserRatingExplicit, UserSimilarity
from sklearn.metrics.pairwise import pairwise_distances
import numpy as np

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        ratings = UserRatingExplicit.objects.all().values('user_id', 'isbn_id', 'rating')
        df = pd.DataFrame.from_records(ratings)

        user_item_matrix = df.pivot_table(index='user_id', columns='isbn_id', values='rating')

        user_means = user_item_matrix.mean(axis=1)
        user_counts = user_item_matrix.count(axis=1)
        user_means_smoothed = user_means.where(user_counts >= 5, 0)
        matrix_centered = user_item_matrix.sub(user_means_smoothed, axis=0)

        user_matrix = matrix_centered.fillna(0)

        user_similarity = 1 - pairwise_distances(user_matrix, metric='cosine')
        user_similarity_df = pd.DataFrame(user_similarity, index=user_matrix.index, columns=user_matrix.index)

        UserSimilarity.objects.all().delete()
        records = []
        for user_id in user_similarity_df.columns:
            if user_id not in user_similarity_df.index:
                continue
            top_k = user_similarity_df[user_id].drop(user_id).sort_values(ascending=False).head(20)
            for similar_id, score in top_k.items():
                try:
                    user = User.objects.get(id=user_id)
                    similar_user = User.objects.get(id=similar_id)
                    records.append(UserSimilarity(user=user, similar_user=similar_user, similarity=score))
                except User.DoesNotExist:
                    continue

        UserSimilarity.objects.bulk_create(records, batch_size=1000)