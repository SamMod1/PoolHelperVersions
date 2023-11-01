from django.test import TestCase
from BackgroundTasks.PlateAnalysis.classes.sample import Sample


class TestSample(TestCase):
    def test_sample_str(self):
        samp = Sample(10,2,1)
        self.assertTrue(str(samp) == '10.0')

    def test_sample_all_data(self):
        samp = Sample(1,1,1)
        self.assertTrue(samp.all_data() == {'FAM' : 1, 'VIC' : 1, 'ROX' : 1, 'nFAM' : 1.0, 'nVIC' : 1.0, 'barcode' : ''})

    def test_sample_set_barcode(self):
        samp = Sample(1,1,1)
        samp.set_barcode('AAA')
        self.assertTrue(samp.barcode == 'AAA')
