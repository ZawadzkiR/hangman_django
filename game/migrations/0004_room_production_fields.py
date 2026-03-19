from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0003_multiplayer_and_translation_key'),
    ]

    operations = [
        migrations.AddField(model_name='multiplayerparticipant', name='is_ready', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='multiplayerroom', name='max_players', field=models.PositiveIntegerField(default=10)),
        migrations.AddField(model_name='multiplayerroom', name='max_rounds', field=models.PositiveIntegerField(default=10)),
        migrations.AddField(model_name='multiplayerroom', name='target_score', field=models.PositiveIntegerField(default=120)),
        migrations.AddField(model_name='multiplayerroom', name='winner_name', field=models.CharField(blank=True, max_length=32)),
    ]
