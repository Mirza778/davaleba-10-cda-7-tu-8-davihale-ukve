from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Post, Comment
from .serializers import (
    CategorySerializer,
    PostSerializer,
    PostListSerializer,
    CommentSerializer,
)
from .permissions import IsAuthorOrReadOnly, IsEditorGroup
from .pagination import StandardResultsPagination


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    @action(detail=True, methods=['get'], url_path='posts')
    def category_posts(self, request, pk=None):
        category = self.get_object()
        posts = category.posts.filter(is_published=True).select_related('author', 'category')
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('author', 'category').all()
    permission_classes = [IsEditorGroup]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post'],
        url_path='publish',
        permission_classes=[IsAuthenticated, IsEditorGroup]
    )
    def publish(self, request, pk=None):
        post = self.get_object()
        post.is_published = True
        post.save(update_fields=['is_published', 'updated_at'])
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['get'],
        url_path='comments_count',
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def comments_count(self, request, pk=None):
        post = self.get_object()
        count = post.comments.count()
        return Response({
            'post_id': post.id,
            'comments_count': count,
        })

    @action(
        detail=False,
        methods=['get'],
        url_path='my_posts',
        permission_classes=[IsAuthenticated]
    )
    def my_posts(self, request):
        posts = Post.objects.filter(
            author=request.user
        ).select_related('author', 'category')
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrReadOnly]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'comment_create'

    def get_queryset(self):
        post_pk = self.kwargs.get('post_pk')
        return Comment.objects.filter(
            post_id=post_pk
        ).select_related('author', 'post')

    def perform_create(self, serializer):
        post_pk = self.kwargs.get('post_pk')
        post = Post.objects.get(pk=post_pk)
        serializer.save(author=self.request.user, post=post)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        is_moderator = request.user.groups.filter(name='მოდერატორები').exists()
        is_author = comment.author == request.user
        if not (is_author or is_moderator or request.user.is_staff):
            return Response(
                {'detail': 'კომენტარის წაშლის უფლება არ გაქვთ.'},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
