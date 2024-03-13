from django.contrib import admin

from SyncVideo.rooms.models import Room, Category


# Register your models here.

class RoomAdmin(admin.ModelAdmin):
    list_display = ('url', 'description', 'visibility', 'created_at')
    list_filter = ('visibility', 'created_at',)
    search_fields = ('url',)
    filter_horizontal = ('categories',)

admin.site.register(Room, RoomAdmin)
admin.site.register(Category)

# Category.objects.create(name='movies', color="#fcba03")
# Category.objects.create(name='education', color="#036ffc")
# Category.objects.create(name='music', color="#fc0356")
# Category.objects.create(name='cartoons', color="#94fc03")
