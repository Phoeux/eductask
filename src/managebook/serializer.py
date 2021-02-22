from django.utils.text import slugify
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer

from managebook.models import Comment, Book, BookLike, Genre, User


class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['book', 'text']


class CustomCommentSerializer(Serializer):
    book_id = serializers.IntegerField()
    text = serializers.CharField()

    def create(self, validated_data):
        return Comment.objects.create(**validated_data)


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class BookSerializer(ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'text', 'author', 'genre']


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = ['title']


class AuthorBooksSerializer(ModelSerializer):
    books = BookSerializer(many=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'books']


class CustomBookSerializer(Serializer):
    title = serializers.CharField()
    text = serializers.CharField()
    genre = serializers.JSONField()

    def create(self, validated_data):
        b = Book(title=validated_data['title'], text=validated_data['text'], slug=slugify(validated_data['title']))
        b.save()
        b.author.add(validated_data['user'])
        for g in validated_data['genre']:
            req_g = Genre.objects.get(id=g)
            b.genre.add(req_g)
        b.save()
        return b


class CustomRateSerializer(Serializer):
    book_id = serializers.IntegerField()
    rate = serializers.IntegerField()

    def create(self, validated_data):
        return BookLike.objects.create(**validated_data)


class UserAPISerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['username']


class BookAPISerializer(serializers.ModelSerializer):
    author = UserAPISerializer(many=True)
    genre = GenreSerializer(many=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'text', 'author', 'genre']


class AuthorBooksAPISerializer(ModelSerializer):
    books = BookAPISerializer(many=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'books']
