from django.contrib import admin
from blog.models import Post, Tag, Comment

class AuthorAdmin(admin.ModelAdmin):
    raw_id_fields = ['post','author']
    list_display = ['post', 'author']

class PostAdmin(admin.ModelAdmin):
    raw_id_fields = ['likes']


admin.site.register(Post,PostAdmin)
admin.site.register(Tag)
admin.site.register(Comment,AuthorAdmin)
