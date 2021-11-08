from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Post, Category, Tag


# CBV를 이용한 views 클래스 구현하기.
# Create your views here.

# ListView 라이브러리를 이용해서 post 목록을 구현
class PostList(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    ordering = '-pk'

    def get_context_data(self, **kwargs):
        context = super(PostList, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count()
        return context


# DetailView 라이브러리를 이용해서 post 상세화면 구현
class PostDetail(DetailView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super(PostDetail, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count()
        return context

# 카테고리 별 페이지
def category_page(request, slug):
    if slug == 'no_category':
        category = '미분류'
        post_list = Post.objects.filter(category=None)
    else:
        category = Category.objects.get(slug=slug)
        post_list = Post.objects.filter(category=category)
    context = {
        'category': category,
        'post_list': post_list,
        'categories': Category.objects.all(),
        'no_category_post_count': Post.objects.filter(category=None).count()
    }

    return render(request, 'blog/post_list.html', context)

# 태그 별 포스트 목록 페이지
def tag_page(request, slug):
    tag = Tag.objects.get(slug=slug)
    post_list = tag.post_set.all()
    categories = Category.objects.all()
    no_category_post_count = Post.objects.filter(category=None).count()
    context = {
        'tag': tag,
        'post_list': post_list,
        'categories': categories,
        'no_category_post_count': no_category_post_count
    }
    return render(request, 'blog/post_list.html', context)

# 포스트 작성 폼
class PostCreate(LoginRequiredMixin, CreateView):
    model = Post
    fields = [
        'title',
        'content',
        'hook_text',
        'head_img',
        'file_upload',
        'category'
    ]

    def form_valid(self, form):
        current_user = self.request.user
        if current_user.is_authenticated:
            form.instance.author = current_user
            return super(PostCreate, self).form_valid(form)
        else:
            return redirect('/blog/')
