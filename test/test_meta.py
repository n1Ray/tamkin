# -*- coding: utf-8 -*-
# TAMkin is a post-processing toolkit for normal mode analysis, thermochemistry
# and reaction kinetics.
# Copyright (C) 2008-2012 Toon Verstraelen <Toon.Verstraelen@UGent.be>, An Ghysels
# <An.Ghysels@UGent.be> and Matthias Vandichel <Matthias.Vandichel@UGent.be>
# Center for Molecular Modeling (CMM), Ghent University, Ghent, Belgium; all
# rights reserved unless otherwise stated.
#
# This file is part of TAMkin.
#
# TAMkin is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# In addition to the regulations of the GNU General Public License,
# publications and communications based in parts on this program or on
# parts of this program are required to cite the following article:
#
# "TAMkin: A Versatile Package for Vibrational Analysis and Chemical Kinetics",
# An Ghysels, Toon Verstraelen, Karen Hemelsoet, Michel Waroquier and Veronique
# Van Speybroeck, Journal of Chemical Information and Modeling, 2010, 50,
# 1736-1750W
# http://dx.doi.org/10.1021/ci100099g
#
# TAMkin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
#--


from tamkin import *

import os, glob, subprocess, sys


def check_example(dirname, fn_py):
    # fix python path
    env = dict(os.environ)
    python_path = env.get('PYTHONPATH')
    if python_path is None:
        python_path = os.getcwd()
    else:
        python_path += ':' + os.getcwd()
    env['PYTHONPATH'] = python_path

    # prepare Popen arguments
    root = os.path.join("examples", dirname)
    assert os.path.isdir(root)
    script = os.path.join(root, fn_py)
    assert os.path.isfile(script)

    # run example and pass through the output
    p = subprocess.Popen([fn_py], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    p.wait()
    sys.stdout.write(p.stdout.read())
    sys.stderr.write(p.stderr.read())

    # final check
    assert p.returncode == 0

def test_example_001():
    check_example("001_ethane", "./thermo.py")

def test_example_002():
    check_example("002_linear_co2", "./thermo.py")

def test_example_003():
    check_example("003_pentane", "./thermo.py")

def test_example_005():
    check_example("005_acrylamide_reaction", "./reaction.py")

def test_example_006():
    check_example("006_5T_ethyl_ethene_addition", "./reaction.py")

def test_example_007():
    check_example("007_mfi_propene_reaction", "./reaction.py")

def test_example_008():
    check_example("008_ethane_rotor", "./thermo.py")

def test_example_009():
    check_example("009_ethyl_ethene", "./reaction.py")

def test_example_012():
    check_example("012_ethyl_ethene_scaling", "./reaction.py")

def test_example_013():
    check_example("013_butane", "./thermo.py")

def test_example_014():
    check_example("014_pentane_mbh", "./thermo.py")

def test_example_015():
    check_example("015_kie", "./reaction.py")

def test_example_016():
    check_example("016_modes", "./modes.py")

def test_example_017():
    check_example("017_activationkineticmodel", "./reaction.py")

def test_example_018():
    check_example("018_physisorption", "./adsorption.py")

def test_example_019():
    check_example("019_ethyl_ethene_simple", "./kinetic.py")

def test_example_020():
    check_example("020_butane_conformers", "./equilibrium.py")

def test_example_021():
    check_example("021_water_formation", "./formation.py")

def test_code_quality():
    root = "tamkin"
    assert os.path.isdir(root)
    white = (" ", "\t")
    for fn in glob.glob("%s/*.py") + glob.glob("%s/io/*.py"):
        f = file(fn)
        for line in f:
            assert line[-2] not in white
