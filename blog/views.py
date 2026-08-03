from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count
from django.db import connection


def get_related_posts_count(tag):
    return tag.posts.count()

def get_likes_count(posts):
    return posts.likes.count()

def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': len(Comment.objects.filter(post=post)),
        # 'comments_amount': post.comments_amount,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }

def serialize_post_optimized(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': len(Post.objects.filter(tags=tag)),
    }


def index(request):

    # popular_posts = Post.objects.prefetch_related('author').annotate(
    #     likes_count=Count('likes'),
    #     comments_amount=Count('comments')
    #     ).order_by('-likes_count')
    popular_posts = Post.objects.prefetch_related('author').annotate(
        likes_count=Count('likes')
        ).order_by('-likes_count')
    
    most_popular_posts = popular_posts[:5]
    
    most_popular_posts_ids = [post.id for post in most_popular_posts]

    posts_with_comments = Post.objects.filter(id__in=most_popular_posts_ids).annotate(comments_count=Count('comments'))
    ids_and_comments = posts_with_comments.values_list('id', 'comments_count')
    count_for_id = dict(ids_and_comments)

    for post in most_popular_posts:
        post.comments_count = count_for_id[post.id]

    # fresh_posts = Post.objects.prefetch_related('author').annotate(
    #     likes_count=Count('likes'),
    #     comments_amount=Count('comments')
    #     ).order_by('published_at')
    fresh_posts = Post.objects.prefetch_related('author').annotate(
        likes_count=Count('likes')
        ).order_by('-published_at')

    most_fresh_posts = fresh_posts[:5]

    most_fresh_posts_ids = [post.id for post in most_fresh_posts]

    fresh_posts_with_comments = Post.objects.filter(id__in=most_fresh_posts_ids).annotate(comments_count=Count('comments'))
    ids_and_comments = fresh_posts_with_comments.values_list('id', 'comments_count')
    count_for_id = dict(ids_and_comments)
    for post in most_fresh_posts:
        post.comments_count = count_for_id[post.id]

    tags = Tag.objects.all()
    # tags = Tag.objects.prefetch_related('posts')
    # popular_tags = sorted(tags, key=get_related_posts_count)
    popular_tags = tags.annotate(tags_count=Count('posts')).order_by('-tags_count')
    most_popular_tags = popular_tags[:5]

    for post in most_popular_posts:
        print(post.likes_count)
        print(post.comments_count)
   

    
    context = {
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post_optimized(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.get(slug=slug)
    comments = Comment.objects.filter(post=post)
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    likes = post.likes.all()

    related_tags = post.tags.all()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': len(likes),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    all_tags = Tag.objects.all()
    popular_tags = sorted(all_tags, key=get_related_posts_count)
    most_popular_tags = popular_tags[-5:]

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

    all_tags = Tag.objects.all()
    popular_tags = sorted(all_tags, key=get_related_posts_count)
    most_popular_tags = popular_tags[-5:]

    most_popular_posts = []  # TODO. Как это посчитать?

    related_posts = tag.posts.all()[:20]

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
