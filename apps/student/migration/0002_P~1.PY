from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='payment_mode',
            field=models.CharField(
                choices=[
                    ('Cash', 'Cash'),
                    ('Check', 'Check'),
                    ('Online', 'Online Transfer'),
                    ('GCash', 'GCash'),
                    ('Bank', 'Bank Deposit'),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='proof_of_payment',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='payment_proofs/%Y/%m/%d/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
            ),
        ),
    ]
