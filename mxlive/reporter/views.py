from django.http import JsonResponse, Http404
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView

from . import models
from .sources import DataField, Aggregation, Annotation, DataSource
from .components import Table, Bars, XYPlot, List
from django.db.models import Count, F, Sum, Avg, Value
from django.db.models.functions import Round


class ReportView(DetailView):
    template_name = 'reporter/report.html'
    model = models.Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report'] = self.object
        context['data_url'] = reverse('report-data', kwargs={'slug': self.object.slug})
        return context


class ReportData(View):
    @staticmethod
    def get_report(*args, slug='', **kwargs):

        report = models.Report.objects.filter(slug=slug).first()
        if not report:
            raise Http404('Report not found')

        return {
            'title': report.title,
            'description': report.description,
            'style': report.style,
            'content': [block.generate(*args, **kwargs) for block in report.entries.order_by('order')],
            'notes': report.notes
        }

    def get(self, request, *args, **kwargs):
        info = self.get_report(*args, **kwargs)
        return JsonResponse({'details': [info]}, safe=False)


class PublicationReport(DataSource):
    model = "publications.Publication"
    fields = [
        DataField(name='citations', source=Aggregation(Sum("metrics__citations")), label='Citations'),
        DataField(name='mentions', source=Aggregation(Sum("metrics__mentions")), label='Media Mentions¹'),
        DataField(name="year", source=Annotation(F("published__year")), label='Year'),
        DataField(name="publications", source=Aggregation(Count("id")), label="Publications"),
        DataField(name="journals", source=Aggregation(Count("journal__id")), label="Journals"),
        DataField(
            name="impact_factor",
            source=Aggregation(Round(Avg("journal__metrics__impact_factor", default=0.0), 1)),
            label="Impact Factor²"
        ),
        DataField(
            name="sjr",
            source=Aggregation(Round(Avg("journal__metrics__sjr_rank", default=0.0), 1)),
            label="SJR³"
        ),
        DataField(
            name="quartile",
            source=Aggregation(Round(Avg("journal__metrics__sjr_quartile", default=0.0), 1)),
            label="SJR³ Quartile"
        ),
        DataField(
            name="h_index",
            source=Aggregation(Round(Avg("journal__metrics__h_index", default=0.0), 1)),
            label="H-Index"
        ),
        DataField(
            name="cites_per_pub",
            source=Aggregation(Round(Avg("metrics__citations"), 1)),
            label="Citations/Article"
        ),
        DataField(
            name="mentions_per_pub",
            source=Aggregation(Round(Avg("metrics__mentions"), 1)),
            label="Mentions/Article"
        ),
    ]
    group_by = ["year"]


class TopTenCited(DataSource):
    model = "publications.Publication"
    fields = [
        DataField(name="article", source=Annotation(F('citation')), label="Article"),
        DataField(name="cites", label="Citations"),
    ]
    order_by = ["-cites"]
    limit = 10


class TopTenMentioned(DataSource):
    model = "publications.Publication"
    fields = [
        DataField(name="article", source=Annotation(F('citation')), label="Article"),
        DataField(name="mentions", label="Mentions"),
    ]
    order_by = ["-mentions"]
    limit = 10


class PDBReleases(DataSource):
    model = "publications.Deposition"
    fields = [
        DataField(name="year", source=Annotation(F("released__year")), label="Year"),
        DataField(name="depositions", source=Aggregation(Count("id")), label="PDB Releases"),
        DataField(
            name="pdb_res",
            source=Aggregation(Round(Avg("resolution", default=0), Value(1))),
            label="Avg Resolution"
        )
    ]
    group_by = ["year"]


class PDBData(DataSource):
    model = "publications.Deposition"
    fields = [
        DataField(name="year", source=Annotation(F("collected__year")), label="Year"),
        DataField(name="collections", source=Aggregation(Count("id")), label="PDB Collection"),
    ]
    group_by = ["year"]


class ReportViews(View):
    title = 'Publication Metrics',
    description = 'Summary of publication and PDB deposition statistics'
    style = 'row'
    notes = []

    content = [
        Table(
            sources=(PublicationReport, PDBReleases),
            title='Metrics Summary',
            rows=[
                'publications', 'depositions', 'pdb_res', 'citations', 'cites_per_pub', 'mentions', 'mentions_per_pub', 'journals',
                'impact_factor', 'sjr', 'quartile', 'h_index'
            ],
            columns='year', values='publications',
            notes=[
                "1. Mentions represent the number of news stories, and social media mentions the reference the publication.",
                "2. The Average Impact Factor is the ratio of citations to the number of citable documents for the journal "
                "over the previous two years. This value is calculated based on citations in the SCOPUS database and may be "
                "different from the Web Of Science values from the Thomson Reuters database",
                "3. SCIMAGO Quartile https://www.scimagojr.com/. A Journal with an SJR quartile of 1 is in the top 25% of "
                "journals in the field when ranked by SJR, and a quartile of 2 is ranked higher than 50% but lower than 25% "
                "of journals in the field."
            ]
        ),
        Bars(
            sources=(PublicationReport, PDBReleases),
            title='Research Output',
            x_axis='year', y_axis=['publications', 'depositions'],
            wrap_x_labels=False, x_culling=15,
            style='col-md-6 col-12'
        ),
        XYPlot(
            sources=(PDBReleases, PDBData),
            title='Data Collection vs PDB Release', scatter=False,
            y1_label='Entries', tick_precision=0,
            x_axis='year', y_axis=[['collections', 'depositions']],
            style='col-md-6 col-12'
        ),
        List(
            sources=(TopTenCited,),
            title='Top Ten Most Cited Articles',
            columns=['article', 'cites'],
            style='col-12 first-col-left'
        ),
        List(
            sources=(TopTenMentioned,),
            title='Top Ten Most Mentioned Articles',
            columns=['article', 'mentions'],
            style='col-12 first-col-left'
        ),
    ]

    def get_report(self, *args, **kwargs):
        r = models.Report.objects.get(pk=1)
        return {
            'title': self.title,
            'description': self.description,
            'style': self.style,
            'content': [block.generate(*args, **kwargs) for block in r.entries.all()],
            'notes': '\n'.join(self.notes)
        }

    def get(self, request):
        report = self.get_report()
        return JsonResponse({'details': [report]}, safe=False)
