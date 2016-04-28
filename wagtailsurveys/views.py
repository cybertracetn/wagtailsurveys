from __future__ import unicode_literals

import csv

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.encoding import smart_str
from django.utils.six import text_type
from django.utils.translation import ugettext as _
from unidecode import unidecode

from wagtail.utils.pagination import paginate
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin import messages

from wagtailsurveys.models import get_surveys_for_user


def index(request):
    survey_pages = get_surveys_for_user(request.user)

    paginator, survey_pages = paginate(request, survey_pages)

    return render(request, 'wagtailsurveys/index.html', {
        'survey_pages': survey_pages,
    })


def delete_submission(request, page_id, submission_id):
    if not get_surveys_for_user(request.user).filter(id=page_id).exists():
        raise PermissionDenied

    page = get_object_or_404(Page, id=page_id).specific
    submission = get_object_or_404(page.get_submission_class(), id=submission_id)

    if request.method == 'POST':
        submission.delete()

        messages.success(request, _("Submission deleted."))
        return redirect('wagtailsurveys:list_submissions', page_id)

    return render(request, 'wagtailsurveys/confirm_delete.html', {
        'page': page,
        'submission': submission
    })


def list_submissions(request, page_id):
    # We can't create backwards relation to Page in AbstractFormSubmission,
    # this is why we need to get specific object
    survey_page = get_object_or_404(Page, id=page_id).specific
    SubmissionClass = survey_page.get_submission_class()

    if not get_surveys_for_user(request.user).filter(id=page_id).exists():
        raise PermissionDenied

    data_fields = survey_page.get_data_fields()

    submissions = SubmissionClass.objects.filter(page=survey_page)
    data_headings = [label for name, label in data_fields]

    if request.GET.get('action') == 'CSV':
        # return a CSV instead
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename=export.csv'

        # Prevents UnicodeEncodeError for questions with non-ansi symbols
        data_headings = [text_type(unidecode(label)) for label in data_headings]

        writer = csv.writer(response)
        writer.writerow(data_headings)
        for s in submissions:
            data_row = []
            form_data = s.get_data()
            for name, label in data_fields:
                data_row.append(smart_str(form_data.get(name)))
            writer.writerow(data_row)
        return response

    paginator, submissions = paginate(request, submissions)

    data_rows = []
    for s in submissions:
        form_data = s.get_data()
        data_row = [form_data.get(name) for name, label in data_fields]
        data_rows.append({
            "model_id": s.id,
            "fields": data_row
        })

    return render(request, 'wagtailsurveys/index_submissions.html', {
        'survey_page': survey_page,
        'submissions': submissions,
        'data_headings': data_headings,
        'data_rows': data_rows
    })
