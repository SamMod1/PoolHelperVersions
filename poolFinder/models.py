from django.db import models
from django.contrib.auth.models import User

SYSTEM_USER_ID = 1

class Batch(models.Model):
    batch = models.CharField(max_length=18, primary_key=True)
    batch_time = models.DateTimeField()
    escalations = models.CharField(max_length=126)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default = SYSTEM_USER_ID)
    in_ff = models.BooleanField(default=True) # Rename to in_fast_finder?
    summary = models.TextField(default='Buffer Summary Unavailable')
    plates = models.CharField(max_length=158, default = '')
    araya = models.CharField(max_length=8, default = 'Unknown')
    buffers = models.CharField(max_length=128, default = '') # Better being left as NULL
    prio_plates = models.CharField(max_length=128, default = '')
    vip_plates = models.CharField(max_length=128, default = '')
    plates_to_do = models.CharField(max_length=128, default = '')

    def __str__(self):
        return self.batch


class AnalysedPlate(models.Model):
    array_code = models.CharField(max_length=9, primary_key=True)
    pool = models.CharField(max_length=12, default='NONE')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    date_in = models.DateTimeField()
    araya = models.CharField(max_length=8, default = 'Unknown')
    pl_comments = models.TextField(default='Unavailable')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default = 1)
    in_ff = models.BooleanField(default=True)
    show_in_plates_in_fastfinder = models.BooleanField(default=True)
    escalated = models.BooleanField(default=False)
    escalation_reason = models.TextField(default = 'NONE')
    repooled = models.BooleanField(default=False)
    restamped = models.BooleanField(default=False)
    prio = models.BooleanField(default=False)
    vip = models.BooleanField(default=False)
    average_rox = models.IntegerField(default=0)
    rox_sd = models.IntegerField(default=0)
    total_rox_below_threshold = models.SmallIntegerField(default=0)
    patient_rox_below_threshold = models.SmallIntegerField(default=0)
    rox_above_threshold = models.SmallIntegerField(default=0)
    high_plods = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.array_code


class Sample(models.Model):
    plate = models.ForeignKey(AnalysedPlate, on_delete=models.CASCADE, db_index=True)
    batch = models.CharField(max_length=18, default='NONE')
    x384_well = models.CharField(max_length=3)
    fam = models.IntegerField()
    vic = models.IntegerField()
    rox = models.IntegerField()
    nfam = models.FloatField(null=True)
    nvic = models.FloatField(null=True)
    flag = models.CharField(max_length=20)
    barcode = models.CharField(max_length=3)

    class Meta:
        unique_together = ('plate', 'x384_well',)


class PlateSummary(models.Model):
    plate = models.ForeignKey(AnalysedPlate, on_delete=models.CASCADE, db_index=True)
    plate_location = models.CharField(max_length=3)
    positives = models.SmallIntegerField(default=0)
    plods = models.SmallIntegerField(default=0)
    negatives = models.SmallIntegerField(default=0)
    vic_fails = models.SmallIntegerField(default=0)
    total_samples = models.SmallIntegerField(default=0)
    inact_plate = models.CharField(max_length=13)
    nexar_or_dwp_ham = models.CharField(max_length=10)
    araya_or_elute = models.CharField(max_length=13)
    hydrocycler_or_kf = models.CharField(max_length=11)
    df_or_384_ham = models.CharField(max_length=11)

    class Meta:
        unique_together = ('plate', 'plate_location',)


class ArayaThresholds(models.Model):
    araya = models.CharField(max_length=8)
    positive = models.FloatField()
    negative = models.FloatField()
    nvic = models.FloatField()
    low_rox = models.FloatField()
    high_rox = models.FloatField()
    lj_mean_accu = models.FloatField(default=0)
    lj_mean_qneg = models.FloatField(default=0)
    lj_mean_qpos = models.FloatField(default=0)
    lj_sd_accu = models.FloatField(default=0)
    lj_sd_qneg = models.FloatField(default=0)
    lj_sd_qpos = models.FloatField(default=0)

    def __str__(self):
        return self.araya


class PoolFinderConfig(models.Model):
    option = models.CharField(max_length=100, primary_key=True)
    value = models.TextField()

    def __str__(self):
        return self.option

    @classmethod
    def get_value(self, name):
        return PoolFinderConfig.objects.get(option = name).value


class Permissions(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_cva = models.BooleanField(default=False)
    is_cva_delagate = models.BooleanField(default=False)
