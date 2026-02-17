"""Adaptadores de django-allauth para usar email como login."""
from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """Genera username automático desde email en registro."""

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        if not user.username and user.email:
            user.username = (user.email or '').lower()[:150]
            if user.__class__.objects.filter(username=user.username).exists():
                import uuid
                user.username = f"{user.email.split('@')[0]}_{uuid.uuid4().hex[:8]}"[:150]
        if commit:
            user.save()
        return user
