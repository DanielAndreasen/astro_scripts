#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division, print_function
import argparse
import os


def send_email(wavelength, step):
    """
    Prepare and send the email
    """
    line_interval = '%s, %s\n' % (wavelength - step, wavelength + step)
    request = request_header
    request += line_interval
    request += request_bottom

    cmd = 'thunderbird -compose "to=vald3@vald.astro.univie.ac.at,'
    cmd += 'subject=VALD-EMS request: ' + str(wavelength) + ','
    cmd += 'preselectid=id2,'
    cmd += 'body=\'$(cat tmp.mail)\'"'

    with open('tmp.mail', 'wb') as f:
        f.write(request)

    os.system(cmd)
    raw_input('\nPress RETURN to continue: ')
    os.remove('rm -f tmp.mail')


def VALDmail(wavelength=1000, step=1, wavelengths=None):
    """
    Create the mail to be send to VALD3 to extract all. This script make use of
    Thunderbird. Please have Thunderbird set up if you want to use this script
    with your email registered at VALD3.

    :wavelength: The center wavelength in Ångstrøm. (Default=1000Å).
    :step: The step (to each side) from the wavelength. Basically this make the
    window of the lines to extract. (Default=1Å).
    :wavelengths: If a list is give with multiple wavelengths multiple mails
    are begin prepared.
    """

    request_header = 'begin request\nextract all\nvia ftp\n'
    request_header += 'default configuration\nshort format\n'
    request_bottom = 'end request\n'

    if wavelengths:
        assert hasattr(wavelengths,
                       '__iter__'), '%s is not iterable' % wavelengths

        for wavelength in wavelengths:
            send_email(wavelength, step)
    else:
        send_email(wavelength, step)


def _parser():
    parser = argparse.ArgumentParser(description='Prepare emails with'
                                     'Thunderbird for VALD.')
    parser.add_argument('-w', '--wavelength',
                        help='The central wavelength(s)',
                        nargs='+',
                        type=float)
    parser.add_argument('-s', '--step',
                        default=1,
                        type=float,
                        help='The wavelength window, twice the size of the\
                              step.')
    return parser.parse_args()


def main():
    args = _parser()
    VALDmail(wavelength=args.wavelength, step=args.step)


if __name__ == '__main__':
    main()
