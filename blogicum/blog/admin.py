from django.contrib import admin

from .models import Post, Category, Comment, Location

admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Location)


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'is_published',
        'created_at',
        'category',
        'location',
    )
    list_editable = (
        'is_published',
    )
    search_fields = ('title',)
    list_filter = ('category',)
    list_display_links = ('title',)


admin.site.register(Post, PostAdmin)
