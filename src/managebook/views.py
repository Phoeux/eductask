from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, Q, CharField, Value, OuterRef, Exists, Prefetch
from django.db.models.functions import Cast
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect
from django.utils import cache
from django.views.decorators.cache import cache_page
from pytils.translit import slugify
from requests import post, get
from rest_framework import status
from rest_framework.authentication import TokenAuthentication, BasicAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from bookshop.settings import GIT_CLIENT_ID, GIT_REDIRECT_URI, GIT_SCOPE, GIT_CLIENT_SECRET
from managebook.forms import BookForm, CommentForm, CustomUserCreateForm, CustomAuthenticationForm
from managebook.models import BookLike, Book, CommentLike, Comment, Genre, User
from django.views import View
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from datetime import datetime
from django.utils.decorators import method_decorator
from json import dumps, loads

from managebook.serializer import CustomCommentSerializer, CommentSerializer, BookSerializer, CustomBookSerializer, \
    CustomRateSerializer
from managebook.utils import XeroFirstAuth, GitAuth


class BookView(View):
    # @method_decorator(cache_page(5))
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
        response['url'] = f'https://github.com/login/oauth/authorize?client_id={GIT_CLIENT_ID}' \
                          f'&redirect_uri={GIT_REDIRECT_URI}&scope={GIT_SCOPE}'
        return render(request, 'index.html', response)


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
        # return Book.objects.filter(id=book_id, author=request.user).delete()
        return Response({'ok': True}, status=status.HTTP_204_NO_CONTENT)
        # return redirect('hello')


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
        # print('reqdata', request.data)
        serializer = self.serializer_class(data=request.data)
        # print('serdata', serializer)
        # print(request.user)
        if serializer.is_valid():
            # print(serializer.is_valid())
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

    # queryset = Comment.objects

    # def get_queryset(self):
    #     queryset = Comment.objects.filter(id=self.kwargs['pk'], user=self.request.user)
    #     return queryset

    def delete(self, request, comment_id):
        serializer = self.serializer_class(data=comment_id)
        # user = request.user
        # if serializer.is_valid():
        serializer.delete(user=request.user, id=comment_id)
        return Response({'ok': True}, status=status.HTTP_204_NO_CONTENT)

    # def delete2(self, request, comment_id):
    #     Comment.objects.filter(id=comment_id).delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)

    # def destroy(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     self.perform_destroy(instance)
    #     return Response(status=status.HTTP_204_NO_CONTENT)
    #
    # def perform_destroy(self, instance):
    #     instance.delete()

    # def get_object(self, comment_id):
    #     try:
    #         return Comment.objects.get(id=comment_id)
    #     except Comment.DoesNotExist:
    #         raise Http404
    #
    # def delete(self, request, comment_id):
    #     comment = self.get_object(comment_id)
    #     comment.delete()
    #     return Response({'ok': True}, status=status.HTTP_204_NO_CONTENT)

    # def delete(self, request, *args, **kwargs):
    #     try:
    #         instance = self.get_object()
    #         self.perform_destroy(instance)
    #     except Http404:
    #         pass
    #     return Response(status=status.HTTP_204_NO_CONTENT)


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
        # print(request.POST['title'])
        # print(request.POST['text'])
        # print(loads(request.POST['genre']))
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
        # print(request.POST['text'])
        return JsonResponse({'ok': True})  # может быть другой ответ


class AddNewCommentAjax(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (BasicAuthentication, SessionAuthentication)
    serializer_class = CustomCommentSerializer

    # queryset = Comment.objects.all()

    def post(self, request):
        # print("REQUEST DATA", request.data)
        serializer = self.serializer_class(data=request.data)
        # print('SER DATA', serializer)
        # print(request.user)
        if serializer.is_valid():
            serializer.save(user=request.user)
            # print('COM SAVE', comment_saved.text)
            # print(f"Success. Comment {comment_saved.text} created succesfully.")
            return Response({'ok': True}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # book = Book.objects.get(id=request.POST['id'])
        # Comment.objects.create(text=request.POST['text'], user=request.user, book=book)
        # return JsonResponse({'ok': True})
        # return self.create(request, *args, **kwargs)

    # def post(self, request, *args, **kwargs):
    #     c = Comment(id=request.POST['book'], text=request.POST['text'], user=request.POST['user'])
    #     c.save()
    #     return JsonResponse({'ok': True})

    # def post(self, request, *args, **kwargs):
    #     return self.create(request, *args, **kwargs)

    # def get_object(self):
    #     return Book.objects.get(id=self.kwargs.get('id'))


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
            # return JsonResponse(context)
            return render(request, 'rep.html', context)
        return render(request, 'rep_list.html', context)


