"""The setuptools module for repomgt.
"""

from setuptools import setup
from distutils.cmd import Command
from distutils.errors import DistutilsOptionError

########################################################################
# Application-specific configuration

import visisort
import inspect

full_version = visisort.VERSION
(main_version, dev_version) = tuple(full_version.split('-', 1)+[''])[0:2]

# python setuptools does not allow the `-` in the version number, so we
# need to re-create the version number.
#
# if we have a dev version, tack that on to the end of the main version;
# otherwise, just use the main version.

if dev_version:
    setup_version = '{0}.{1}'.format(main_version, dev_version)
else:
    setup_version = main_version

# fetch and clean the documentation from the `visisort` package.

documentation = inspect.cleandoc(visisort.__doc__)

# rewrite the ``README.rst`` file

with open('README.rst', 'w') as readme:
    print >> readme, documentation

########################################################################
# `bump` command to bump the version number in the version file.
#   --major         = bump the major version, reset minor, patch, and pre-release
#   --minor         = bump the minor version, reset patch and pre-release
#   --patch         = if there's a pre-release, reset the pre-release;
#                     otherwise, bump patch
#   --alpha         = if there's an alpha pre-release, bump it;
#                     otherwise, bump the patch and add an alpha 1 pre-release.
#   --beta          = if there's an alpha pre-release, change it to beta 1;
#                     if there's a beta pre-release, bump it;
#                     otherwise, bump the patch and add a beta 1 pre-release.
#   --rc            = if there's an alpha or beta pre-release, change it to rc 1;
#                     if there's an rc pre-release, bump it;
#                     otherwise, bump the patch and add an rc 1 pre-release.
#   --version-file  = the filename which holds the version number.
#   --version-ident = the identifier to which the version number is assigned.
#                     If not specified, the version-file must consist solely
#                     of the version string with no quotes or other punctuation
#                     around it.

import re
import os.path
import sys
import ConfigParser

class bump_command(Command):
    """A custom command to bump a version number"""

    description = "Bump the version number of the package."

    user_options = [
        # which file holds the version identifier
        ('major', None,
         "Bump the major version and reset the minor, patch, and pre-release versions.") ,
        ('minor', None,
         "Bump the minor version and reset the patch and pre-release versions.") ,
        ('patch', None,
         "If there is a pre-release version, reset it; otherwise, bump the patch version.") ,
        ('alpha', None,
         "If there is an alpha pre-release version, bump it; otherwise, bump the patch and add alpha pre-release version 1.") ,
        ('beta', None,
         "If there is an alpha pre-release version, change it to beta pre-repease version 1; if there is a beta pre-release version, bump it; otherwise, bump the patch and add beta pre-release version 1.") ,
        ('rc', None,
         "If there is an alpha or beta pre-release version, change it to rc pre-repease version 1; if there is an rc pre-release version, bump it; otherwise, bump the patch and add rc pre-release version 1.") ,
        ('release', None,
         "Bump the packaging release without affecting the rest of the version.") ,
        ('version-file=', None,
         "The file (relative to setup.py) which holds the version string") ,
        ('version-ident=', None,
         "The identifier to which the version string is assigned.  If not specified, version-file must consist only of the version string and nothing else.") ,
    ]
    boolean_options = [ 'major', 'minor', 'patch', 'alpha', 'beta', 'rc', 'release' ]

    def initialize_options(self):
        self.version_file  = None
        self.version_ident = None
        self.major         = False
        self.minor         = False
        self.patch         = False
        self.alpha         = False
        self.beta          = False
        self.rc            = False
        self.release       = False

    def finalize_options(self):
        if self.version_file is None:
            raise DistutilsOptionError, \
                "Must supply version-file."
        ver_opts = [self.major, self.minor, self.patch].count(True)
        pre_opts = [self.alpha, self.beta, self.rc].count(True)
        if ver_opts > 1:
            raise DistutilsOptionError, \
                "Must supply only one version field (major, minor, patch) to bump."
        if pre_opts > 1:
            raise DistutilsOptionError, \
                "Must supply only one pre-release field (alpha, beta, rc) to bump."

    # really complicated regex to parse a version number in the form:
    #   <primary>(-<prerelease>)?
    # where primary is one of:
    #   <major>
    #   <major>.<minor>
    #   <major>.<minor>.<patch>
    # and prerelease is one of:
    #   a<#> or a-<#> or a.<#> or alpha<#> or alpha-<#> or alpha.<#>
    #   b<#> or b-<#> or b.<#> or beta<#> or beta-<#> or beta.<#>
    #   c<#> or c-<#> or c.<#> or rc<#> or rc-<#> or rc.<#>
    version_re = re.compile(r'''
        ^
        (?P<major>0|[1-9][0-9]*)
        (?:
            [.]
            (?P<minor>0|[1-9][0-9]*)
            (?:
                [.]
                (?P<patch>0|[1-9][0-9]*)
                (?:
                    -
                    (?:
                        (?:
                            (?P<alphatag>a(?:lpha)?[-.]?)
                            (?P<alpha>0|[1-9][0-9]*)
                        )
                      | (?:
                            (?P<betatag>b(?:eta)?[-.]?)
                            (?P<beta>0|[1-9][0-9]*)
                        )
                      | (?:
                            (?P<rctag>r?c[-.]?)
                            (?P<rc>0|[1-9][0-9]*)
                        )
                    )
                )?
            )?
        )?
        $''', re.VERBOSE)

    # bump a version number specified in the dictionary `parts`.
    # `bump` is either a key to a version component in `parts`, in which case it specifies the version component to bump,
    # or is a list of keys, in which case the _last_ such key that exists is the one that is bumped.  If none exist, the _first_ key in the list is bumped.
    # `zero` is a list of keys to zero out, if they exist.
    # `clear` is a list of keys to make not exist.

    @staticmethod
    def _bump_version(parts, bump=None, zero=(), clear=()):
        if bump is not None:
            if not isinstance(bump, basestring):
                bump_candidate = [key for key in bump if key in parts and parts[key] is not None]
                if len(bump_candidate):
                    bump = bump_candidate[-1]
                else:
                    bump = bump[0]
            if bump in parts and parts[bump] is not None:
                parts[bump] = str(1 + int(parts[bump]))
            else:
                parts[bump] = '1'
        for key in zero:
            if key in parts and parts[key] is not None:
                parts[key] = '0'
        for key in clear:
            if key in parts:
                parts[key] = None

    def run(self):
        # get the contents of the version file
        version_file_contents = open(self.version_file, 'r').read()
        # if we have a version_ident, create a regular expression to
        # look for it; if not, the RE is easy.
        if self.version_ident is None:
            # if we want the entire file, use re.DOTALL so . will match newlines
            version_file_re = re.compile(r'^(?P<version>.*)$', re.DOTALL)
        else:
            # otherwise, use re.MULTILINE so ^ and $ will match at beginning and end of a line
            # rather than just beginning and end of the string as a whole
            version_file_re = re.compile(
                        r'''^{0} *= *(?P<quote>['"])(?P<version>.*?)(?P=quote) *(?:#.*)?$'''.format(
                            re.escape(self.version_ident)
                        ),
                        re.MULTILINE
                    )
        version_file_match = version_file_re.search(version_file_contents)
        if version_file_match is None:
            raise DistutilsOptionError, \
                'Version identifier {0!r} followed by string not found!'.format(self.version_ident)
        version_string = version_file_match.group('version')
        version_string_match = self.version_re.match(version_string)
        if version_string_match is None:
            raise DistutilsOptionError, \
                'Invalid version format {0!r}'.format(version_string)
        version_parts = version_string_match.groupdict()

        # find and load the `setup.cfg` file
        setup_cfg_file = os.path.join(os.path.dirname(sys.argv[0]), 'setup.cfg')
        setup_cfg = ConfigParser.RawConfigParser()
        setup_cfg.read(setup_cfg_file)

        # ensure the `setup.cfg` file has the [build_data] section
        if not setup_cfg.has_section('build_data'):
            setup_cfg.add_section('build_data')

        # update version_parts based on the version flags.
        # we will have at most one version flag (major/minor/patch)
        # and at most one pre-release flag (alpha/beta/rc).
        # if we have a pre-release flag, then we bump that pre-release.
        # if the version previously did not have a pre-release, then we also bump
        # the flagged version component, or the lowest defined version component if none were flagged.
        # if we don't have a pre-release flag, and we do have a version flag, then we bump the version component flagged.
        # if we have neither a pre-release nor version flag, then we bump the lowest defined version component.

        if self.alpha or self.beta or self.rc:

            # if we don't currently have a pre-release version,
            # -or- we have a `higher` pre-release type than what is being bumped,
            # then we need to bump one of the version components.
            if (
                        (
                            version_parts['alpha'] is None
                            and version_parts['beta'] is None
                            and version_parts['rc'] is None
                        ) or (
                            self.alpha and (
                                version_parts['beta'] is not None
                                or version_parts['rc'] is not None
                            )
                        ) or (
                            self.beta and
                                version_parts['rc'] is not None
                        )
                    ):

                # if we have a version component flagged, bump that one and clear the lower version components (if they exist).
                # if not, we bump the lowest one that exists.
                if self.major:
                    self._bump_version(version_parts, 'major', zero=('minor', 'patch'))
                elif self.minor:
                    self._bump_version(version_parts, 'minor', zero=('patch',))
                elif self.patch:
                    self._bump_version(version_parts, 'patch')
                else:
                    self._bump_version(version_parts, ('major', 'minor', 'patch'))

                version_parts['alpha'] = version_parts['beta'] = version_parts['rc'] = None

            # bump the appropriate pre-release component and clear any lower component
            if self.alpha:
                self._bump_version(version_parts, 'alpha')
            elif self.beta:
                self._bump_version(version_parts, 'beta', clear=('alpha',))
            elif self.rc:
                self._bump_version(version_parts, 'rc', clear=('alpha', 'beta'))

        elif self.major or self.minor or self.patch:

            # We only actually bump the version if we don't have a prerelease -or- we have a non-0 version in a lower component
            if (
                        (
                            version_parts['alpha'] is None
                            and version_parts['beta'] is None
                            and version_parts['rc'] is None
                        ) or (
                            self.major and (
                                version_parts['minor'] not in (None, '0')
                                or version_parts['patch'] not in (None, '0')
                            )
                        ) or (
                            self.minor and (
                                version_parts['patch'] not in (None, '0')
                            )
                        )
                    ):

                if self.major:
                    self._bump_version(version_parts, 'major', zero=('minor', 'patch'))
                elif self.minor:
                    self._bump_version(version_parts, 'minor', zero=('patch',))
                else:
                    self._bump_version(version_parts, 'patch')

            # reset the pre-release versions no matter what
            self._bump_version(version_parts, clear=('alpha', 'beta', 'rv'))

        else:

            # with no flags on the command line, we simply bump the lowest component version that exists.
            self._bump_version(version_parts, ('major', 'minor', 'patch', 'rc', 'beta', 'alpha'))

        # if --release given, bump the release
        # if not, reset the release to '1'
        if self.release:
            # just bump the integer part of the release
            release = str(int(release) + 1)
        else:
            release = '1'

        # reconstruct the version string
        new_version_string = ''.join(
                    '{1}{0}'.format(
                        version_parts[key],
                        '' if key == 'major'
                        else '-{0}'.format(
                            'rc.' if 'rctag' not in version_parts or version_parts['rctag'] is None
                            else version_parts['rctag']
                        ) if key == 'rc'
                        else '-{0}'.format(
                            'beta.' if 'betatag' not in version_parts or version_parts['betatag'] is None
                            else version_parts['betatag']
                        ) if key == 'beta'
                        else '-{0}'.format(
                            'alpha.' if 'alphatag' not in version_parts or version_parts['alphatag'] is None
                            else version_parts['alphatag']
                        ) if key == 'alpha'
                        else '.'
                    )
                    for key in ('major', 'minor', 'patch', 'rc', 'beta', 'alpha')
                        if key in version_parts and version_parts[key] is not None
                )

        if new_version_string != version_string:

            # finally, we can replace the version string in the original file
            version_file_contents = (
                        version_file_contents[:version_file_match.start('version')]
                        + new_version_string
                        + version_file_contents[version_file_match.end('version'):]
                    )

            # and recreate the file, carefully
            version_file = open(self.version_file, 'r+')
            version_file.write(version_file_contents)
            version_file.truncate()
            version_file.close()

            print 'Version in {0!r} bumped from {1!r} to {2!r}'.format(self.version_file, version_string, new_version_string)

            setup_cfg.set('build_data', 'version', new_version_string.split('-',1)[0])

            # re-write the `build.cfg` file

            print 'setup.cfg version bumped to {0!r}'.format(setup_cfg.get('build_data', 'version'))
            setup_cfg.write(open(setup_cfg_file, 'w'))

########################################################################
# the main setup call.

setup(
    name = 'visisort' ,
    version = setup_version ,
    description = documentation.split('\n',1)[0],
    long_description = documentation,
    url = 'https://github.com/darkfoxprime/python-visisort' ,
### bugtrack_url = 'https://github.com/darkfoxprime/python-easy_xml/issues' , ### NOT SUPPORTED by distutils :(
    author = 'Johnson Earls' ,
    author_email = 'darkfoxprime@gmail.com' ,
    license = 'ISC' ,
    classifiers = [
        'Development Status :: 4 - Beta' ,
        'Intended Audience :: Developers' ,
        'License :: OSI Approved :: ISC License (ISCL)' ,
        'Operating System :: OS Independent' ,
        'Programming Language :: Python :: 2.3' ,
        'Programming Language :: Python :: 2.4' ,
        'Programming Language :: Python :: 2.5' ,
        'Programming Language :: Python :: 2.6' ,
        'Programming Language :: Python :: 2.7' ,
        'Topic :: Software Development :: Libraries :: Python Modules' ,
        'Topic :: Text Processing :: Markup :: XML' ,
    ] ,
    keywords = 'sort,gui' ,
    packages = [ 'visisort' ] ,
    install_requires = [] ,
    package_data = {} ,
    data_files = [] ,
    entry_points = {
        'console_scripts': [
            'visisort=visisort.main:main',
        ]
    } ,
    cmdclass = {
        'bump': bump_command ,
    } ,
)
