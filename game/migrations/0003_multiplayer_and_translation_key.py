from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_alter_gamesession_options_alter_word_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='word',
            name='translation_key',
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.CreateModel(
            name='MultiplayerRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=8, unique=True)),
                ('host_name', models.CharField(max_length=32)),
                ('host_session', models.CharField(db_index=True, max_length=64)),
                ('host_language', models.CharField(choices=[('pl', 'Polski'), ('sk', 'Slovenský'), ('en', 'English')], default='en', max_length=2)),
                ('status', models.CharField(choices=[('waiting', 'Waiting'), ('playing', 'Playing'), ('round_over', 'Round over'), ('finished', 'Finished')], default='waiting', max_length=16)),
                ('turn_seconds', models.PositiveIntegerField(default=45)),
                ('round_number', models.PositiveIntegerField(default=0)),
                ('current_translation_key', models.CharField(blank=True, max_length=64)),
                ('current_word_text', models.CharField(blank=True, max_length=64)),
                ('current_word_language', models.CharField(choices=[('pl', 'Polski'), ('sk', 'Slovenský'), ('en', 'English')], default='en', max_length=2)),
                ('current_category', models.CharField(blank=True, max_length=64)),
                ('turn_started_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='MultiplayerParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_token', models.CharField(db_index=True, max_length=64)),
                ('nickname', models.CharField(max_length=32)),
                ('order_no', models.PositiveIntegerField(default=1)),
                ('language', models.CharField(choices=[('pl', 'Polski'), ('sk', 'Slovenský'), ('en', 'English')], default='en', max_length=2)),
                ('score', models.IntegerField(default=0)),
                ('guessed_letters', models.TextField(blank=True)),
                ('mistakes', models.PositiveSmallIntegerField(default=0)),
                ('round_status', models.CharField(choices=[('idle', 'Idle'), ('playing', 'Playing'), ('won', 'Won'), ('lost', 'Lost'), ('timeout', 'Timeout')], default='idle', max_length=16)),
                ('current_word_text', models.CharField(blank=True, max_length=64)),
                ('current_category', models.CharField(blank=True, max_length=64)),
                ('current_hint', models.CharField(blank=True, max_length=128)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='game.multiplayerroom')),
            ],
            options={'ordering': ['order_no', 'joined_at'], 'unique_together': {('room', 'session_token')}},
        ),
    ]
