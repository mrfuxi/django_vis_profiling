"""
Django cProfile middleware

Based on:
https://gist.github.com/kesor/1229681
"""

from django.core.exceptions import MiddlewareNotUsed
from django.conf import settings
from django.shortcuts import render
import cProfile
import pstats
import marshal
from cStringIO import StringIO

from views import _render_profile


class cProfileMiddleware(object):
    def __init__(self):
        if not self.is_enable():
            raise MiddlewareNotUsed()

        self.profiler = None
        self.modes = ("profile", "profilebin", "profile_graph")

    def is_enable(self, request=None):
        if getattr(settings, "PROFILER", None):
            if request is None:
                return True

            if not hasattr(self, "modes"):
                raise Exception("No modes specified, something is wrong")

            for mode in self.modes:
                if mode in request.GET:
                    return mode

        return False

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if self.is_enable(request):
            self.profiler = cProfile.Profile()
            args = (request,) + callback_args
            return self.profiler.runcall(callback, *args, **callback_kwargs)

    def process_response(self, request, response):
        state = self.is_enable(request)

        if 'profile' == state:
            self.profiler.create_stats()
            out = StringIO()
            stats = pstats.Stats(self.profiler, stream=out)
            # Values for stats.sort_stats():
            # - calls           call count
            # - cumulative      cumulative time
            # - file            file name
            # - module          file name
            # - pcalls          primitive call count
            # - line            line number
            # - name            function name
            # - nfl                     name/file/line
            # - stdname         standard name
            # - time            internal time

            psort = request.GET.get("profile_sort")

            if psort not in ("tottime", "time", "cumtime", "cumulative", "ncalls", "calls"):
                psort = "time"

            stats.sort_stats(psort).print_stats()
            response.content = out.getvalue()
            response['Content-type'] = 'text/plain'

        elif 'profilebin' == state:
            self.profiler.create_stats()
            response.content = marshal.dumps(self.profiler.stats)
            filename = request.path.strip('/').replace('/', '_') + '.pstat'
            response['Content-Disposition'] = \
                'attachment; filename=%s' % (filename,)
            response['Content-type'] = 'application/octet-stream'

        elif 'profile_graph' == state:
            self.profiler.create_stats()
            stats = pstats.Stats(self.profiler)

            return _render_profile(request, stats)

        return response
