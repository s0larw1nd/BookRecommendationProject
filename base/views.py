from django.shortcuts import render, redirect
from django.views import View
from .models import Book, UserAge, UserLocation, UserRatingImplicit, UserRatingExplicit, UserComment, UserContentProfile, BookContentProfile, BookSimilarity, UserSimilarity, UserFactors, BookFactors
from django.contrib.auth.models import User
from django.db.models import Avg
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from pgvector.django import CosineDistance
from django.db.models import F

from scipy.spatial import distance

# Create your views here.
    
class HomeView(View):
    @staticmethod
    def calculate_recommendations_content(user):
        user_profile = UserContentProfile.objects.get(user = user).vector

        books = BookContentProfile.objects.annotate(
            distance=CosineDistance(F('vector'), user_profile)
        ).order_by('distance')

        return [b.book for b in books[:20]]
    
    @staticmethod
    def calculate_recommedations_neighborhood_item(user):
        books_rated = [b.isbn_id for b in UserRatingExplicit.objects.filter(user=user).order_by('-rating')]
        recommendations = []
        for book in books_rated:
            obook = Book.objects.get(isbn=book)
            if len(recommendations) >= 20:
                recommendations = recommendations[:20]
                break
            for sbook in BookSimilarity.objects.filter(book=obook).order_by('-similarity'):
                recommendations.append(sbook.similar_book)
        
        return recommendations
    
    @staticmethod
    def calculate_recommedations_neighborhood_user(user):
        similar_users = UserSimilarity.objects.filter(user=user).order_by('-similarity').values('similar_user','similarity')
        rated_books = {}
        
        for sim_user in similar_users:
            ratings = UserRatingExplicit.objects.filter(user=sim_user['similar_user']).values('isbn','rating')
            for r in ratings:
                if r['isbn'] not in rated_books: rated_books[r['isbn']] = []
                if sim_user['similarity'] > 0:
                    rated_books[r['isbn']].append([r['rating'], sim_user['similarity']])

        ratings_books = [] 
        for book_isbn, book_ratings in rated_books.items():
            if not book_ratings: continue
            predicted = 0
            similarities = 0
            for book_rating in book_ratings:
                predicted += book_rating[0] * book_rating[1]
                similarities += abs(book_rating[1])
            ratings_books.append([book_isbn, predicted/similarities])

        ratings_books = sorted(ratings_books, key=lambda x: x[1], reverse=True)[:20]
        recommendations = []

        for item in ratings_books:
            recommendations.append(Book.objects.get(isbn=item[0]))
        
        return recommendations
    
    @staticmethod
    def calculate_recommedations_svdpp(user):
        user = UserFactors.objects.get(user_id=user.id)
        top_items = (
            BookFactors.objects
            .annotate(sim=CosineDistance("factors", user.factors))
            .order_by("sim")[:20]
        )

        recommendations = []
        for ti in top_items:
            recommendations.append(Book.objects.get(isbn=ti.isbn))

        return recommendations

    def get(self, request):
        q = request.GET.get('q') if request.GET.get('q') != None else ''
        if q:
            books = Book.objects.filter(title__icontains=q)[:20]
        elif self.request.user.is_authenticated:
            books = HomeView.calculate_recommedations_neighborhood_user(request.user)[:20]
        else:
            books = Book.objects.all()[:20]
        context = {
            'books': books
        }
        return render(request, 'base/home.html', context)
    
class BookView(View):
    def get(self, request, pk):
        book = Book.objects.get(id = pk)
        ratings = UserRatingExplicit.objects.filter(isbn = book.isbn)
        k_ratings = len(list(ratings))
        avg_rating = ratings.aggregate(avg=Avg('rating'))['avg']
        average = round(avg_rating,2) if avg_rating is not None else 'Нет оценок'
        if self.request.user.is_authenticated and UserRatingExplicit.objects.filter(user=request.user, isbn=book.isbn):
            rated = True
            cur_rating = UserRatingExplicit.objects.get(user=request.user, isbn=book.isbn)
            try:
                cur_comment = UserComment.objects.get(user=request.user, isbn=book.isbn)
            except Exception:
                cur_comment = None
        else:
            rated = False
            cur_rating = None
            cur_comment = None
        context = {
            'book': book,
            'average': average,
            'k_ratings': k_ratings,
            'ratings': ratings,
            'rated': rated,
            'cur_rating': cur_rating,
            'cur_comment': cur_comment,
        }
        return render(request, 'base/book.html', context)
    
    def post(self, request, pk):
        cur_rating = UserRatingExplicit.objects.filter(user=request.user, isbn=Book.objects.get(id=pk).isbn)

        if cur_rating:
            cur_rating = UserRatingExplicit.objects.get(user=request.user, isbn=Book.objects.get(id=pk).isbn)
            cur_rating.rating = request.POST.get('rating')
            cur_rating.save()
        else:
            UserRatingExplicit.objects.update_or_create(
                user=request.user,
                isbn=Book.objects.get(id=pk),
                rating=request.POST.get('rating')
            )

        if request.POST.get('comment'):
            cur_comment = UserComment.objects.get(user=request.user, isbn=Book.objects.get(id=pk).isbn)
            
            if cur_comment:
                cur_comment.comment = request.POST.get('comment')
                cur_comment.save()
            else:
                UserComment.objects.update_or_create(
                    user=request.user,
                    isbn=Book.objects.get(id=pk),
                    comment=request.POST.get('comment')
                )

            """ UserRatingImplicit.objects.create(
                user=request.user,
                isbn=Book.objects.get(id=pk),
            ) """

        return HttpResponseRedirect(self.request.path_info)
    
class UserView(View):
    def get(self, request, pk):
        user = User.objects.get(id=pk)
        try:
            age = UserAge.objects.get(user=pk).age
        except Exception:
            age = None
        
        try:
            location = UserLocation.objects.get(user=pk)
        except Exception:
            location = None

        ratings = UserRatingExplicit.objects.filter(user=pk)
        context = {
            'user': user,
            'age': age,
            'location': location,
            'ratings': ratings
        }
        return render(request, 'base/user.html', context)
    
class AuthorView(View):
    def get(self, request, pk):
        books = Book.objects.filter(author = pk)
        book_data = []

        for book in books:
            avg_rating = UserRatingExplicit.objects.filter(isbn=book.isbn).aggregate(avg=Avg('rating'))['avg']
            book_data.append({
                'book': book,
                'avg_rating': round(avg_rating, 2) if avg_rating is not None else 'Нет оценок'
            })

        context = {
            'author': pk,
            'book_data': book_data
        }
        return render(request, 'base/author.html', context)
    
class PublisherView(View):
    def get(self, request, pk):
        books = Book.objects.filter(publisher = pk)
        book_data = []

        for book in books:
            avg_rating = UserRatingExplicit.objects.filter(isbn=book.isbn).aggregate(avg=Avg('rating'))['avg']
            book_data.append({
                'book': book,
                'avg_rating': round(avg_rating, 2) if avg_rating is not None else 'Нет оценок'
            })
        
        context = {
            'publisher': pk,
            'book_data': book_data
        }
        return render(request, 'base/publisher.html', context)
    
class Login(View):
    def get(self, request):
        if request.user.is_authenticated: return redirect('home')

        context = {'page': 'login'}
        return render(request, 'base/login_register.html', context)
    
    def post(self, request):
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exist')

class Logout(View):
    def get(self, request):
        logout(request)
        return redirect('home')
    
class Register(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'base/login_register.html', {'form': form})
    
    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "An error occured during registration")

class DeleteRating(View):
    def get(self, request, pk):
        rating = UserRatingExplicit.objects.get(id=pk)
        return render(request, 'base/delete.html', {'obj': rating})
    
    def post(self, request, pk):
        rating = UserRatingExplicit.objects.get(id=pk)
        rating.delete()
        return redirect('home')