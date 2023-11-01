class SpoofBytesIO:
    def read(self):
        return 'test'
    def readlines(self):
        barray = []
        with open('poolFinder//unit_test_resources//test_data//test-araya_bytes.txt', 'r') as file:
            array = file.read().split('\\n')
        for x in array:
            barray.append(x.encode().replace(b'\\n', b'\n').replace(b'\\r', b'\r'))
        return barray

    
class CallableGenerator:
    """
    Instances of this class will be callable. Each time they are called they will return the next item in the generator which was
    supplied on initialisation
    """
    def __init__(self, generator_to_call = None):
        self.generator = generator_to_call

    def set_new_generator(self, new_generator_iterable):
        self.generator = (x for x in new_generator_iterable)
    
    def __call__(self, a=None, *args):
        return next(self.generator)
    

class MockFileUpload:
    def __init__(self, filename):
        self.name = filename
        self.file = SpoofBytesIO()