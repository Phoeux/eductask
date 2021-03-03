from django.contrib import admin

# Register your models here.
from managebook.models import Book, Comment, Genre, User, BookStatistic, BookStat


class BookStatAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'view')


class CommentAdmin(admin.StackedInline):
    model = Comment
    extra = 2
    readonly_fields = ['like']


class BookAdmin(admin.ModelAdmin):
    inlines = [CommentAdmin]
    prepopulated_fields = {'slug': ('title',)}
    list_display = ['title', 'publish_date', 'views']
    search_fields = ['title']
    list_filter = ['publish_date', 'author', 'genre']


admin.site.register(Book, BookAdmin)
admin.site.register(Genre)
admin.site.register(User)
admin.site.register(BookStat, BookStatAdmin)
