from django.contrib import admin

from import_export.admin import ImportExportMixin

from .models import (
    Page,
    Resource,
    Category,
    EmailTemplate,
    ResourceImage,
    EmailQueueItem,
)


class ResourceAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "post_status",
        "event_source_timezone",
        "contact",
        "institution",
        "year",
    )
    readonly_fields = (
        "uuid",
        "created",
        "modified",
    )
    search_fields = (
        "post_id",
        "title",
        "country",
        "contact",
        "firstname",
        "lastname",
        "email",
        "institution",
        "link",
    )
    list_filter = ("post_status", "post_type", "event_type", "notified", "year")

    change_form_template = "web/admin/change_form.html"

    save_as = True


class PageAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    change_form_template = "web/admin/change_form.html"


class CategoryAdmin(admin.ModelAdmin):
    pass


class EmailTemplateAdmin(admin.ModelAdmin):
    pass


class ResourceImageAdmin(admin.ModelAdmin):
    pass


class EmailQueueItemAdmin(admin.ModelAdmin):
    pass


admin.site.register(Resource, ResourceAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(ResourceImage, ResourceImageAdmin)
admin.site.register(EmailQueueItem, EmailQueueItemAdmin)
