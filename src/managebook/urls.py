from django.conf.urls import url
from django.urls import path, include
from django.views.decorators.cache import cache_page
from rest_framework.routers import DefaultRouter

from managebook import views

router = DefaultRouter()
router.register('all_books', views.AllBooksApi)
router.register('all_author_books', views.AuthorBooksAPI)

urlpatterns = [
    path('api/', include(router.urls)),
    # path('hello/', cache_page(2)(views.BookView.as_view()), name='hello'),
    path('hello/', views.BookView.as_view(), name='hello'),
    path('hello/<int:num_page>', views.BookView.as_view(), name='hello_with_num_page'),
    path('add_rate/<int:rate>/<int:book_id>', views.AddRateBook.as_view(), name='add_rate'),
    path('add_like2comment/<int:comment_id>', views.AddLike.as_view(), name='add_like2comment'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('add_book/', views.AddNewBook.as_view(), name='add_book'),
    path('add_comment/<int:book_id>', views.AddComment.as_view(), name='add_comment'),
    path('delete_book/<int:book_id>', views.DeleteBook.as_view(), name='delete_book'),
    path('update_book/<str:book_slug>', views.UpdateBook.as_view(), name='update_book'),
    path('delete_comment/<int:comment_id>', views.DeleteComment.as_view(), name='delete_comment'),
    path('update_comment/<int:comment_id>', views.UpdateComment.as_view(), name='update_comment'),
    path('add_like_ajax/', views.AddLikeAjax.as_view()),
    path('add_book_rate_ajax/', views.AddBookRateAjax.as_view()),
    path('delete_comment_ajax/<int:comment_id>', views.DeleteCommentAjax.as_view()),
    path('add_new_book_ajax/', views.AddNewBookAjax.as_view(), name='add_new_book_ajax'),
    path('add_new_comment_ajax/', views.AddNewCommentAjax.as_view()),

    path('com_list_api/', views.CommentListApi.as_view()),
    path('book_list_api/', views.BookListApi.as_view(), name='book_list_api'),
    path('delete_book_api/<int:book_id>', views.DeleteBookAPI.as_view(), name='delete_book_api'),
    path('update_book_api/<str:slug>', views.UpdateBookAPI.as_view(), name='update_book_api'),
    path('github', views.GitRepos.as_view()),
    # path('authors_books_api/', views.AuthorBooksAPI.as_view()),
    path('author_books/', views.AuthorsBooks3.as_view(), name='all_author_books'),
    path('author_books_ajax/', views.AuthorsBooks3Ajax.as_view(), name='all_author_books_ajax'),
    path('author_books/?<str:author_id>/', views.AuthorsBooks3.as_view(), name='author_books'),
    # path('list_rep/', views.GitRepos.as_view(), name='reps'),

    # url(r'^(?P<book_id>[0-9]+)/$', views.BookStatView.as_view(), name='book_stat'),

    path('book_stat_list/', views.ListBookStatistics.as_view(), name='book_stat_list'),
    path('book_stat/<int:book_id>', views.BookStatistics.as_view(), name='book_stat'),
    path('recommended_books/',views.RecommendedBooks.as_view(), name='recommended_books')
    # path('book_list_stat/<int:book_id>/', views.BookStatView.as_view(), name='book_stat')
]
