from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (5, '★★★★★ (5/5)'),
        (4, '★★★★☆ (4/5)'),
        (3, '★★★☆☆ (3/5)'),
        (2, '★★☆☆☆ (2/5)'),
        (1, '★☆☆☆☆ (1/5)'),
    ]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Ваша оцінка"
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment', 'image']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Поділіться своїми враженнями про товар...'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'comment': 'Ваш відгук',
            'image': 'Прикріпити фото (опціонально)',
        }