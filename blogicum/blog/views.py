import datetime as dt

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView
)
from django.urls import reverse

from .forms import CommentForm, PostForm, UserForm
from .models import Post, Category, Comment, User

NUMBER_OF_POSTS = 10


def output_published(queryset, skip_filter=True):
    queryset = queryset.select_related(
        'category', 'location', 'author'
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    if not skip_filter:
        return queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=dt.datetime.now()
        )
    return queryset


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS

    def get_author(self):
        return get_object_or_404(
            User, username=self.kwargs['username']
        )

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            profile=self.get_author()
        )

    def get_queryset(self):
        author = self.get_author()
        return output_published(
            author.posts.all(),
            not author != self.request.user
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user.username])


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user.username]
        )


class PostDispatchMixin:

    def dispatch(self, *args, **kwargs):
        object = self.get_object()
        if self.request.user != object.author:
            return redirect('blog:post_detail', post_id=object.id)
        return super().dispatch(*args, **kwargs)


class PostUpdateView(PostDispatchMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs[self.pk_url_kwarg]]
        )


class PostDeleteView(LoginRequiredMixin, PostDispatchMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            form=PostForm(instance=self.object)
        )

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user.username]
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.object.post.id]
        )


class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self, **kwargs):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            author=self.request.user)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.object.post.id]
        )


class CommentUpdateView(CommentMixin, LoginRequiredMixin, UpdateView):
    pass


class CommentDeleteView(CommentMixin, LoginRequiredMixin, DeleteView):
    pass


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = NUMBER_OF_POSTS

    def get_queryset(self):
        return output_published(Post.objects.all(), skip_filter=False)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            form=CommentForm(),
            comments=Comment.objects.select_related('post')
        )

    def get_queryset(self):
        return output_published(
            Post.objects.all(),
            not self.request.user != get_object_or_404(
                Post, pk=self.kwargs[self.pk_url_kwarg]
            ).author
        ).prefetch_related('comments')


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = NUMBER_OF_POSTS

    def get_category(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            category=self.get_category()
        )

    def get_queryset(self):
        return output_published(
            self.get_category().posts.all(),
            skip_filter=False
        )
