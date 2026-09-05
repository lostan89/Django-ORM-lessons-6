from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count, Prefetch
from django.db import connection


def get_related_posts_count(tag):
    return tag.posts.count()

def get_likes_count(posts):
    return posts.likes.count()

def serialize_post(post):
    tags_list = list(post.tags.all())
    first_tag_title = tags_list[0].title if tags_list else None

    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in tags_list],
        'first_tag_title': post.tags.all()[0].title,
    }

def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_with_tag
    }

def index(request):

    tags = Tag.objects.annotate(posts_with_tag=Count('posts')).order_by()
    print(tags[0].posts_with_tag)
    most_popular_posts = Post.objects.popular().select_related('author').prefetch_related(Prefetch('tags',queryset=tags),'tags__posts')[:5]

    most_popular_posts_ids = [post.id for post in most_popular_posts]

    posts_with_comments = Post.objects.filter(id__in=most_popular_posts_ids).fetch_with_comments_count()
    ids_and_comments = posts_with_comments.values_list('id', 'comments_count')
    count_for_id = dict(ids_and_comments)
    for post in most_popular_posts:
        post.comments_count = count_for_id[post.id]

    fresh_posts = Post.objects.fetch_with_comments_count().select_related('author').order_by('-published_at')

    most_fresh_posts = fresh_posts.prefetch_related(Prefetch('tags',queryset=tags))[:5]
    
    most_popular_tags = tags.popular()[:5]
    
    context = {
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [
            serialize_post(post) for post in most_fresh_posts
        ],
        'popular_tags': [
            serialize_tag(tag) for tag in most_popular_tags
        ],
    }
    return render(request, 'index.html', context)

def post_detail(request, slug):
    post = Post.objects.annotate(likes_count=Count('likes')).prefetch_related(Prefetch('tags',queryset=Tag.objects.annotate(posts_with_tag=Count('posts')))).get(slug=slug)
    comments = Comment.objects.filter(post=post).select_related('author')
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    related_tags = post.tags.all()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    all_tags = Tag.objects.annotate(posts_with_tag=Count('posts'))
    
    most_popular_tags = all_tags.popular()[:5]

    most_popular_posts = []  # TODO. Как это посчитать?

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    all_tags = Tag.objects.annotate(posts_with_tag=Count('posts'))
    most_popular_tags = all_tags.popular()[:5]

    top_post_ids = (
    Post.objects
    .annotate(likes_count=Count('likes', distinct=True))
    .order_by('-likes_count')
    [:5]
    .values_list('id', flat=True)
)

    most_popular_posts = (
        Post.objects
        .filter(id__in=top_post_ids)
        .annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
        )
        .select_related('author')
        .prefetch_related(Prefetch('tags',queryset=all_tags))
    )
   
    related_posts = (
        tag.posts
        .annotate(comments_count=Count('comments', distinct=True))
        .select_related('author')
        .prefetch_related(Prefetch('tags',queryset=all_tags))
        [:20]
    )
    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
