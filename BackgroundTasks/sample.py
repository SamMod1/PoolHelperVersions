import numpy as np


class Sample:
    """
    Stores data for an individual sample
    __init__(fam : int, vic : int, rox : int, barcode = '')
    
    Attributes
    ---------
    fam : int
        the FAM value
    vic : int
        the VIC value
    rox : int 
        the ROX value
    barcode : str
        the sample's barcode
    
    Methods
    -------
    all_data()
        returns data as a dictionary
    set_barcode(barcode)
        sets the sample barcode
    """
    def __init__(self, fam : int, vic : int, rox : int, barcode = ''):
        self.fam = fam
        self.vic = vic
        self.rox = rox
        if self.rox != 0:
            self.nfam = self.fam / self.rox
            self.nvic = self.vic / self.rox
        else:
            self.nfam = np.nan
            self.nvic = np.nan
        self.barcode = barcode

    def __str__(self):
        return str(self.nfam)
        
    def all_data(self) -> dict:
        """Returns the sample data as a dictionary"""
        return {'FAM': self.fam, 'VIC': self.vic, 'ROX': self.rox, 'nFAM': self.nfam, 'nVIC': self.nvic, 'barcode': self.barcode}
    
    def set_barcode(self, barcode : str):
        """Sets the sample barcode"""
        self.barcode = barcode
        