import datetime as dt

from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView
)
from django.urls import reverse, reverse_lazy


from .models import Post, Category, Comment, User
from .forms import CommentForm, PostForm, UserForm

PAGINATOR = 10


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = PAGINATOR

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User, username=self.kwargs['username']
        )
        return context

    def get_queryset(self):
        user = get_object_or_404(
            User, username=self.kwargs['username']
        )
        comments = Comment.objects.all()
        posts = Post.objects.select_related(
            'author',
            'category',
            'location',
        ).prefetch_related(
            Prefetch('comments', queryset=comments)
        ).filter(author=user).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
        if user != self.request.user:
            posts = posts.filter(
                is_published=True,
                pub_date__lt=dt.datetime.now()
            )
        return posts


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserForm
    template_name = 'blog/user.html'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile', args=[self.request.user])


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            args=[self.request.user]
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
            kwargs={'post_id': self.kwargs['post_id']}
        )


class PostDeleteView(LoginRequiredMixin, PostDispatchMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, pk=post_id)
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
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
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )


class CommentUpdateView(CommentMixin, LoginRequiredMixin, UpdateView):
    pass


class CommentDeleteView(CommentMixin, LoginRequiredMixin, DeleteView):
    pass


def output_published():
    return Post.objects.select_related(
        'category', 'location', 'author'
    ).prefetch_related(
        Prefetch('comments', queryset=Comment.objects.all())
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=dt.datetime.now()
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = PAGINATOR

    def get_queryset(self):
        return output_published()


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.all().select_related(
            'author'
        )
        return context

    def get_queryset(self):
        posts = Post.objects.select_related(
            'category', 'location', 'author'
        ).prefetch_related(
            Prefetch('comments', queryset=Comment.objects.all())
        ).annotate(comment_count=Count('comments'))
        if self.request.user != get_object_or_404(
            posts, pk=self.kwargs[self.pk_url_kwarg]
        ).author:
            posts = posts.filter(
                is_published=True,
                category__is_published=True,
                pub_date__lt=dt.datetime.now()
            )
        return posts


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = PAGINATOR

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category.objects.all(),
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return context

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return output_published().filter(
            category=category,
            is_published=True
        )
