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
        fields = '__all__'
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'comment': forms.Textarea(attrs={'rows': '20', 'col': '40'})
        }
        exclude = ('author', 'is_published',)


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
