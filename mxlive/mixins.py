from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from django.conf import settings

from tempfile import mkdtemp
from slugify import slugify
import subprocess
import os
import shutil

TEMP_PREFIX = getattr(settings, 'TEX_TEMP_PREFIX', 'render_tex-')
CACHE_PREFIX = getattr(settings, 'TEX_CACHE_PREFIX', 'render-tex')
CACHE_TIMEOUT = getattr(settings, 'TEX_CACHE_TIMEOUT', 30), # 86400)  # 1 day

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to allow access through a view only if the user is a superuser.
    Can be used with any View.
    """
    def test_func(self):
        return self.request.user.is_superuser


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.object.pk,
            }
            return JsonResponse(data)
        else:
            return response

class Tex2PdfMixin(object):
    """
    Mixin to create a .pdf file from a LaTeX template.
    """

    def get_template_name(self):
        return "users/base.html"

    def get(self, request, *args, **kwargs):
        object = self.get_object()
        name = slugify(object.name)
        context = self.get_template_context()
        template = get_template(self.get_template_name())

        rendered_tpl = template.render(context).encode('utf-8')

        tmp = mkdtemp(prefix=TEMP_PREFIX)
        tex_file = os.path.join(tmp, '%s.tex' % name)
        f = open(tex_file, 'w')
        f.write(rendered_tpl)
        f.close()
        try:
            FNULL = open(os.devnull, 'w')
            process = subprocess.call(['xelatex', '-interaction=nonstopmode', tex_file], cwd=tmp, stdout=FNULL, stderr=subprocess.STDOUT)

            try:
                pdf = open("%s/%s.pdf" % (tmp, name))
            except:
                if request.user.is_superuser:
                    log = open("%s/%s.log" % (tmp, name)).read()
                    return HttpResponse(log, "text/plain")
                else:
                    raise RuntimeError("xelatex error (code %s) in %s/%s" % (process, tmp, name))

        finally:
            shutil.rmtree(tmp)

        res = HttpResponse(pdf, "application/pdf")

        return res