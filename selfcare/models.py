from django.db import models
from django.urls import reverse

# Create your models here.
class DeviceType(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

class Device(models.Model):
    name = models.CharField(max_length=50)
    device_type = models.ForeignKey(DeviceType, null=False, on_delete=models.CASCADE) 
    logo = models.ImageField(upload_to='logo')
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('device', args=[str(self.id)])
