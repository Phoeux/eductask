# from django.contrib.auth.models import User
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer

from managebook.models import Comment, Book, BookLike, Genre, User


class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ['book', 'text']

    # def create(self, validated_data):
    #     comm = Comment.objects.create(**validated_data)
    #     comm.save()
    #     return Comment.objects.create(**validated_data)

    # def save(self,*args, **kwargs):
    #     self.Comment.user.save()
    #     super().save(*args, **kwargs)


class CustomCommentSerializer(Serializer):
    book_id = serializers.IntegerField()
    text = serializers.CharField()

    def create(self, validated_data):
        return Comment.objects.create(**validated_data)

    # def save(self, user, *args, **kwargs):
    #     return Comment.objects.create(**self.validated_data, user=user)

    # def delete(self, user, id):
    #     return Comment.objects.delete(user=user, id=id)

    # def delete(self, user, comment_id):
    #     # comment = validated_data['comment_id']
    #     return Comment.objects.filter(id=comment_id, user=user).delete()

    # super().save(request, *args, **kwargs)
    # book = self.validated_data['id']
    # text = self.validated_data['text']


class BookSerializer(ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'text', 'author', 'genre']


class GenreSerializer(ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


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

    # def save(self, user, *args, **kwargs):
    #     author = user
    #     return Book.objects.create(**self.validated_data, author=author)


class CustomRateSerializer(Serializer):
    book_id = serializers.IntegerField()
    rate = serializers.IntegerField()

    def create(self, validated_data):
        return BookLike.objects.create(**validated_data)

    # def save(self, user, *args, **kwargs):
    #     return BookLike.objects.create(**self.validated_data, user=user)