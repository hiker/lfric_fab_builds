#!/usr/bin/env python3
# ##############################################################################
#  (c) Crown copyright Met Office. All rights reserved.
#  For further details please refer to the file COPYRIGHT
#  which you should have received as part of this distribution
# ##############################################################################

'''This is an OO basic interface to FAB. It allows the typical LFRic
applications to only modify very few settings to have a working FAB build
script.
'''

import logging
from pathlib import Path

from fab.build_config import BuildConfig
from fab.steps.analyse import analyse
from fab.steps.archive_objects import archive_objects
from fab.steps.compile_fortran import compile_fortran
from fab.steps.find_source_files import find_source_files, Exclude
from fab.steps.link import link_exe
from fab.steps.preprocess import preprocess_fortran
from fab.steps.psyclone import psyclone, preprocess_x90

from lfric_common import configurator, fparser_workaround_stop_concatenation


logger = logging.getLogger('fab')
logger.setLevel(logging.DEBUG)


class FabBase:
    '''This is the base class for all LFRic FAB scripts.

    :param str name: the name to be used for the workspace. Note that
        the name of the compiler will be added to it.
    :param gpl_utils_config: a BuildConfig object which contains the
        path to LFRic's gpl_utils, from which rose-picker is used.
    :param Optional[str] root_symbol:
    '''

    def __init__(self, name, gpl_utils_config, root_symbol=None):
        this_file = Path(__file__)
        # The root directory of the LFRic installation
        self._lfric_root = this_file.parents[3]
        if root_symbol:
            self._root_symbol = root_symbol
        else:
            self._root_symbol = name
        self._gpl_utils_source = gpl_utils_config.source_root / 'gpl_utils'
        self._config = BuildConfig(
            project_label=f'{name}-$compiler', verbose=True)
        self._preprocessor_flags = []
        self._compiler_flags = []
        self._link_flags = []

    @property
    def config(self):
        ''':returns: the FAB BuildConfig instance.
        :rtype: :py:class:`fab.BuildConfig`
        '''
        return self._config

    @property
    def lfric_root(self):
        return self._lfric_root

    @property
    def gpl_utils_source(self):
        return self._gpl_utils_source

    def set_preprocessor_flags(self, list_of_flags):
        self._preprocessor_flags = list_of_flags

    def set_compiler_flags(self, list_of_flags):
        self._compiler_flags = list_of_flags

    def set_link_flags(self, list_of_flags):
        self._link_flags = list_of_flags

    def grab_files(self):
        pass

    def find_source_files(self):
        find_source_files(self.config,
                          path_filters=[Exclude('unit-test', '/test/')])

    def get_rose_meta(self):
        return ""

    def configurator(self):
        rose_meta = self.get_rose_meta()
        if rose_meta:
            configurator(self.config, lfric_source=self.lfric_root,
                         gpl_utils_source=self.gpl_utils_source,
                         rose_meta_conf=rose_meta)

    def preprocess_fortran(self):
        preprocess_fortran(self.config, common_flags=self._preprocessor_flags)

    def preprocess_x90(self):
        preprocess_x90(self.config, common_flags=self._preprocessor_flags)

    def get_transformation_script(self):
        return ""

    def psyclone(self):
        psyclone(self.config, kernel_roots=[self.config.build_output],
                 transformation_script=self.get_transformation_script(),
                 cli_args=[])

    def analyse(self):
        analyse(self.config, root_symbol=self._root_symbol,
                ignore_mod_deps=['netcdf', 'MPI', 'yaxt', 'pfunit_mod',
                                 'xios', 'mod_wait'])

    def compile_fortran(self):
        compile_fortran(self.config,
                        common_flags=["-c"]+self._compiler_flags)

    def archive_objects(self):
        archive_objects(self.config)

    def link(self):
        link_exe(self.config, linker='mpifort', flags=self._link_flags)

    def build(self):
        # We need to use with to trigger the entrance/exit functionality,
        # but otherwise the config object is used from this object, so no
        # need to use it anywhere.
        with self._config as _:
            self.grab_files()
            # generate more source files in source and source/configuration
            self.configurator()
            self.find_source_files()
            self.preprocess_fortran()
            self.preprocess_x90()
            self.psyclone()
            fparser_workaround_stop_concatenation(self.config)
            self.analyse()
            self.compile_fortran()
            self.archive_objects()
            self.link()
