from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ["core:home", "products:list", "core:about", "core:contact"]

    def location(self, item):
        return reverse(item)
