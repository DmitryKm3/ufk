from django.db import models

# Create your models here.
class NotifyRecipient(models.Model):
    email_address = models.EmailField()
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

class UK(models.Model):
    uk_npp = models.IntegerField()
    uk_name = models.CharField(max_length=500)
    uk_shortname = models.CharField(max_length=200)
    uk_inn = models.CharField(max_length=12)
    uk_ogrn = models.DecimalField(max_digits=15, decimal_places=0)
    uk_nlic = models.CharField(max_length=14)
    uk_dlic = models.CharField(max_length=10)
    uk_slic = models.CharField(max_length=30)
    uk_addr = models.CharField(max_length=250)
    uk_phones = models.TextField()
    uk_site = models.CharField(max_length=500)
    uk_sitetype = models.CharField(max_length=5)
    uk_enabled = models.BooleanField(default=True)
    uk_lastaccess = models.DateTimeField(auto_now=True)
    uk_lastupdate = models.DateTimeField(auto_now=True)
    uk_extractor = models.CharField(max_length=2048, blank=True)
    uk_site_unavailable_code = models.IntegerField(blank=True)
    uk_site_error_text = models.CharField(max_length=2048, blank=True)

    def __str__(self):
        return self.uk_name


class PIF(models.Model):
    pif_npp = models.IntegerField()
    pif_type = models.CharField(max_length=15)
    pif_status = models.CharField(max_length=23)
    pif_name = models.CharField(max_length=500)
    pif_shortname = models.CharField(max_length=200)
    pif_category = models.CharField(max_length=40)
    pif_npdu = models.CharField(max_length=20)
    pif_dpdu = models.CharField(max_length=10)
    pif_spdu = models.CharField(max_length=10)
    pif_prefnames = models.TextField(blank=True)
    pif_prefpdu = models.TextField(blank=True)
    pif_uk = models.ForeignKey(UK, null=False, on_delete=models.CASCADE)
    pif_enabled = models.BooleanField(default=True)
    pif_lastupdate = models.DateTimeField(auto_now=True)
    pif_checkpage = models.CharField(max_length=2048, blank=True)

    def __str__(self):
        return self.pif_name

class RType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Rule(models.Model):
    name = models.CharField(max_length=200)
    rtype = models.ForeignKey(RType, null=False, on_delete=models.CASCADE)
    uk = models.ForeignKey(UK, null=False, on_delete=models.CASCADE)
    extractor = models.CharField(max_length=200, blank=True)
    selector = models.CharField(max_length=200, blank=True)
    regexp = models.CharField(max_length=300, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class CheckLog(models.Model):
    date_log = models.DateTimeField(auto_now=True)
    uk = models.ForeignKey(UK, null=True, on_delete=models.CASCADE, blank=True)
    pif = models.ForeignKey(PIF, null=True, on_delete=models.CASCADE, blank=True)
    text = models.TextField(blank=True)
    doc_name = models.TextField(blank=True)
    doc_date = models.DateTimeField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return "{} {} {}".format(self.date_log, self.uk, self.pif)

class MonitoringLog(models.Model):
    date = models.DateTimeField(auto_now=True)
    status = models.TextField()
    unavailable = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)

class PUCB(models.Model):
    pucb_npp = models.IntegerField()
    pucb_name = models.CharField(max_length=150)
    pucb_inn = models.CharField(max_length=12)
    pucb_sitetype = models.CharField(max_length=5)
    pucb_site = models.CharField(max_length=500) 
    pucb_enabled = models.BooleanField(default=True)
    pucb_lastaccess = models.DateTimeField(auto_now=True)
