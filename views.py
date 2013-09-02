from django.shortcuts import render

from os import unlink
from tempfile import NamedTemporaryFile

from forms import ProfileFileForm
from stats_parser import pstats_to_json


def profile_from_file(request):
    if request.method == 'POST':
        form = ProfileFileForm(request.POST, request.FILES)
        if form.is_valid():
            prof_file = request.FILES['prof_file']
            #stats = prof_file.read()
            tmp_f = NamedTemporaryFile(delete=False)
            tmp_f.write(prof_file.read())
            tmp_f.close()

            response = _render_profile(request, tmp_f.name)
            unlink(tmp_f.name)

            return response
    else:
        form = ProfileFileForm()

    data = {'form': form,
            'page_title': 'Profile from file',
            }

    return render(request, 'from_file.html', data)


def _render_profile(request, stats):
    json_data, total_tt = pstats_to_json(stats)

    return render(request, 'prof.html', {
                'json_data': json_data,
                'total_time': total_tt,
                'page_title': 'Request profiler',
            })
