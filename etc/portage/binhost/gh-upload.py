#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2021-2022 by Yen-Chin, Lee <coldnew.tw@gmail.com>
# Copyright 2020 by generik at spreequalle.de. All rights reserved.
# This file is released under the "JSON License Agreement". Please see the LICENSE
# file that should have been included as part of this package.

import os
import socket
import re
import xml.etree.ElementTree as xml
from pathlib import Path
from github import Github, GithubException, UnknownObjectException, InputGitAuthor

gh_repo = 'coldnew/gentoo-binhost'
gh_token = '<your github access token>'
gh_branch = os.environ['CHOST'] # use chost as git branch name
gh_relName = gh_branch + '/' + os.environ['CATEGORY'] # create new github release for every category
gh_author = InputGitAuthor(os.environ['PORTAGE_BUILD_USER'], os.environ['PORTAGE_BUILD_USER'] + '@' + socket.getfqdn())
g_header_uri = "https://github.com/{}/release/download/{}".format(gh_repo, gh_branch)

g_pkgName = os.environ['PF'] # create a new github asset for every package
g_pkgVersion = os.environ['PV']
g_cat = os.environ['CATEGORY']

# detect pkgdir layout
# https://wiki.gentoo.org/wiki/Binary_package_guide
g_pkgdirLayoutVersion = 2 if os.environ['PORTAGE_FEATURES'].__contains__('binpkg-multi-instance') else 1

g_xpakExt = 'tbz2' # XPAK extension (chanding compression scheme $BINPKG_COMPRESS does not change the extenstion)
g_xpak = os.environ['PF'] + '.' + g_xpakExt
g_xpakPath = os.environ['PKGDIR'] + '/' + g_cat + '/' + g_xpak
g_xpakStatus = ' added.'
g_manifest = 'Packages'
g_manifestPath = os.environ['PKGDIR'] + '/' + g_manifest

if g_pkgdirLayoutVersion == 2:
    g_xpakExt = 'xpak'
    g_xpakDir = os.environ['PKGDIR'] + '/' + g_cat + '/' + os.environ['PN']
    g_buildID = str(len([name for name in os.listdir(g_xpakDir) if os.path.isfile(os.path.join(g_xpakDir,name)) and name.startswith(os.environ['PF'] + '-')]))
    g_xpak = os.environ['PF'] + '-' + g_buildID  + '.' + g_xpakExt
    g_xpakPath = os.environ['PKGDIR'] + '/' + g_cat + '/' + os.environ['PN'] + '/' + g_xpak
    # create new github release for every category
    g_cat = os.environ['CATEGORY']  + '/' + os.environ['PN']
    gh_relName = gh_branch + '/' + g_cat # create new github release for every category

# FIXME figure out how to do this right, will fail on custom repos
def getXpakDesc():
    try:
        # this has to be relative to the ebuild in case of different repos
        # custom repos have no metadata.xml for base categories like sys-apps
        # if packages from these there merged before github release create we don't get the description
        g_catMetadataFile = Path(os.environ['EBUILD']).parents[1] / 'metadata.xml'
        root = xml.parse(g_catMetadataFile)
        g_catDesc = root.findall('./longdescription[@lang="en"]')

        if len(g_catDesc) > 0:
            g_catDesc = g_catDesc[0].text.strip()
            g_catDesc = re.sub('^\s*', '', g_catDesc, flags=re.M)  # strip leading spaces>
            g_catDesc = re.sub('\n', ' ', g_catDesc, flags=re.M)  # convert to single lin>
    except:
        g_catDesc = 'custom category'

    return g_catDesc

def getEbuildDesc():
    """Get DESCRIPTION from ebuild"""
    try:
        g_catDesc = ''
        # read description fron ebuild
        ebuildPath = os.environ['EBUILD']
        with open(ebuildPath, 'r', encoding='utf-8') as ebuildFile:
            for line in ebuildFile:
                line = line.strip()
                try:
                    key, value = line.split('=', 1)
                except ValueError:
                    continue
                if key == 'DESCRIPTION':
                    g_catDesc = value
        # remove quotes at start and end
        g_catDesc = g_catDesc.strip('\"')
    except:
        g_catDesc = ''

    return g_catDesc

g = Github(gh_token, timeout = 280)
repo = g.get_repo(gh_repo)

# make sure we are working on an existent branch
try:
    branch = repo.get_branch(gh_branch)
except GithubException:
    print("branch not found!\nCreate git branch: '%s' first!" % gh_branch)
    exit(1)

# get release
try:
    rel = repo.get_release(gh_relName)
# create new release (gentoo category), read category description from gentoo metadata
except UnknownObjectException:
    if g_pkgdirLayoutVersion == 2:
        g_catDesc = getEbuildDesc()
    else:
        g_catDesc = getXpakDesc()

    rel = repo.create_git_release(gh_relName, g_cat, g_catDesc, target_commitish=gh_branch)

# upload packages as an gitlab asset
assets = rel.get_assets()
for asset in rel.get_assets():
    if asset.name == g_xpak:
        g_xpakStatus = ' updated.'
        asset.delete_asset()

asset = rel.upload_asset(path=g_xpakPath, content_type='application/x-tar', name=g_xpak)
print('GIT ' + g_xpak + ' upload')

# create/update Packages file
try:
    commitMsg = g_cat + "-" + g_pkgVersion + g_xpakStatus
    with open(g_manifestPath, 'r') as file:
        g_manifestFile = file.read()

    # check if we need to insert PORTAGE_BINHOST_HEADER_URI in Packages
    # the URI: entry will always between PROFILE: and TIMESTAMP:
    def insertURI(match):
       return match.group(1) + "URI: {}\n".format(g_header_uri) + match.group(2)
    g_manifestFile = re.sub(r'(PROFILE:.*\n)(TIMESTAMP:.*\n)', insertURI, g_manifestFile)

    # receive git file/blob reference via git tree
    ref = repo.get_git_ref(f'heads/{gh_branch}') # get branch ref
    tree = repo.get_git_tree(ref.object.sha).tree # get git tree
    sha = [x.sha for x in tree if x.path == g_manifest] # get file sha

    if not sha:
        # create new file (Packages)
        repo.create_file(g_manifest, commitMsg, g_manifestFile, branch=gh_branch, committer=gh_author)
    else:
        repo.update_file(g_manifest, commitMsg, g_manifestFile, sha[0], branch=gh_branch, committer=gh_author)
except Exception as e:
    print('error handling Manifest under: ' + g_manifestPath + ' Error: ' + str(e))
    exit(1)
print('GIT ' + g_manifest + ' commit')

