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


def output_published(queryset, author=None):
    info = queryset.select_related(
        'category', 'location', 'author'
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    if author is False:
        return info.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=dt.datetime.now()
        )
    return info


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return dict(**context, profile=get_object_or_404(
            User, username=self.kwargs['username'])
        )

    def get_queryset(self):
        author = get_object_or_404(
            User, username=self.kwargs['username']
        )
        posts = output_published(author.posts.all())
        if author != self.request.user:
            posts = output_published(author.posts.all(), author=False)
        return posts


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserForm
    template_name = 'blog/user.html'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user])


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    slug_field = 'username'

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
            args=[self.kwargs['post_id']]
        )


class PostDeleteView(LoginRequiredMixin, PostDispatchMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return dict(**context, form=PostForm(instance=self.object))

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
            kwargs={'post_id': self.kwargs['post_id']}
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
            kwargs={'post_id': self.object.post.id}
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
        return output_published(Post.objects.all(), author=False)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return dict(
            **context,
            form=CommentForm(),
            comments=Comment.objects.select_related('post')
        )

    def get_queryset(self):
        posts = output_published(
            Post.objects.all()
        ).prefetch_related('comments')
        if self.request.user != get_object_or_404(
            posts, pk=self.kwargs[self.pk_url_kwarg]
        ).author:
            posts = output_published(
                Post.objects.all(),
                author=False
            ).prefetch_related('comments')
        return posts


def category_settings(slug):
    return get_object_or_404(
        Category,
        slug=slug,
        is_published=True
    )


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = NUMBER_OF_POSTS

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return dict(
            **context,
            category=category_settings(self.kwargs['category_slug'])
        )

    def get_queryset(self):
        category = category_settings(self.kwargs['category_slug'])
        return output_published(category.posts.all(), author=False)
