from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('live_photo', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gallery',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='日期'),
        ),
    ] 