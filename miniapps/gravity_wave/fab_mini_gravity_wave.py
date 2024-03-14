#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''A FAB build script for miniapps/gravity_wave. It relies on the FabBase class
contained in the infrastructure directory.
'''

import logging
import sys

from fab.steps.grab.folder import grab_folder

# Until we sort out the build environment, add the directory that stores the
# base class of our FAB builds:
sys.path.insert(0, "../../infrastructure/build/fab")

from fab_base import FabBase
from grab_lfric import gpl_utils_source_config


class FabMiniGravityWave(FabBase):

    def __init__(self, name="gravity_wave", root_symbol=None):
        super().__init__(name, gpl_utils_source_config,
                         root_symbol=root_symbol)

        self.set_preprocessor_flags(
            ['-DRDEF_PRECISION=64', '-DR_SOLVER_PRECISION=64',
             '-DR_TRAN_PRECISION=64', '-DUSE_XIOS'])

        self.set_compiler_flags(
            ['-ffree-line-length-none', '-fopenmp', '-g', '-std=f2008',
             '-Wall', '-Werror=conversion', '-Werror=unused-variable',
             '-Werror=character-truncation', '-Werror=unused-value',
             '-Werror=tabs',
             # The lib directory contains mpi.mod
             '-I', ('/home/joerg/work/spack/var/spack/environments/lfric-v0/'
                    '.spack-env/view/lib'),
             # mod_wait.mod
             '-I', ('/home/joerg/work/spack/var/spack/environments/lfric-v0/'
                    '.spack-env/view/include')])

        self.set_link_flags(
            ['-fopenmp',
             '-L', ('/home/joerg/work/spack/var/spack/environments/lfric-v0/'
                    '.spack-env/view/lib'),
             '-lyaxt', '-lyaxt_c', '-lxios', '-lnetcdff', '-lnetcdf',
             '-lhdf5', '-lstdc++'])

    def grab_files(self):
        dirs = ['infrastructure/source/', 'components/driver/source/',
                'components/inventory/source/', 'components/science/source/',
                'components/lfric-xios/source/',
                'miniapps/gravity_wave/source/', 'gungho/source/']

        # pylint: disable=redefined-builtin
        for dir in dirs:
            grab_folder(self.config, src=self.lfric_root / dir, dst_label='')

    def get_rose_meta(self):
        return (self.lfric_root / 'miniapps/gravity_wave' / 'rose-meta' /
                'lfric-gravity_wave' / 'HEAD' / 'rose-meta.conf')

    def get_transformation_script(self):
        ''':returns: the transformation script to be used by PSyclone.
        :rtype: Path
        '''
        return ""


# -----------------------------------------------------------------------------
if __name__ == '__main__':

    logger = logging.getLogger('fab')
    logger.setLevel(logging.DEBUG)
    fab_mini_gravity_wave = FabMiniGravityWave()
    fab_mini_gravity_wave.build()