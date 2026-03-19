from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('game', '0004_room_production_fields')]

    operations = [
        migrations.AddField(model_name='multiplayerroom', name='difficulty_mode', field=models.CharField(default='random', max_length=16)),
        migrations.AddField(model_name='multiplayerroom', name='category_mode', field=models.CharField(default='random', max_length=64)),
        migrations.AlterField(model_name='multiplayerroom', name='max_players', field=models.PositiveIntegerField(default=999999)),
    ]
