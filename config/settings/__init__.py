from .base import *

env_name = os.environ.get('DJANGO_ENV', 'development')
if env_name == 'production':
    from .production import *
else:
    from .development import *
