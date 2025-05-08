from django.conf import settings
from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel
from mxlive.lims.models import Beamline, Container, Dewar, ContainerLocation, LoadHistory

SELECT_DURATION = getattr(settings, 'LOADER_SELECT_DURATION', 5 * 60)  # Default to 5 minutes


class Config(TimeStampedModel):
    beamline = models.ForeignKey(Beamline, on_delete=models.CASCADE)
    automounter = models.ForeignKey(Container, on_delete=models.CASCADE)
    selected = models.ForeignKey(Container, related_name='selected', on_delete=models.SET_NULL, null=True)
    updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.automounter.kind}"

    def select(self, puck):
        self.selected = puck
        self.updated = timezone.now()
        self.save()

    def check_timeout(self) -> bool:
        elapsed = timezone.now() - self.modified
        if self.selected and elapsed.total_seconds() > SELECT_DURATION:
            self.select(None)
            return True
        return False

    def get_location(self, position: str) -> ContainerLocation:
        location = self.automounter.kind.locations.filter(name=position).first()
        return location

    def get_container(self, position: str):
        return self.automounter.children.filter(location__name=position).first()

    def load(self, position: str) -> Container:
        puck = self.selected
        self.select(None)
        location = self.get_location(position)
        existing = self.automounter.children.filter(location=location).first()
        if existing:
            LoadHistory.objects.filter(child=existing).active().update(end=timezone.now())
            Container.objects.filter(pk=existing.pk).update(parent=None, location=None)

        LoadHistory.objects.create(child=puck, parent=self.automounter, location=location)
        Container.objects.filter(pk=puck.pk).update(parent=self.automounter, location=location)
        return puck

    def unload(self, puck: Container):
        self.check_timeout()
        self.select(puck)
        LoadHistory.objects.filter(child=puck).active().update(end=timezone.now())
        Container.objects.filter(pk=puck.pk).update(parent=None, location=None)


