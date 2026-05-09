from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Post, Comment

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['created_at']


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'post', 'created_at']
        read_only_fields = ['author', 'post', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category_detail = CategorySerializer(source='category', read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author',
            'category', 'category_detail',
            'is_published', 'created_at', 'updated_at',
            'comments_count',
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_comments_count(self, obj):
        return obj.comments.count()


class PostListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category_detail = CategorySerializer(source='category', read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'author', 'category', 'category_detail',
            'is_published', 'created_at', 'updated_at', 'comments_count',
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_comments_count(self, obj):
        return obj.comments.count()
