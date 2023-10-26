from django import forms

from .models import Comment, Post, User


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',)


class PasswordChangeForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('password',)


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            )
        }
        exclude = ('author',)


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
