from django.db import models
from model_utils.models import TimeStampedModel
from mxlive.lims.models import Beamline, Container, Dewar


class Config(TimeStampedModel):
    beamline = models.ForeignKey(Beamline, on_delete=models.CASCADE)
    automounter = models.ForeignKey(Container, on_delete=models.CASCADE)
    selected = models.ForeignKey(Container, related_name='selected', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.beamline.acronym} - {self.created}"
