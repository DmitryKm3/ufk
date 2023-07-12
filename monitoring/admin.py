from django.contrib import admin

# Register your models here.
from .models import NotifyRecipient, PIF, UK, Rule, RType, CheckLog, MonitoringLog, PUCB
admin.site.register(NotifyRecipient)
admin.site.register(PIF)
admin.site.register(UK)
admin.site.register(Rule)
admin.site.register(RType)
admin.site.register(CheckLog)
admin.site.register(MonitoringLog)
admin.site.register(PUCB)
