#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2019 by generik at spreequalle.de. All rights reserved.
# This file is released under the "MIT License Agreement". Please see the LICENSE
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

g_pkgName = os.environ['PF'] # create a new github asset for every package
g_cat = os.environ['CATEGORY']
g_xpakExt = 'tbz2' # XPAK extension (chanding compression scheme $BINPKG_COMPRESS does not change the extenstion)
g_xpak = os.environ['PF'] + '.' + g_xpakExt
g_xpakPath = os.environ['PKGDIR'] + '/' + g_cat + '/' + g_xpak
g_xpakStatus = ' added.'
g_manifest = 'Packages'
g_manifestPath = os.environ['PKGDIR'] + '/' + g_manifest

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

g = Github(gh_token)
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

# https://github.com/PyGithub/PyGithub/issues/661
def get_blob_content(repo, branch, path_name):
    # first get the branch reference
    ref = repo.get_git_ref(f'heads/{branch}')
    # then get the tree
    tree = repo.get_git_tree(ref.object.sha, recursive='/' in path_name).tree
    # look for path in tree
    sha = [x.sha for x in tree if x.path == path_name]
    if not sha:
        # well, not found..
        return None
    # we have sha
    return repo.get_git_blob(sha[0])

def get_contents(repo, branch, path_name):
    try:
        return repo.get_contents(path_name, ref=branch)
    except GithubException:
        return get_blob_content(repo, branch, path_name)

# create/update Packages file
try:
    commitMsg = g_pkgName + g_xpakStatus
    with open(g_manifestPath, 'r') as file:
        g_manifestFile = file.read()
# https://docs.github.com/en/rest/reference/repos#get-repository-content
# This API supports files up to 1 megabyte in size.
    #cnt = repo.get_contents(g_manifest, ref=gh_branch)
    cnt = get_contents(repo, gh_branch, g_manifest)
    cnt = repo.update_file(g_manifest, commitMsg, g_manifestFile, cnt.sha, branch=gh_branch, committer=gh_author)
except UnknownObjectException:
    # create new file (Package)
    cnt = repo.create_file(g_manifest, commitMsg, g_manifestFile, branch=gh_branch, committer=gh_author)
except Exception as e:
    print('error handling Manifest under: ' + g_manifestPath + ' due to ' + e)
    exit(1)
print('GIT ' + g_manifest + ' commit')
