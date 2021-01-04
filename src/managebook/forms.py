from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.forms import ModelForm, Textarea, TextInput, SelectMultiple
from django import forms

from managebook.models import Book, Comment


class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'text', 'genre')
        widgets = {
            'title': TextInput(attrs={'class': 'form-control'}),
            'text': Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'genre': SelectMultiple(attrs={'class': 'form-control'})
        }
        labels = {
            'title': 'hello title'
        }
        help_text = {
            'text': 'special text for special ppl'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CustomUserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        widgets = {'username': TextInput(attrs={'class': 'form-control'})}

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        strip=False,
    )


class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password','class': 'form-control'}),
    )