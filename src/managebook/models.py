from datetime import timezone

from django.contrib.auth.models import AbstractUser
from django.db import models, IntegrityError, transaction

from django.db.models import Avg


class User(AbstractUser):
    git_username = models.CharField(max_length=40, blank=True, default=None, null=True)
    git_repos_num = models.PositiveIntegerField(default=0, blank=True)
    books = models.ManyToManyField('Book', verbose_name="книга", db_index=True, related_name='authors_books')


class Genre(models.Model):
    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    title = models.CharField(max_length=50, verbose_name='Название')

    def __str__(self):
        return self.title


class Book(models.Model):
    class Meta:
        permissions = (
        #     ('hide_comments', 'скрыть комменты'),
        #     ('is_owner', 'Владелец'),
            ('is_author', 'Автор'),
        )
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'

    title = models.CharField(
        max_length=50,
        verbose_name='Название',
        help_text='введите название книги',
        db_index=True,
        unique=True
    )
    slug = models.SlugField(unique=True, verbose_name='Слаг')
    text = models.TextField(verbose_name='текст')
    author = models.ManyToManyField(User, verbose_name="автор", db_index=True, related_name='book')
    publish_date = models.DateField(auto_now_add=True)
    genre = models.ManyToManyField('managebook.Genre', verbose_name='жанр')
    rate = models.ManyToManyField(User, through='managebook.BookLike', related_name='rate')
    cached_rate = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    price = models.PositiveIntegerField(default=0)
    viewers = models.ManyToManyField(User, through='managebook.BookStat', blank=True, related_name='viewed_books')
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title if self.title is not None else 'name is not defined'


class BookStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='users_bookstat')
    book = models.ForeignKey(Book, on_delete=models.DO_NOTHING, related_name='books_bookstat')
    view = models.PositiveIntegerField(default=0)


class Comment(models.Model):
    text = models.TextField(verbose_name="текст")
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="пользователь", related_name='comment')
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, verbose_name="книга", related_name='comment')
    like = models.ManyToManyField(
        User, through='CommentLike', related_name='like', blank=True, null=True)
    cashed_like = models.PositiveIntegerField(default=0)


class BookLike(models.Model):
    class Meta:
        unique_together = ['user', 'book']

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='book_like')
    rate = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        try:
            super().save(**kwargs)
        except IntegrityError:
            bl = BookLike.objects.get(user=self.user, book=self.book)
            bl.rate = self.rate
            bl.save()
            flag = False
        else:
            self.book.cached_rate = self.book.book_like.aggregate(Avg('rate'))['rate__avg']
            self.book.save()
            flag = True
        return flag


class CommentLike(models.Model):
    class Meta:
        unique_together = ['comment', 'user']

    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name='comment_like')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comment_like')

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            CommentLike.objects.get(
                comment_id=self.comment.id, user_id=self.user.id).delete()
            self.comment.cashed_like -= 1
            flag = False
        else:
            self.comment.cashed_like += 1
            flag = True
        self.comment.save()
        return flag


class BookStatistic(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True, verbose_name="Дата")
    views = models.IntegerField(default=0, verbose_name='Просмотры')
    viewer = models.ManyToManyField(User, blank=True, null=True, related_name='bookstat')


    def __str__(self):
        return self.book.title
