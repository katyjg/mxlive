from django.http import JsonResponse
from django.views import View

from mxlive.publications.models import Publication, Deposition

from .models import WithChoices
from .sources import DataField, Aggregation, Annotation, DataSource, Table
from django.db.models import Count, F, Sum, Avg
from django.db.models.functions import Round


class PublicationReport(DataSource):
    model = Publication
    fields = [
        #DataField(name="type", source=Annotation("type", WithChoices(Publication, 'kind')), label="Type"),
        DataField(name='citations', source=Aggregation("citations", Sum("metrics__citations")), label='Citations'),
        DataField(name='mentions', source=Aggregation("mentions", Sum("metrics__mentions")), label='Media Mentions¹'),
        DataField(name="year", source=Annotation("year", F("published__year")), label='Year'),
        DataField(name="publications", source=Aggregation("publications", Count("id")), label="Publications"),
        DataField(name="journals", source=Aggregation("journals", Count("journal__id")), label="Journals"),
        DataField(
            name="impact_factor",
            source=Aggregation("impact_factor", Round(Avg("journal__metrics__impact_factor", default=0.0), 1)),
            label="Average Impact Factor²"
        ),
        DataField(
            name="sjr",
            source=Aggregation("sjr", Round(Avg("journal__metrics__sjr_rank", default=0.0), 1)),
            label="Average SJR³"
        ),
        DataField(
            name="quartile",
            source=Aggregation("quartile", Round(Avg("journal__metrics__sjr_quartile", default=0.0), 1)),
            label="Average SJR³ Quartile"
        ),
        DataField(
            name="h_index",
            source=Aggregation("h_index", Round(Avg("journal__metrics__h_index", default=0.0), 1)),
            label="Average H-Index"
        ),
        DataField(
            name="cites_per_pub",
            source=Aggregation("cites_per_pub", Round(Avg("metrics__citations"), 1)),
            label="Citations/Article"
        ),
        DataField(
            name="mentions_per_pub",
            source=Aggregation("mentions_per_pub", Round(Avg("metrics__mentions"), 1)),
            label="Mentions/Article"
        ),
    ]
    group_by = ["year"]


class DepositionReport(DataSource):
    model = Deposition
    fields = [
        DataField(name="year", source=Annotation("year", F("released__year")), label="Year"),
        DataField(name="depositions", source=Aggregation("depositions", Count("id")), label="Depositions"),
        DataField(
            name="pdb_res",
            source=Aggregation("pdb_res", Round(Avg("resolution", default=0), 1)),
            label="Average PDB Resolution"
        )
    ]
    group_by = ["year"]


class ReportView(View):
    title = 'Publication Metrics',
    description = 'Summary of publication and PDB deposition statistics'
    style = 'row'
    notes = []

    blocks = [
        Table(
            source=PublicationReport,
            itle='Metrics Summary',
            rows=[
                'publications', 'citations', 'cites_per_pub', 'mentions', 'mentions_per_pub', 'journals',
                'impact_factor', 'sjr', 'quartile', 'h_index'
            ],
            columns='year', values='publications',
            labels=PublicationReport.get_labels(),
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
        Table(
            source=DepositionReport,
            rows=['depositions', 'pdb_res'],
            columns='year', values='depositions',
            labels=DepositionReport.get_labels()
        )
    ]

    def get_report(self, *args, **kwargs):
        return {
            'title': self.title,
            'description': self.description,
            'style': self.style,
            'content': [block.generate(*args, **kwargs) for block in self.blocks],
            'notes': '\n'.join(self.notes)
        }

    def get(self, request):
        report = self.get_report()
        return JsonResponse({'details': [report]}, safe=False)
