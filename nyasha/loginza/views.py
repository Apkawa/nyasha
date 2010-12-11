# -*- coding: utf-8 -*-
import json
import urllib

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_list_or_404, redirect, get_object_or_404
from models import OpenID

@csrf_exempt
def openid_login(request, secret_hash,  provider=None):
    if secret_hash == request.session.get('openid_secret_hash') and 'token' in request.POST:
        token = request.POST['token']
        profile_json = urllib.urlopen("http://loginza.ru/api/authinfo?token=%s"%token).read()
        try:
            profile_data = json.loads(profile_json)
        except ValueError:
            pass

        if not provider:
            provider_url = profile_data['provider']
            for p, p_name in OpenID.PROVIDER_CHOICES:
                if p in provider_url:
                    provider = p
                    break

        o, created = OpenID.objects.get_or_create(
                provider_url=profile_data['provider'], 
                uid=profile_data['uid'],
                defaults={'profile_json':profile_json}
                )

        request.session['openid_pk'] = o.pk

    if 'openid_secret_hash' in request.session:
        del request.session['openid_secret_hash']
    return redirect('login')
