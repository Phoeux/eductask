from datetime import datetime
from json import loads
import pandas as pd
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, CharField, OuterRef, Exists, Prefetch, Sum, F
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from pytils.translit import slugify
from requests import post, get
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication, BasicAuthentication, SessionAuthentication
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, UpdateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bookshop.settings import GIT_CLIENT_ID, GIT_REDIRECT_URI, GIT_SCOPE, GIT_CLIENT_SECRET
from managebook.forms import BookForm, CommentForm, CustomUserCreateForm, CustomAuthenticationForm
from managebook.models import BookLike, Book, CommentLike, Comment, Genre, User, BookStat
from managebook.serializer import CustomCommentSerializer, CommentSerializer, BookSerializer, CustomBookSerializer, \
    CustomRateSerializer, BookAPISerializer, AuthorBooksAPISerializer
from managebook.utils import GitAuth


class BookView(View):
    # @method_decorator(cache_page(5))
    # @permission_required('managebook.is_owner')
    def get(self, request, num_page=1):
        response = {'form': CommentForm()}

        if request.user.is_authenticated:
            sub_query_1 = BookLike.objects.filter(user=request.user, book=OuterRef('pk')).values('rate')
            sub_query_2 = Exists(User.objects.filter(id=request.user.id, book=OuterRef('pk')))
            sub_query_3 = Exists(User.objects.filter(id=request.user.id, comment=OuterRef('pk')))
            sub_query_4 = Exists(User.objects.filter(id=request.user.id, like=OuterRef('pk')))
            comment = Comment.objects.annotate(is_owner=sub_query_3, is_liked=sub_query_4). \
                select_related('user').prefetch_related('like')
            comment_prefetch = Prefetch('comment', comment)
            result = Book.objects.annotate(user_rate=Cast(sub_query_1, CharField()),
                                           is_owner=sub_query_2). \
                prefetch_related(comment_prefetch, 'author', 'genre', 'rate')
        else:
            result = Book.objects. \
                prefetch_related('author', 'genre', 'comment', 'comment__user').all()
        pag = Paginator(result, 5)
        response['content'] = pag.page(num_page)
        response['count_page'] = list(range(1, pag.num_pages + 1))
        response['book_form'] = BookForm()
        response['comment_form'] = CommentForm()
        response['author'] = User.objects.all()
        response['url'] = f'https://github.com/login/oauth/authorize?client_id={GIT_CLIENT_ID}' \
                          f'&redirect_uri={GIT_REDIRECT_URI}&scope={GIT_SCOPE}'
        return render(request, 'index.html', response)


class AuthorsBooks(View):
    def get(self, request, author_id):
        context = []
        author_id_split = author_id.split(',')
        for id in author_id_split:
            users_data = {}
            req_auth = get_object_or_404(User, id__in=id)
            authors_books = Book.objects.filter(author=req_auth)
            price = authors_books.annotate(whole_price=Sum('price')).aggregate(Sum('whole_price'))['whole_price__sum']
            # all_users_prices = list(map(lambda x: {x["username"]: x["whole_price"]},
            #                             User.objects.annotate(whole_price=Sum("books__price")).values("whole_price",
            #                                                                                  "username")))
            all_users_prices = User.objects.annotate(whole_price=Sum("books__price"), count_book=Count('books')).values(
                "whole_price", "username", 'count_book')
            # book_num = map(lambda x: {x['username']: x['book_num']},
            #                User.objects.annotate(book_num=Count('book')).values('book_num', 'username'))
            users_data.update(req_auth=req_auth)
            # users_data.update(book_num=book_num)
            users_data.update(price=price)
            users_data.update(authors_books=authors_books)
            # users_data.update(all_users_prices=all_users_prices)
            context.append(users_data)
            # context.append(all_users_prices)
        return render(request, 'authors_books.html',
                      {"context": context, 'all_users_prices': all_users_prices})  # , content_type="text/strings")


class AuthorsBooks2(View):
    def get(self, request, author_id):
        context = {}
        auth_list = []
        authors_books_list = []
        price_list = []
        # all_users_prices_list = []
        author_id_split = author_id.split(',')
        for id in author_id_split:
            req_auth = User.objects.filter(id__in=id)
            auth_list.append(req_auth[0])
            authors_books = Book.objects.filter(author=req_auth[0])
            authors_books_list.append(authors_books)

            price = authors_books.annotate(whole_price=Sum('price')).aggregate(Sum('whole_price'))['whole_price__sum']
            price_list.append(price)

            all_users_prices = list(map(lambda x: {x["username"]: x["whole_price"]},
                                        User.objects.annotate(whole_price=Sum("books__price")).values("whole_price",
                                                                                                      "username")))
            # all_users_prices_list.append(all_users_prices)
            book_num = list(map(lambda x: {x['username']: x['book_num']},
                                User.objects.annotate(book_num=Count('book')).values('book_num', 'username')))
            context.update(req_auth=auth_list)
            context.update(price=price_list)
            context.update(authors_books=authors_books_list)

            context.update(book_num=book_num)
            context.update(all_users_prices=all_users_prices)
        return render(request, 'authors_books.html', context)  # , content_type="text/strings")
        # return context


class AuthorsBooks3(View):
    def get(self, request, author_id=None):
        context = []
        author_id_split = []
        data = list(request.get_full_path().split('/')[-1])
        for author_id in data:
            if author_id.isdigit():
                author_id_split.append(author_id)
        if author_id is not None:
            # author_id_split = author_id.split(',')
            aggregated_users_data = User.objects.filter(id__in=author_id_split).prefetch_related("books").annotate(
                whole_price=Sum("books__price"), count_book=Count('books'))
        else:
            aggregated_users_data = User.objects.all().prefetch_related("books").annotate(
                whole_price=Sum("books__price"), count_book=Count('books'))
        for user in aggregated_users_data:
            users_data = {}
            users_data.update(whole_price=user.whole_price)
            users_data.update(count_book=user.count_book)
            users_data.update(username=user.username)
            users_data.update(
                books=[{"title": book.title, "text": book.text, 'price': book.price} for book in user.books.all()])
            context.append(users_data)
        return render(request, 'authors_books.html', {"context": context})


class AuthorsBooks3Ajax(View):
    def get(self, request, author_id=None):
        context = []
        author_id_split = []
        data = list(request.get_full_path().split('_')[-1])
        for author_id in data:
            if author_id.isdigit():
                author_id_split.append(author_id)
        if author_id is not None:
            # author_id_split = author_id.split(',')
            aggregated_users_data = User.objects.filter(id__in=author_id_split).prefetch_related("books").annotate(
                whole_price=Sum("books__price"), count_book=Count('books'))
        else:
            aggregated_users_data = User.objects.all().prefetch_related("books").annotate(
                whole_price=Sum("books__price"), count_book=Count('books'))
        for user in aggregated_users_data:
            users_data = {}
            users_data.update(whole_price=user.whole_price)
            users_data.update(count_book=user.count_book)
            users_data.update(username=user.username)
            users_data.update(
                books=[{"title": book.title, "text": book.text, 'price': book.price} for book in user.books.all()])
            context.append(users_data)
        return JsonResponse({"context": context})


class AddRateBook(View):
    def get(self, request, rate, book_id):
        if request.user.is_authenticated:
            BookLike.objects. \
                create(book_id=book_id, rate=rate, user_id=request.user.id)
        return redirect('hello')


class AddLike(View):
    def get(self, request, comment_id):
        if request.user.is_authenticated:
            CommentLike.objects. \
                create(comment_id=comment_id, user_id=request.user.id)
        return redirect('hello')


class RegisterView(View):
    def get(self, request):
        form = CustomUserCreateForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = CustomUserCreateForm(data=request.POST)
        if form.is_valid():
            form.save()
            # login(request, user)
            return redirect('hello')
        messages.error(request, message="This Username is already exists")
        return redirect("login")


class LoginView(View):
    def get(self, request):
        form = CustomAuthenticationForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())

            return redirect('hello')
        messages.error(request, message='User does not exist')
        return redirect('login')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('hello')


class AddNewBook(View):
    def get(self, request):
        form = BookForm()
        return render(request, 'create_book.html', {'form': form})

    def post(self, request):
        book = BookForm(data=request.POST)
        if book.is_valid():
            # book.save()
            nb = book.save(commit=False)
            nb.slug = slugify(nb.title)
            try:
                nb.save()
            except IntegrityError:
                nb.slug += datetime.now().strftime('%Y:%m:%d %H:%M:%S:$f')
                nb.save()
            nb.author.add(request.user)
            book.save_m2m()
            return redirect('hello')
        return redirect('add_book')


class DeleteBook(View):
    def get(self, request, book_id):
        if request.user.is_authenticated:
            book = Book.objects.get(id=book_id)
            if request.user in book.author.all():
                book.delete()
        return redirect('hello')


class DeleteBookAPI(DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, SessionAuthentication)

    def delete(self, request, book_id):
        Book.objects.filter(id=book_id, author=request.user).delete()
        return Response({'ok': True}, status=status.HTTP_204_NO_CONTENT)


class UpdateBook(View):
    def get(self, request, book_id):
        if request.user.is_authenticated:
            book = Book.objects.get(id=book_id)
            if request.user in book.author.all():
                bf = BookForm(instance=book)
                return render(request, 'update_book.html', {'form': bf, 'id': book.id})
        return redirect('hello')

    def post(self, request, book_id):
        book = Book.objects.get(id=book_id)
        bf = BookForm(instance=book, data=request.POST)
        if bf.is_valid():
            bf.save()
        return redirect('hello')


class UpdateBookAPI(UpdateAPIView):
    serializer_class = BookSerializer
    lookup_field = "slug"
    queryset = Book.objects


class AddComment(View):
    def post(self, request, book_id):
        if request.user.is_authenticated:
            cf = CommentForm(data=request.POST)
            comment = cf.save(commit=False)
            comment.user = request.user
            comment.book_id = book_id
            comment.save()
        return redirect("hello")


class DeleteComment(View):
    def get(self, request, comment_id):
        if request.user.is_authenticated:
            try:
                Comment.objects.get(id=comment_id, user=request.user).delete()
            except Comment.DoesNotExist:
                pass
        return redirect('hello')


class UpdateComment(View):
    def get(self, request, comment_id):
        if request.user.is_authenticated:
            comment = Comment.objects.get(id=comment_id)
            if comment.user == request.user:
                cf = CommentForm(instance=comment)
                return render(request, 'update_comment.html', {'form': cf, 'id': comment.id})
        return redirect('hello')

    def post(self, request, comment_id):
        comment = Comment.objects.get(id=comment_id)
        cf = CommentForm(instance=comment, data=request.POST)
        if cf.is_valid():
            cf.save()
        return redirect('hello')


class AddLikeAjax(View):
    def post(self, request):
        if request.user.is_authenticated:
            cl_id = request.POST['cl_id'][3:]
            flag = CommentLike(user=request.user, comment_id=cl_id).save()
            comment = Comment.objects.get(id=cl_id)
            return JsonResponse({
                'ok': True,
                'count_like': comment.cashed_like,
                'flag': flag,
                'user': request.user.username})
        return JsonResponse({'ok': False})


class AddBookRateAjax2(View):
    def post(self, request):
        if request.user.is_authenticated:
            bl = BookLike(
                user=request.user, book_id=request.POST['book_id'], rate=request.POST['book_rate'])
            flag = bl.save()
            bl.book.refresh_from_db()
            return JsonResponse({
                'flag': flag,
                'cached_rate': bl.book.cached_rate,
                'rate': bl.rate,
                'user': request.user.username})
        return JsonResponse({'ok': False})


class AddBookRateAjax(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, SessionAuthentication, TokenAuthentication)
    serializer_class = CustomRateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'ok': True}, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteCommentAjax3(View):
    def delete(self, request, comment_id):
        if request.user.is_authenticated:
            Comment.objects.filter(id=comment_id, user=request.user).delete()
        return JsonResponse({'ok': True})


class DeleteCommentAjax(DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, SessionAuthentication)

    def delete(self, request, comment_id):
        Comment.objects.filter(id=comment_id, user=request.user).delete()
        return Response({'ok': True}, status=status.HTTP_204_NO_CONTENT)


class DeleteCommentAjax2(DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, SessionAuthentication)
    serializer_class = CustomCommentSerializer

    def delete(self, request, comment_id):
        serializer = self.serializer_class(data=comment_id)
        serializer.delete(user=request.user, id=comment_id)
        return Response({'ok': True}, status=status.HTTP_204_NO_CONTENT)


class AddNewBookAjax2(View):
    def post(self, request):
        if request.user.is_authenticated:
            b = Book(title=request.POST['title'], text=request.POST['text'], slug=slugify(request.POST['title']))
            try:
                b.save()
            except IntegrityError:
                b.slug += datetime.now().strftime('%Y:%m:%d %H:%M:%S:$f')
                b.title += datetime.now().strftime('%Y:%m:%d %H:%M:%S:$f')
                b.save()
            b.author.add(request.user)
            for g in loads(request.POST['genre']):
                req_g = Genre.objects.get(id=g)
                b.genre.add(req_g)
            b.save()
        return JsonResponse({'ok': True})


class AddNewBookAjax(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, SessionAuthentication)
    serializer_class = CustomBookSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddNewCommentAjax2(View):
    def post(self, request):
        if request.user.is_authenticated:
            book = Book.objects.get(slug=request.POST['slug'])
            Comment.objects.create(text=request.POST['text'], user=request.user, book=book)
        return JsonResponse({'ok': True})  # может быть другой ответ


class AddNewCommentAjax(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, SessionAuthentication)
    serializer_class = CustomCommentSerializer

    # queryset = Comment.objects.all()

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'ok': True}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentListApi(ListAPIView):
    serializer_class = CommentSerializer
    queryset = Comment.objects

    class Meta:
        model = Comment
        fields = '__all__'


class BookListApi(ListAPIView):
    serializer_class = BookSerializer
    queryset = Book.objects

    class Meta:
        model = Book
        fields = '__all__'


class GitRepos(View):
    def get(self, request):
        code = request.GET['code']
        url = f'https://github.com/login/oauth/access_token?client_id={GIT_CLIENT_ID}&client_secret={GIT_CLIENT_SECRET}&code={code}&redirect_uri={GIT_REDIRECT_URI}'
        data = post(url)
        access_token = data.text.split("&")[0].split("=")[1]
        response = get("https://api.github.com/user",
                       headers={
                           'Authorization': f'token {access_token}',
                           'Accept': 'application/json'
                       })
        git_username = response.json()['login']
        context = GitAuth(git_username)
        context['code'] = code
        context['login'] = git_username
        if request.user.is_authenticated:
            request.user.git_username = git_username
            request.user.git_repos_num = context['total_rep_num']
            request.user.save()
            return render(request, 'rep.html', context)
        return render(request, 'rep.html', context)


class AllBooksApi(viewsets.ModelViewSet):
    queryset = Book.objects
    serializer_class = BookAPISerializer


class AuthorBooksAPI(viewsets.ModelViewSet):
    serializer_class = AuthorBooksAPISerializer
    queryset = User.objects.all()


class BookStatView(View):
    # template_name = 'bookview.html'

    def get(self, request, *args, **kwargs):
        book = get_object_or_404(Book, id=self.kwargs['book_id'])
        context = {}

        obj, created = BookStatistic.objects.get_or_create(
            defaults={
                'book': book,
                'date': timezone.now()
            },
            date=timezone.now(), book=book
        )
        obj.views += 1
        obj.save(update_fields=['views'])

        popular = BookStatistic.objects.all().values('book_id', 'book__title').annotate(views=Sum('views')). \
            order_by('-views')
        context['popular_list'] = popular
        # cont = []
        # viewer_data = {}

        # if request.user.is_authenticated:
        #     viewer = User.objects.get(id=request.user.id)
        #     # user_views = User.objects.get(id=request.user.id)
        #     viewer_data['viewer'] = viewer
        #     # aggregated_data = User.objects.filter(id=request.user.id).annotate(views=Sum('bookstat__views'), views_user=F('views')+1)
        #     aggregated_data = Book.objects.filter(id=self.kwargs['book_id']).annotate(views=Sum('bookstatistic__views'), user_views=F('bookstatistic__views')+1)
        #     for data in aggregated_data:
        #         viewer_data.update(views=data.views)
        #         viewer_data.update(user_views=data.user_views)

        #     viewer_data.update(views_user=data.views_user)
        #     cont.append(viewer_data)
        # return render(request, 'bookview.html', {'context': cont})
        return render(request, 'bookview.html', context=context)


class BookDetail(View):
    def get(self, request, *args, **kwargs):
        context = {}
        book = Book.objects.filter(id=self.kwargs['book_id'])
        context['book'] = book
        return render(request, 'book_detail.html', context)


class ListBookStatistics(View):
    def get(self, request):
        context = {}
        popular = Book.objects.all().values_list('id', 'title', 'views').order_by('-views')
        context['popular_list'] = popular
        return render(request, 'book_stat_list.html', context)


class RecommendedBooks(View):
    def get(self, request):

        # active_user_books = User.objects.get(id=request.user.id).users_bookstat.values_list('book__title', flat=True)
        active_user_books = User.objects.get(id=request.user.id).users_bookstat.values_list("book_id", flat=True)
        users_who_also_read_my_books = BookStat.objects.filter(book_id__in=active_user_books).exclude(
            user=request.user).distinct().values_list("user__id", flat=True)
        book_recommended = BookStat.objects.filter(user_id__in=users_who_also_read_my_books).exclude(book_id__in=active_user_books)
        df = pd.DataFrame(book_recommended.values("book__title", "view")).groupby("book__title").sum("view").sort_values("view", ascending=False)
        new_books = list(df.index)

        # for user in User.objects.all().exclude(id=request.user.id):
        #     if user.users_bookstat.values_list('book__title', flat=True).exists():
        #         book = set(i.book.title for i in user.users_bookstat.all())-set(i.book.title for i in active_user_books)
        #         new_books.update(book=book)
        #         context.append(book)
        #
        #         for book_title in book:
        #             if book_title.title in user.users_bookstat.values_list('book__title', 'book__views'):
        #                 book_view = book_title.title[1]
        #         context.update(book_view=book_view)

        # active_user_books.difference(user_viewed_books)

        # context = []
        # active_user_books = User.objects.get(id=request.user.id).users_bookstat.values_list('book__title', flat=True)
        # for user in User.objects.all().exclude(id=request.user.id):
        #     users_data = {}
        #     users_data.update(user=user.username)
        #     user_viewed_books_list = []
        #     if user.users_bookstat.values_list('book__title', flat=True).exists():
        #         for user_viewed_books in user.users_bookstat.values_list('book__title', flat=True):
        #             user_viewed_books_list.append(user_viewed_books)
        #         users_data.update(user_viewed_books_list=user_viewed_books_list)
        #         context.append(users_data)

        return render(request, 'recommended_books.html', {'context':new_books})


class BookStatistics(View):
    def get(self, request, book_id):
        context = {}
        book = get_object_or_404(Book, id=book_id)
        book.views += 1
        book.save()
        context.update(book_title=book.title, book_views=book.views)

        if request.user.is_authenticated:
            curr_view, flag = BookStat.objects.get_or_create(user_id=request.user.id, book_id=book_id)
            updated_view_num = curr_view.view + 1
            BookStat.objects.filter(user_id=request.user.id, book_id=book_id).update(view=updated_view_num)
            context.update(user_stat_username=curr_view.user, user_stat_view=updated_view_num)

        users_username = BookStat.objects.filter(book_id=book_id).values_list("user__username", flat=True)
        # context.update(all_viewers=all_viewers)
        # all_viewers_id = []
        # for item in all_viewers:
        #     for key, value in item.items():
        #         all_viewers_id.append(value)
        # users_username = User.objects.filter(id__in=all_viewers)
        context.update(users_username=users_username)

        return render(request, 'book_detail.html', context)
