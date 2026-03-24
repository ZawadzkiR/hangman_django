from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0006_room_mistake_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="multiplayerroom",
            name="room_mode",
            field=models.CharField(choices=[("vs", "VS"), ("coop", "Co-op")], default="vs", max_length=12),
        ),
        migrations.AddField(
            model_name="multiplayerroom",
            name="shared_guessed_letters",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="multiplayerroom",
            name="shared_mistakes",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="multiplayerroom",
            name="current_turn_order",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
