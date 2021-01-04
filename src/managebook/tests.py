from time import sleep

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import transaction
from django.db.models import Avg
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from managebook.models import Book, BookLike, Comment, Genre
from django.contrib.auth.models import User
from selenium.webdriver import Chrome


# Create your tests here.
# class TestModel(TestCase):
#     def test_rate(self):
#         user_1 = User.objects.create(username='user_1')
#         user_2 = User.objects.create(username='user_2')
#         book = Book.objects.create(text='text', slug='slug')
#         BookLike.objects.create(book=book, user=user_1, rate=4)
#         BookLike.objects.create(book=book, user=user_2, rate=6)
#         rate__avg = book.book_like.aggregate(Avg('rate'))['rate__avg']
#         self.assertEqual(rate__avg, 5)
#
#     def test_cached_rate(self):
#         user_1 = User.objects.create(username='user_1')
#         user_2 = User.objects.create(username='user_2')
#         book = Book.objects.create(text='text', slug='slug')
#         BookLike.objects.create(book=book, user=user_1, rate=4)
#         BookLike.objects.create(book=book, user=user_2, rate=6)
#         self.assertEqual(book.cached_rate, 5)
#
#     def test_comment_like(self):
#         user_1 = User.objects.create(username='user_1')
#         user_2 = User.objects.create(username='user_2')
#         book = Book.objects.create(text='text', slug='slug')
#         comment = Comment.objects.create(text='text', user=user_1, book=book)
#         comment.like.add(user_2)
#         comment.like.add(user_1)
#         comment.save()
#         like = comment.like.count()
#         self.assertEqual(like, 2)  # coverage run --source='.' manage.py test .
#
#
# class TestViews(TestCase):
#
#     def setUp(self):
#         self.user = User.objects.create_user(username='Test Name', password='test pwd')
#         self.client.force_login(self.user)
#
#     def test_hello(self):
#         url = reverse('hello')
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.client.logout()
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#
#     def test_add_rate(self):
#         book = Book.objects.create(text='text', slug='slug')
#         url = reverse('add_rate', args=[7, book.id])
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 302)
#         book.refresh_from_db()
#         self.assertEqual(book.cached_rate, 7)
#
#         self.client.logout()
#         url = reverse('add_rate', args=[1, book.id])
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 302)
#         book.refresh_from_db()
#         self.assertEqual(book.cached_rate, 7)
#
#     def test_add_like2comment(self):
#         book = Book.objects.create(text='text', slug='slug')
#         comment = Comment.objects.create(text='text', user=self.user, book=book)
#         url = reverse('add_like2comment', args=[comment.id])
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 302)
#         comment.refresh_from_db()
#         self.assertEqual(comment.cashed_like, 1)
#
#     def test_add_comment(self):
#         book = Book.objects.create(text='text', slug='slug')
#         url = reverse('add_comment', args=[book.id])
#         data = {'text': 'test comment text'}
#         response = self.client.post(url, data=data)
#         self.assertEqual(response.status_code, 302)
#         book.refresh_from_db()
#         self.assertEqual(book.comment.first().text, data['text'])
#
#     def test_delete_book(self):
#         book = Book.objects.create(text='text', slug='slug')
#         book.author.add(self.user)
#         book.save()
#         url = reverse('delete_book', args=[book.id])
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Book.objects.count(), 0)
#
#     def test_update_book(self):
#         g1 = Genre.objects.create(title='genre 1')
#         g2 = Genre.objects.create(title='genre 2')
#         book = Book.objects.create(text='text', slug='slug')
#         book.author.add(self.user)
#         book.genre.add(g1)
#         book.save()
#         url = reverse('update_book', args=[book.slug])
#         data = {
#             'title': 'update new title',
#             'text': 'update new text',
#             'genre': ['2']}
#         response = self.client.post(url, data=data)
#         self.assertEqual(response.status_code, 302)
#         book.refresh_from_db()
#         self.assertEqual(book.title, data['title'])
#         self.assertEqual(book.text, data['text'])
#         self.assertEqual(book.genre.first().title, g2.title)
#
#     # def test_register(self):
#     #     self.client.logout()
#     #     url = reverse('register')
#     #     response = self.client.get(url)
#     #     self.assertEqual(response.status_code, 200)
#     #     self.assertTemplateUsed(response, 'register.html')
#     #     data = {'username': 'glebtest',
#     #             'password1': 'qwertyqwerty',
#     #             'password2': 'qwertyqwerty'}
#     #     response = self.client.post(url, data=data)
#     #     self.assertEqual(response.status_code, 302)
#     #     user = User.objects.get(id=2)
#     #     self.assertEqual(user.username, data['username'])
#     #     response = self.client.post(url, data=data)
#     #     self.assertEqual(response.status_code, 302)
#
#     def test_login(self):
#         self.client.logout()
#         url = reverse('login')
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'login.html')
#         data = {'username': 'Test Name',
#                 'password': 'test pwd'
#                 }
#         response = self.client.post(url, data=data)
#         self.assertEqual(response.status_code, 302)
#     def test_logout(self):
#         url = reverse('logout')
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 302)
#
#     def test_add_book(self):
#         url = reverse('add_book')
#         g1 = Genre.objects.create(title='genre 1')
#         g2 = Genre.objects.create(title='genre 2')
#         data = {
#             'title': 'update new title',
#             'text': 'update new text',
#             'genre': ['1', '2']}
#         response = self.client.post(url, data=data)
#         self.assertEqual(response.status_code,302)
#         book = Book.objects.first()
#         self.assertEqual(book.title, data['title'])
#         self.assertEqual(book.text, data['text'])
#         arr = [i.title for i in book.genre.all()]
#         self.assertEqual(arr, [g1.title, g2.title])
#
#     def test_delete_comment(self): #проверить удаляется ли коммент другим пользователем
#         book = Book.objects.create(text='text', slug='slug')
#         comment = Comment.objects.create(text='text of comment', user=self.user, book=book)
#         url = reverse('delete_comment', args=[comment.id])
#         # data = {
#         #     'title': 'update new title',
#         # }
#         response = self.client.get(url)
#         self.assertEqual(response.status_code,302)
#         self.assertEqual(Comment.objects.count(), 0)

# class TestBySelenium(StaticLiveServerTestCase):
#     def setUp(self):
#         user_1 = User.objects.create_user(username="test_name1")
#         user_2 = User.objects.create_user(username="test_name2")
#         genre_1 = Genre.objects.create(title="testgenre1")
#         genre_2 = Genre.objects.create(title="testgenre2")
#         book = Book.objects.create(title="test title", text="test text")
#         book.author.add(user_1)
#         book.author.add(user_2)
#         book.genre.add(genre_1)
#         book.genre.add(genre_2)
#         book.save()
#
#     def test_one(self):
#         driver = Chrome()
#         driver.get(self.live_server_url + reverse("hello"))
#         sleep(5)
#         authors = driver.find_element_by_xpath("/html/body/div/div/h5[3]").text
#         self.assertEqual(authors, "Authors: test_name1 test_name2")

class TestBook(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='Test Name', password='test pwd')
        Genre.objects.create(title='test_genre1')
        Genre.objects.create(title='test_genre2')

    def test_create(self):
        self.client.force_login(self.user)
        Genre.objects.create(title='testgenre')
        url = reverse('add_new_book_ajax')
        data = {
            'title': 'test title',
            'text': 'text',
            'user': 1,
            'genre': [1]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.exists(), 1)

    def test_delete(self):
        self.client.force_login(self.user)
        Genre.objects.create(title='testgenre')

        # book = Book.objects.create(title='testbook', text='testtext')
        # book.author.add(self.user)
        # book.save()

        url = reverse('add_new_book_ajax')
        data = {
            'title': 'test title',
            'text': 'test text',
            'user': 1,
            'genre': [1]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # count_book = Book.objects.all().count()
        self.assertEqual(Book.objects.exists(), 1)

        url = reverse('delete_book_api', kwargs={'book_id': Book.objects.first().id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # count_book = Book.objects.all().count()
        count_book_exists = Book.objects.exists()
        self.assertFalse(count_book_exists) # как проверить, не думаю что это работает и не уверен что книга удаляется
        # self.assertEqual(count_book, 0)

    # exists, assertequal
    def test_list(self):
        self.client.force_login(self.user)

        url = reverse('add_new_book_ajax')
        data1 = {
            'title': 'testtitle',
            'text': 'testtext',
            'user': 1,
            'genre': [1, 2]
        }
        data2 = {
            'title': 'testtitle2',
            'text': 'testtext2',
            'user': 1,
            'genre': [1]
        }
        response = self.client.post(url, data1, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url, data2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('book_list_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Book.objects.first().title, 'testtitle')
        self.assertEqual(response.json()[1]['text'], 'testtext2')

    def test_update(self):
        self.client.force_login(self.user)

        url = reverse('add_new_book_ajax')
        data = {
            'title': 'test_title',
            'text': 'test_text',
            'user': 1,
            'genre': [1]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('update_book_api', kwargs={'slug': Book.objects.first().slug})
        data_upd = {
            'title': 'updated_title'
        }
        response = self.client.patch(url, data_upd, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['title'], 'updated_title')

