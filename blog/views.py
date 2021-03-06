from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Post, Category, Tag, Comment
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify
from .forms import CommentForm

# rest framework
from .serializers import PostSerializer, CommentSerializer
from rest_framework import generics, viewsets


# Create your views here.

# REST Framework

# viewsets
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer






# generic APIView
# class PostListApi(generics.ListAPIView):
#     queryset = Post.objects.all().order_by('-created_at')
#     serializer_class = PostSerializer
#
#
# class PostDetailApi(generics.RetrieveAPIView):
#     queryset = Post.objects.all()
#     serializer_class = PostSerializer
#
#
# class PostCreateApi(generics.CreateAPIView):
#     serializer_class = PostSerializer
#
#     def get_object(self, queryset=None):
#         return Post.objects.filter(author=self.request.user)
#
#     def post(self, request, *args, **kwargs):
#         return self.create(request)
#
#
# class CategoryListApi(PostListApi):
#     def get_queryset(self, **kwargs):
#         return Post.objects.filter(category__slug=self.kwargs['slug'])
#
#
# class TagListApi(PostListApi):
#     def get_queryset(self, **kwargs):
#         return Post.objects.filter(tags__slug=self.kwargs['slug'])
#
#
# class CommentApiView(viewsets.ModelViewSet):
#     serializer_class = CommentSerializer
#     queryset = Comment.objects.all()




# CBV를 이용한 views 클래스 구현하기.
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
        context['comment_form'] = CommentForm
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
class PostCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    fields = [
        'title',
        'content',
        'hook_text',
        'head_img',
        'file_upload',
        'category'
    ]

    # 스태프 또는 슈퍼 유저만 포스트 작성 폼에 접근 권한 부여.
    def test_func(self):
        return self.request.user.is_superuser or self.request.is_staff

    # 로그인한 사용자만 포스트 작성 폼 접근 가능.
    def form_valid(self, form):
        current_user = self.request.user
        if current_user.is_authenticated and (current_user.is_staff or current_user.is_usperuser):
            form.instance.author = current_user

            # form_valid() 함수의 결과값을 response에 저장.
            response = super(CreateView, self).form_valid(form)

            # post_form.html에서 form method가 post로 설정된 내용에서 tags_str로 전달된 값을 변수로 저장.
            tags_str = self.request.POST.get('tags_str')
            if tags_str:
                tags_str = tags_str.strip()
                tags_str = tags_str.replace(';', ',')
                tags_list = tags_str.split(',')

                for t in tags_list:
                    t = t.strip()

                    # get_or_create() 메서드는 name이 t인 tag 인스턴스와 두번째는 이 인스턴스가 새로 생성되었는지 나타내는 bool 형태 값.
                    tag, is_tag_created = Tag.objects.get_or_create(name=t)

                    if is_tag_created:
                        tag.slug = slugify(t, allow_unicode=True)
                        tag.save()

                    self.objects.tags.add(tag)
            return response
        else:
            return redirect('/blog/')

# 포스트 수정 폼
class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post
    fields = [
        'title',
        'content',
        'hook_text',
        'head_img',
        'file_upload',
        'category'
    ]

    template_name = 'blog/post_update_form.html'

    # CBV를 사용할 떄 템플릿으로 추가 인자를 넘기기 위함.
    def get_context_data(self, **kwargs):
        context = super(PostUpdate, self).get_context_data()
        if self.object.tags.exists():
            tags_str_list = list()
            for t in self.object.tags.all():
                tags_str_list.append(t.name)
            context['tags_str_list'] = ','.join(tags_str_list)

        return context


    # dispatch() 메서드는 방문자가 서버에 GET방식인지 POST방식으로 요청했는지 판단하는 기능.
    def dispatch(self, request, *args, **kwargs):
        # self.get_object() == Post.objects.get(pk=pk)와 같다.
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(PostUpdate, self).dispatch(request, *args, **kwargs)
        # 권한이 없는 방문자가 접근할때 403오류 메시지 출력.
        else:
            raise PermissionDenied

    def form_valid(self, form):
        response = super(PostUpdate, self).form_valid(form)
        # 수정 전의 태그 데이터를 삭제
        self.object.tags.clear()
        tags_str = self.request.POST.get('tags_str')

        if tags_str:
            tags_str = tags_str.strip()
            tags_str = tags_str.replace(';', ',')
            tags_list = tags_str.split(',')

            for t in tags_list:
                t = t.strip()
                tag, is_tag_created = Tag.object.get_or_create(name=t)
                if is_tag_created:
                    tag.slug = slugify(t, allow_unicode=True)
                    tag.save()
                self.object.tag.add(tag)

        return response


# 댓글 작성
def new_comment(request, pk):
    if request.user.is_authenticated:
        post = get_object_or_404(Post, pk=pk)

        if request.method == 'POST':
            comment_form = CommentForm(request.POST)

            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.post = post
                comment.author = request.user
                comment.save()
                return redirect(comment.get_absolute_url())
        else:
            return redirect(post.get_absolut_url())
    else:
        raise PermissionDenied




