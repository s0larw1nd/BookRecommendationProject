from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from base.models import UserRatingExplicit, UserRatingImplicit, Book, BookFactors, UserFactors
import numpy as np

def train_svdpp(train_data, implicit_data, 
                n_users, n_items, 
                f=40,
                lr=0.001, reg=0.02, n_epochs=10):
        
        mu = np.mean([r for _, _, r in train_data])
        bu = np.zeros(n_users)
        bi = np.zeros(n_items)
        P = np.random.normal(0, 0.01, (n_users, f))
        Q = np.random.normal(0, 0.01, (n_items, f))
        Y = np.random.normal(0, 0.01, (n_items, f))

        Nu = {u: [] for u in range(n_users)}
        for u, i in implicit_data:
            Nu[u].append(i)

        for epoch in range(n_epochs):
            epoch_err = 0
            k = 0
            for u, i, r in train_data:
                sqrt_Nu = np.sqrt(max(len(Nu[u]), 1e-6))
                y_sum = np.sum(Y[Nu[u]], axis=0) / sqrt_Nu

                pred = mu + bu[u] + bi[i] + P[u].dot(Q[i] + y_sum)

                err = r - pred

                epoch_err += abs(err)
                k += 1

                bu[u] += lr * (err - reg * bu[u])
                bi[i] += lr * (err - reg * bi[i])

                P[u] += lr * (err * (Q[i] + y_sum) - reg * P[u])
                Q[i] += lr * (err * (P[u] + y_sum) - reg * Q[i])

                for j in Nu[u]:
                    Y[j] += lr * (err * Q[i] / sqrt_Nu - reg * Y[j])
            
            print(epoch, epoch_err/k)

            lr *= 0.99

        return mu, bu, bi, P, Q, Y

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        explicit_qs = UserRatingExplicit.objects.values_list('user_id', 'isbn', 'rating')
        implicit_qs = UserRatingImplicit.objects.values_list('user_id', 'isbn')

        books = Book.objects.values_list('isbn', flat=True).distinct()
        isbn2idx = {isbn: idx for idx, isbn in enumerate(books)}
        user_ids = list({u for u, _, _ in explicit_qs} | {u for u, _ in implicit_qs})
        user2idx = {u: idx for idx, u in enumerate(user_ids)}

        train_data = [
            (user2idx[u], isbn2idx[isbn], float(r))
            for u, isbn, r in explicit_qs
        ]

        implicit_data = [
            (user2idx[u], isbn2idx[isbn])
            for u, isbn in implicit_qs
        ]
        
        mu, bu, bi, P, Q, Y = train_svdpp(train_data, implicit_data, n_users=User.objects.all().count(), n_items=Book.objects.all().count())

        UserFactors.objects.all().delete()
        BookFactors.objects.all().delete()

        user_objs = [
            UserFactors(
                user_id=u_id,
                bias=float(bu[user_idx]),
                factors=P[user_idx].tolist()
            )
            for u_id, user_idx in user2idx.items()
        ]

        book_objs = [
            BookFactors(
                isbn=isbn,
                bias=float(bi[item_idx]),
                factors=Q[item_idx].tolist(),
                implicit=Y[item_idx].tolist()
            )
            for isbn, item_idx in isbn2idx.items()
        ]

        UserFactors.objects.bulk_create(user_objs, batch_size=500)
        BookFactors.objects.bulk_create(book_objs, batch_size=500)