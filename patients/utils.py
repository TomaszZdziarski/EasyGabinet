from django.db.models import Q
from dentists.models import Article


def searchArticles(request):
    search_query = ''

    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')

    #tags = Tag.objects.filter(name__icontains=search_query)

    articles = Article.objects.distinct().filter(
        Q(title__icontains=search_query) |
        Q(content__icontains=search_query)
        #Q(author__name__icontains=search_query)
        #Q(tags__in=tags)

    )
    return articles,search_query

