from django.db import models

# Create your models here.
class OpenID(models.Model):
    PROVIDER_CHOICES = [
             ('google', 'google'),
             ('yandex', 'yandex'),
             ('mailruapi', 'mailruapi'),
             ('mailru', 'mailru'),
             ('vkontakte', 'vkontakte'),
             ('facebook', 'facebook'),
             ('twitter', 'twitter'),
             ('loginza', 'loginza'),
             ('myopenid', 'myopenid'),
             ('webmoney', 'webmoney'),
             ('rambler', 'rambler'),
             ('flickr', 'flickr'),
             ('lastfm', 'lastfm'),
             ('verisign', 'verisign'),
             ('aol', 'aol'),
             ('steam', 'steam'),
             ('openid', 'openid'),
             ]

    uid = models.CharField(max_length=128, db_index=True)

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_url = models.URLField()


    profile_json = models.TextField()

    datetime_create = models.DateTimeField(auto_now_add=True)
    datetime_update = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('provider', 'uid')

    def get_profile_data(self):
        import json
        try:
            return json.loads(self.profile_json)
        except ValueError:
            pass
        return {}
