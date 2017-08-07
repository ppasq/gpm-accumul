import glob
import os
import datetime

from gpm_repo import gpm_wrapper
from gpm_repo.credentials import DATADIR
from gpm_repo.gpm_ftp import GPMFTP
from gpm_repo.gpm_wrapper import GPM_FFORMAT
from gpm_repo.time_serie import PrecipTimeSerie


UPDATE_FILE = 'update.txt'
UPDATE_ABSPATH = os.path.join(DATADIR, UPDATE_FILE)
DATETIME_FORMAT = '%Y-%m-%dT%H:%M%z'


def mirror_gpm_site():
    # since the maximum cumulate is 144h, we need 288 files to build it
    n_gpm_files = 28
    # n_gpm_files = 288
    with GPMFTP() as ftp:
        ftp.grab_latest_nfiles(n_gpm_files, DATADIR)
    # delete old files
    gpm_filelist = glob.glob(os.path.join(DATADIR, GPM_FFORMAT))
    if len(gpm_filelist) > n_gpm_files:
        for gpm_file in gpm_filelist[: -n_gpm_files]:
            try:
                os.remove(gpm_file)
            except OSError:
                print('Cannot remove old gpm file: ' + gpm_file)


def compare_dates():
    try:
        with open(UPDATE_ABSPATH, 'r') as update_file:
            update_file.readline()
            datetime_str = update_file.readline()
        erds_update = datetime.datetime.strptime(datetime_str, DATETIME_FORMAT)
    except FileNotFoundError:
        erds_update = datetime.datetime.min
    print('ERDS latest update is on: ', erds_update.isoformat())

    gpm_filelist = glob.glob(os.path.join(DATADIR, GPM_FFORMAT))
    latest_gpm_obj = gpm_wrapper.GPMImergeWrapper(gpm_filelist[-1])
    gpmfiles_update = latest_gpm_obj.end_dt
    print('GPM latest file ends on: ', gpmfiles_update.isoformat())

    delta = gpmfiles_update - erds_update
    if delta.total_seconds() > 120:
        print('ERDS is not up-to-date with the GPM data')
        is_up_to_date = False
    else:
        print('ERDS is up-to-date with the GPM data available')
        is_up_to_date = True
    return is_up_to_date


def compare_precip():
    pass


def cumulate():
    TIFF_FFORMAT = 'precip_{:03d}.tif'

    duration = datetime.timedelta(hours=12)
    serie_012h = PrecipTimeSerie.latest(duration, DATADIR)

    tif_abspath = os.path.join(DATADIR, TIFF_FFORMAT.format(12))
    serie_012h.save_accumul(tif_abspath)

    if serie_012h.measurements:
        with open(UPDATE_ABSPATH, 'w') as update_file:
            update_file.write('latest measure ended at:\n')
            update_file.write(
                serie_012h.measurements[-1].end_dt.strftime(DATETIME_FORMAT))


def generate_alerts():
    cumulate()
    compare_precip()


def start():
    mirror_gpm_site()
    is_up_to_date = compare_dates()
    if not is_up_to_date:
        print('Updating ERDS...')
        generate_alerts()


if __name__ == '__main__':
    start()
