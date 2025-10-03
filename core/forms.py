from django import forms
class UploadForm(forms.Form):
    image = forms.ImageField()
    target_crop = forms.CharField(required=False)
    target_state = forms.CharField(required=False)
