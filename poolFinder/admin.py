from django.contrib import admin
import poolFinder.models as db


admin.site.register(db.Batch)
admin.site.register(db.AnalysedPlate)
admin.site.register(db.Sample)
admin.site.register(db.ArayaThresholds)
admin.site.register(db.PoolFinderConfig)
admin.site.register(db.Permissions)
admin.site.register(db.PlateSummary)
