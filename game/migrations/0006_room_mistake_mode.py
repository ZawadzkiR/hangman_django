from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('game', '0005_room_filters_unlimited'),
    ]

    operations = [
        migrations.AddField(
            model_name='multiplayerroom',
            name='mistake_mode',
            field=models.CharField(default='medium', max_length=16),
        ),
    ]
