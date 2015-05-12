from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from optparse import make_option
from scheduler.models import Visit, Proposal, Beamline, Stat, get_shift_mode
import datetime
from datetime import datetime, date, timedelta
from django.conf import settings
from django.template import loader

class Command(BaseCommand):
    args = '<visit_id>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        self.visit = None
        self.mod_type = None
        self.mod_msg = None
        self.mod = False
        self.pr = False
        self.sendable = False
        if args:
            try:
                self.visit = Visit.objects.get(pk=args[0])
                self.mod_type = args[1]
                if len(args) > 2:
                    self.mod_msg = args[2]
            except:
                raise CommandError('Visit %s does not exist' % args[0])
        self.from_email = getattr(settings, 'FROM_EMAIL', "sender@no-reply.ca")
        self.url_root = getattr(settings, 'URL_ROOT', "")
        self.site_name = getattr(settings, 'SITE_NAME_SHORT', "")
        self.template_name = 'scheduler/email_body.txt'
        self.subject_template_name = "scheduler/email_subject.txt"
        if args:
            self.recipient_list = [mail_tuple[1] for mail_tuple in settings.AUTO_SCHEDULERS]
        else:
            self.recipient_list = [mail_tuple[1] for mail_tuple in settings.SCHEDULERS]
        
        this_monday = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
        this_day = datetime.now().date()
        self.run_start = None
        shift_choices = [s[0] for s in Stat.SHIFT_CHOICES]
        shift_choices.reverse()
        mshifts = 0
        while not self.run_start:
            for shift in shift_choices:
                if get_shift_mode(this_day, shift) in ['Maintenance','Shutdown']:
                    mshifts += 1
                else:
                    mshifts = 0
                if mshifts > 3:
                    self.run_start = this_day + timedelta(days=1)
            this_day = this_day - timedelta(days=1)
        self.data = {}
        printed = {}
        for bl in Beamline.objects.exclude(name__startswith='SIM'):
            self.data[bl.name] = [[],[]]
            printed[bl.name] = []
        visits = Visit.objects.filter(beamline__name__in=self.data.keys())
        
        for v in visits.filter(start_date__lte=this_monday).filter(start_date__gte=self.run_start).order_by('start_date'):
            prop = v.proposal and '%s, %s. %s' % (v.proposal.proposal_id, v.proposal.first_name[0].upper(), v.proposal.last_name) or None
            if prop and prop not in printed[v.beamline.name]:
                printed[v.beamline.name].append(prop)
        for v in visits.filter(start_date__gte=this_monday).filter(start_date__lte=this_monday+timedelta(days=7)).order_by('start_date'):
            if v.email_notify()[:7] not in [p[:7] for p in printed[v.beamline.name]]:
                if v.email_notify()[:7] not in [n[:7] for n in self.data[v.beamline.name][0]]:
                    self.data[v.beamline.name][0].append(v.email_notify())
            else:
                if v.email_notify()[:7] not in [n[:7] for n in self.data[v.beamline.name][1]]: 
                    self.data[v.beamline.name][1].append('%s, %s. %s' % (v.proposal.proposal_id, v.proposal.first_name[0].upper(), v.proposal.last_name))
            self.sendable = True
        if self.visit:
            self.pr = not visits.exclude(pk=self.visit.pk).filter(start_date__lte=self.visit.start_date).filter(start_date__gte=self.run_start).filter(beamline=self.visit.beamline).exists()
            if self.mod_msg:
                prop = '%s, %s. %s' % (self.visit.proposal.proposal_id, self.visit.proposal.first_name[0].upper(), self.visit.proposal.last_name)
                self.mod = [self.mod_type, prop, self.mod_msg]
        
        if self.sendable:   
            self.save()

    def message(self):
        """
        Render the body of the message to a string.
        
        """
        if callable(self.template_name):
            template_name = self.template_name()
        else:
            template_name = self.template_name
            
        
        return loader.render_to_string(template_name, dictionary={
                                            'print': self.pr,
                                            'data': self.data,
                                            'mod': self.mod,
                                            'run': self.run_start,
                                            'site': [self.url_root, self.site_name],
                                            })

    def subject(self):
        """
        Render the subject of the message to a string.
        
        """
        now = datetime.now().date()
        date = now - timedelta(days=now.weekday())
        subject = loader.render_to_string(self.subject_template_name, dictionary={
                                            'print': self.pr,
                                            'date': date,
                                            'visit': self.visit})
        return ''.join(subject.splitlines())


    def get_message_dict(self):
        """
        Generate the various parts of the message and return them in a
        dictionary, suitable for passing directly as keyword arguments
        to ``django.core.mail.send_mail()``.
    
        By default, the following values are returned:
        * ``from_email``
        * ``message``
        * ``recipient_list``
        * ``subject``
        
        """
        message_dict = {}
        for message_part in ('from_email', 'message', 'recipient_list', 'subject'):
            if message_part == 'recipient_list':
                attr = getattr(self, message_part)
            else:
                attr = getattr(self, message_part)
            message_dict[message_part] = callable(attr) and attr() or attr
        return message_dict
    
    def save(self, fail_silently=False):
        """
        Build and send the email message.
        
        """
        send_mail(fail_silently=fail_silently, **self.get_message_dict())








'''Put the following at the top of your cron.py file:

#!/usr/bin/python
import os, sys
sys.path.append('/path/to/') # the parent directory of the project
sys.path.append('/path/to/project') # these lines only needed if not on path
os.environ['DJANGO_SETTINGS_MODULE'] = 'myproj.settings'

# imports and code below
'''


'''
PROPS = Proposal.objects.all().values('proposal_id')
PROPOSALS = []
for p in PROPS:
    PROPOSALS.append(p['proposal_id'])
for prop in proposals:
    if prop[3] not in PROPOSALS:
        new_proposal = Proposal()
        new_proposal.description = prop[2]
        new_proposal.first_name = prop[1]
        new_proposal.last_name = prop[0]
        new_proposal.proposal_id = prop[3]
        if prop[7] is not 'SUBMITTED':
            new_proposal.expiration = datetime.strptime(str(prop[7]).replace(' ',''), '%Y-%m-%d')
        new_proposal.save()
'''
proposals = [["Grigg","Jason","Iron uptake in Staphylococcus aureus","11-2354","2012-06-30"],
["Anzar","Muhammad","Detection of ice crystallization in vitrified bovine oocytes","11-2403","2012-06-30"],
["Moore","Stanley","Structural Studies of Chromosomal and Flagellar Proteins","11-2406","2012-06-30"],
["Leung","Charles","Glover - Structural studies of proteins in DNA damage response","11-2427","2012-06-30"],
["Merrill","Allan","Molecular Mechanism of Bacterial Virulence Factors in the Mono-ADP-ribosyltransferase Family","11-2430","2012-06-30"],
["Pai","Emil","Various conformational states of the bacterial magnesium channel CorA","11-2432","2012-06-30"],
["Saridakis","Vivian","Structural Studies of Ubiquitin Specific Protease 7 and other USP/UBPs","11-2444","2012-06-30"],
["Lemieux","Joanne","Structural studies of membrane proteins in disease","11-2595","2012-06-30"],
["Mark","Brian","Structural investigations of viral host immune evasion mechanisms and bacterial antibiotic resistance","11-2625","2012-06-30"],
["Campbell","Stephen","Structural studies of proteins involved in the DNA damage response","11-2688","2012-06-30"],
["Cygler","Miroslaw (Mirek)","Structural studies of microbial protein-protein complexes","11-2708","2012-06-30"],
["Strynadka","Natalie","Structural studies of the bacterial secretion systems","11-2709","2012-06-30"],
["Luo","Yu","Crystallographic studies on RecA-like recombinases and proteins involved in bacterial teichoic acid synthesis","11-2739","2012-06-30"],
["Baral","Pravas Kumar","Structural studies of therapeutic antibodies for prion diseases","11-2821","2012-06-30"],
["Sanders","David","Crystallographic studies of unusual sugar modifying enzymes","11-2858","2012-06-30"],
["Prasad","Lata","Structure-Function Relationships in Biologically Important Enzymes.","11-2860","2012-06-30"],
["Paetzel","Mark","Crystallographic analysis of protease inhibitor complexes.","11-2865","2012-06-30"],
["Shilton","Brian","Mechanical Coupling in ATP Hydrolyzing Systems and Structure of a Novel 'Split' Ribonucleotide Reductase","11-2866","2012-06-30"],
["Tempel","Wolfram","Structure determination of health-related proteins","11-2867","2012-06-30"],
["Kimber","Matthew","Substrate/product co-complexes of a novel dehydratase family","11-2868","2012-06-30"],
["Van Petegem","Filip","Structure-function of calcium channels and associated proteins","11-2870","2012-06-30"],
["Chang","Geoffrey","Structures of Transmembrane Mutidrug Transporters","11-2871","2012-06-30"],
["Sygusch","Jurgen","Crystallographic structure determination of aldolases, ssDNA binding proteins, and bacterial virulence factors","12-2921","2012-12-31"],
["Miller","Gregory","Structure Determination Inositol Phosphate Kinases","12-2928","2012-12-31"],
["Fraser","Marie","Catalytic Mechanism and Biological Roles of Succinyl-CoA Synthetase and Related Enzymes","12-2936","2012-12-31"],
["Grochulski","Pawel","Structural Insights in the Secretion Pathway of Aeromonas hydrophila","12-3009","2012-06-30"],
["Cicmil","Nenad","Structural studies of Shiga like toxin 1 complexed with its peptide inhibitor","12-3339","2012-06-30"],
["Grochulski","Pawel","Structural studies of selected proteins","12-3350","2012-06-30"],
["Berghuis","Albert","Structural Studies of Antibiotic Resistance Enzymes","12-3352","2012-06-30"],
["Kozlov","Guennadi","Structural studies of sacsin, a protein involved in neurodegenerative disorder","12-3380","2012-06-30"],
["Loewen","Michele","The Crystal Structure of Pea Rubisco Bound to a Novel Inhibitor","12-3383","2012-06-30"],
["Orriss","George","Structural analysis of Tocopherol Cyclase a key enzyme in vitamin E biosynthesis","12-3409","2012-06-30"],
["Moraes","Trevor","Structural Investigation of protein and Ion translocation machineries","13-2357","2012-12-31"],
["Nagar","Bhushan","Structural analysis of protein-nucleic acid interactions in RNA silencing","13-3027","2012-12-31"],
["Burtnick","Leslie","Crystallographic structures of gelsolin family members","13-3059","2012-12-31"],
["Boraston","Alisdair","Structural analysis of virulence factors from prokaryotic and eukaryotic human pathogens","13-3067","2012-12-31"],
["Audette","Gerald","Crystallographic Studies of Transfer Proteins from the F Plasmid of E. coli","13-3111","2012-12-31"],
["Gaudin","Catherine","Heme Uptake by the Staphylococcus aureus Isd System","13-3114","2012-12-31"],
["Cygler","Miroslaw (Mirek)","Structural studies of microbial protein-protein complexes","13-3115","2012-12-31"],
["Howell","Lynne","Bacterial Biofilm development","13-3141","2012-12-31"],
["Cicmil","Nenad","Structural Studies of Tumor Necrosis Factor alpha complexed with its DNA inhibitor","13-3184","2012-12-31"],
["Kimber","Matthew","The structure of the beta carboxysome, and functionally related proteins","13-3218","2012-12-31"],
["Mosimann","Steven","Structure and Function of Novel myo-Inositol Polyphosphatases","13-3224","2012-12-31"],
["Rini","James","Viral Glycoproteins, Cell Surface Receptors and Glycosyltransferases","13-3235","2012-12-31"],
["Houry","Walid","Structural studies on the lysine decarboxylase system involved in the bacterial acid stress response","13-3238","2012-12-31"],
["Ng","Kenneth","Molecular Structural Studies of Proteins Involved with Viral and Bacterial Diseases","13-3243","2012-12-31"],
["Campbell","Stephen","Structural studies of proteins involved in the DNA damage response.","13-3273","2012-12-31"],
["Paetzel","Mark","Crystallographic analysis of protease inhibitor complexes.","13-3303","2012-12-31"],
["Bertwistle","Drew","Crystallographic Studies of the Active Site of Myo-Inositol Dehydrogenase","13-3438","2012-12-31"],
["Grochulski","Pawel","Determination of crystal structures of small molecules","13-3496","2012-12-31"],
["Zhou","Ming","Complex structures of human 17beta-HSDs/ligands and rat rLcn6/ligands","13-3499","2012-12-31"],
["Van Petegem","Filip","Regulation of cardiac calcium and sodium channels","13-3758","2012-12-31"],
["Fodje","Michel","CMCF 08B1-1 Maintenance, Upgrades &amp; Commissioning","13-3762","2012-12-31"],
["Lin","Sheng-xiang","Structural study of human HCMV DNA Polymerase","13-3803","2012-12-31"],
["Berghuis","Albert","Structural Studies of Antibiotic Resistance Enzymes","14-3443","2013-06-30"],
["Wilson","Ian","Structural studies of immune-related complexes","14-3454","2013-06-30"],
["Loewen","Peter","Structure and function in protection against reactive oxygen species.","14-3476","2013-06-30"],
["Stetefeld","Joerg","Structural analysis of Tocopherol Cyclase","14-3544","2013-06-30"],
["Evans","Stephen","Anti-LPS Broadly Neutralizing Antibodies for Septic Shock Research","14-3588","2013-06-30"],
["Stetefeld","Joerg","Structural studies of netrin-1","14-3620","2013-06-30"],
["Bie","Haiying","Crystal structure determination and inhibitor studies of Acyl-CoA carboxylases from mycobacterium tuberculosis","14-3871","2013-06-30"],
["Labiuk","Shaunivan","Detection of crystallinity and characterization of a Tacrolimus immune suppresant drug suspension","14-3877","2013-06-30"],
["Chiovitti","David","Structure / Function analysis of Eukaryotic Protein Kinases and Phospho-Regulatory Systems","14-4201","2013-06-30"],
["Luo","Yu","Bioc843 Graduate student training at macromolecular crystallography beamline","14-4208","2013-06-30"],
["Gorin","James","Maintenance, upgrade and devlopment access of the CMCF-ID beamline.","14-4264","2013-06-30"],
["Gorin","James","Contract #5073.011","14-4266","2012-06-30"],
["Labiuk","Shaunivan","Contract # 5146","14-4275","2012-06-30"],
["Labiuk","Shaunivan","Contract # 5144-001","14-4278","2012-06-30"],
["Mao","Daniel","Structure / Function analysis of Eukaryotic Protein Kinases and Phospho-Regulatory Systems","14-4280","2013-06-30"],
["Aller","Stephen","Macromolecular crystallography of membrane proteins for atomic resolution studies","14-4281","2013-06-30"],
["Lin","Sheng-xiang","Structure-Function Study of Human 17beta-Hydroxysteroid Dehydrogenase type 7, Its Complex Forms and Other Enzymes","15-3920","2013-12-31"],
["Serpell","Christopher","Crystallography of Functional Synthetic DNA Nanostructures","15-3934","2013-12-31"],
["Jia","Zongchao","Structural studies of Etk, a membrane protein involved in regulating capsular polysaccharide transport","15-4073","2013-12-31"],
["Ritchie","Dustin","MacMillan-Structural Investigation of the Essential Spliceosomal Proteins p14 and p220 (PRP8)","15-4136","2013-12-31"]]

