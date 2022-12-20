from django import forms


class CrawlerUrlForm(forms.Form):
    url = forms.URLField(
        widget=forms.TextInput(
            attrs={"class": "form-control mx-sm-3", "id": "inlineFormInput"}
        )
    )
