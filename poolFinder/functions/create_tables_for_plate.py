from poolFinder.models import PlateSummary
from poolFinder.functions.app_functions import round_fixed
import pandas as pd


def _create_plate_info_table(plate):
    plate_summary = PlateSummary.objects.filter(plate=plate.array_code).all()

    if plate.pool == 'None':
        positives = [plate_summary[0].positives]
        plods = [plate_summary[0].plods]
    else:
        if plate_summary[0].total_samples:
            positives = [str(plate_summary[0].positives) + ' (' + str(round_fixed(plate_summary[0].positives / plate_summary[0].total_samples * 100, 2)) + '%)', '']
            plods = [str(plate_summary[0].plods) + ' (' + str(round_fixed(plate_summary[0].plods / plate_summary[0].total_samples * 100, 2)) + '%', '']
            plods[0] += f', {plate.high_plods} high)'
        else:
            positives = [0, '']
            plods = [0, '']

    if not plate.pool == 'None':
        negatives = [plate_summary[0].negatives, '']
        vic_fails = [plate_summary[0].vic_fails, '']
        total_samples = [plate_summary[0].total_samples, '']
        inact_plate = ['', '']
        nexar_or_dwp_ham = [plate_summary[0].nexar_or_dwp_ham, '']
        araya_or_elute = [plate_summary[0].araya_or_elute, '']
        hydrocycler_or_kf = [plate_summary[0].hydrocycler_or_kf, '']
        df_or_384_ham = [plate_summary[0].df_or_384_ham, '']

        for row in plate_summary[1:]:
            if row.total_samples:
                positives.append(str(row.positives) + ' (' + str(round_fixed(row.positives / row.total_samples * 100, 2)) + '%)')
            else:
                positives.append(0)
            plods.append(row.plods)
            negatives.append(row.negatives)
            vic_fails.append(row.vic_fails)
            total_samples.append(row.total_samples)
            inact_plate.append(row.inact_plate)
            nexar_or_dwp_ham.append(row.nexar_or_dwp_ham)
            araya_or_elute.append(row.araya_or_elute)
            hydrocycler_or_kf.append(row.hydrocycler_or_kf)
            df_or_384_ham.append(row.df_or_384_ham)

        plate_info = {
            plate.array_code : (plate.pool, '', 'Q1', 'Q2', 'Q3', 'Q4'),
            'Positives' : positives,
            'PLODs' : plods,
            'Negatives' : negatives,
            'VIC Failures' : vic_fails,
            'Total Samples' : total_samples,
            '' : ['', '', '', '', '', ''],
            'Instrument info' : inact_plate,
            'Nexar' : nexar_or_dwp_ham,
            'Araya' : araya_or_elute,
            'Hydrocycler' : hydrocycler_or_kf,
            '384 Hamilton' : df_or_384_ham
            }
    else:
        plate_info = {
            '384' : [plate.array_code],
            'Positives' : positives[0],
            'PLODs' : plods[0],
            'Total Samples' : [0],
            '' : [''],
            'Araya' : [plate.araya],
            }
            
    plate_info = pd.DataFrame(plate_info).to_html(index=False)

    return plate_info


def _create_plate_roxbox(plate):
    mean_rox = plate.average_rox
    sd = plate.rox_sd
    cv = str(round_fixed(sd / mean_rox * 100, 2)) + '%'
    mean_rox = str(mean_rox) + ' (RFU)'
    rox_below_threshold = str(plate.total_rox_below_threshold) + ' (' + str(plate.patient_rox_below_threshold) + ' patient)'
    rox_above_threshold = plate.rox_above_threshold

    roxbox = {
        'Average ROX' : [mean_rox],
        'Standard Deviation' : [sd],
        'CV' : [cv],
        f'ROX < {plate.thresholds["LOW_ROX"]}' : [rox_below_threshold],
        f'ROX >= {plate.thresholds["HIGH_ROX"]}' : [rox_above_threshold]
    }
    return pd.DataFrame(roxbox).to_html(index=False)


def create_plate_tables(plate):
    plate.plate_info = _create_plate_info_table(plate)
    plate.roxbox = _create_plate_roxbox(plate)

    return plate
