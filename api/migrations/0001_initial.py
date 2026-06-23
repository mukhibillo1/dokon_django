from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ArxivMijoz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asl_id', models.IntegerField()),
                ('ism', models.CharField(max_length=255)),
                ('telefon', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField()),
                ('arxivlangan_vaqt', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Mijoz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ism', models.CharField(max_length=255)),
                ('telefon', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Qarz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mahsulot', models.CharField(max_length=255)),
                ('summa', models.FloatField()),
                ('tolandi', models.BooleanField(default=False)),
                ('arxivda', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mijoz', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='qarzlar',
                    to='api.mijoz'
                )),
                ('arxiv_mijoz', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='qarzlar',
                    to='api.arxivmijoz'
                )),
            ],
        ),
    ]
