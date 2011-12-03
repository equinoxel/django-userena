from django.utils import translation
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.template import RequestContext, loader
from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden



from userena import settings as userena_settings


class Http403(Exception):
    pass

def render_to_403(*args, **kwargs):
    """
    Returns a HttpResponseForbidden whose content is filled with the result of calling
    django.template.loader.render_to_string() with the passed arguments.
    """
    if not isinstance(args,list):
        args = []
        args.append('403.html')

    httpresponse_kwargs = {'mimetype': kwargs.pop('mimetype', None)}
    response = HttpResponseForbidden(loader.render_to_string(*args, **kwargs), **httpresponse_kwargs)

    return response

class UserenaLocaleMiddleware(object):
    """
    Set the language by looking at the language setting in the profile.

    It doesn't override the cookie that is set by Django so a user can still
    switch languages depending if the cookie is set.

    """
    def process_request(self, request):
        lang_cookie = request.session.get(settings.LANGUAGE_COOKIE_NAME)
        if not lang_cookie:
            if request.user.is_authenticated():
                try:
                    profile = request.user.get_profile()
                except (ObjectDoesNotExist, SiteProfileNotAvailable):
                    profile = False

                if profile:
                    try:
                        lang = getattr(profile, userena_settings.USERENA_LANGUAGE_FIELD)
                        translation.activate(lang)
                        request.LANGUAGE_CODE = translation.get_language()
                    except AttributeError: pass

    def process_exception(self,request,exception):
        if isinstance(exception,Http403):
            if settings.DEBUG:
                raise PermissionDenied
            return render_to_403(context_instance=RequestContext(request, {'message': exception.message,
                                                                           'request_path': request.path}))
