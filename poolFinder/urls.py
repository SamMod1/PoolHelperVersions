from django.urls import path
from poolFinder.views import list_views, other_views


urlpatterns = [
    path('', other_views.home, name = 'Pool Helper-Home'),
    path('batches-awaiting-release/', list_views.batches_awaiting_release, name = 'Pool Helper-Batches Awaiting Release'),
    path('plates-in-ff/', list_views.plates_in_ff, name = 'Pool Helper-Plates in FF'),
    path('batch/<str:pk>/', other_views.batch_overview, name = 'Pool Helper-Batch Overview'),
    path('plate/<str:pk>/', other_views.plate, name = 'Pool Helper-Plate'),
    path('archive/<int:pk>/', list_views.archive, name = 'Pool Helper-Archive'),
    path('search/', other_views.search, name = 'Pool Helper-Search'),
    path('search/result/<str:pk>/', list_views.search_results, name = 'Pool Helper-Search Results'),
    path('modify/<str:pk>/', other_views.modify_plate, name = 'Pool Helper-Modify Plate'),
    path('restart-background-tasks/', other_views.restart_backgrouns_process, name = 'Pool Helper-Task Restart'),
    path('db-api/', other_views.database_api, name = 'Pool Helper-DB API')
]
