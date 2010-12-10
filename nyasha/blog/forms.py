from django import forms
from models import Profile
from django.contrib.auth.models import User


class PostForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea)



class ProfileEditForm(forms.ModelForm):
    username = forms.CharField()
    class Meta:
        model = Profile
        fields = ('name', 'url', 'comment', 'avatar', 'is_off')

    def __init__(self, *args, **kwargs):
        ins = kwargs['instance']
        kwargs['initial'] = {'username':ins.user.username}
        super(ProfileEditForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        data = self.cleaned_data
        username = data.get('username')
        if User.objects.filter(username=username
                ).exclude(pk=self.instance.user_id).exists():
            raise forms.ValidationError("New username exists!")

        return username


