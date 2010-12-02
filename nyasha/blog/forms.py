from django import forms
from models import Profile


class PostForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea)



class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('name', 'url', 'comment', 'avatar')
