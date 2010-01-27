# TAMkin is a post-processing toolkit for thermochemistry and kinetics analysis.
# Copyright (C) 2008-2010 Toon Verstraelen <Toon.Verstraelen@UGent.be>,
# Matthias Vandichel <Matthias.Vandichel@UGent.be> and
# An Ghysels <An.Ghysels@UGent.be>, Center for Molecular Modeling (CMM), Ghent
# University, Ghent, Belgium; all rights reserved unless otherwise stated.
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
# parts of this program are required to cite the following five articles:
#
# "Vibrational Modes in partially optimized molecular systems.", An Ghysels,
# Dimitri Van Neck, Veronique Van Speybroeck, Toon Verstraelen and Michel
# Waroquier, Journal of Chemical Physics, Vol. 126 (22): Art. No. 224102, 2007
# DOI:10.1063/1.2737444
#
# "Cartesian formulation of the Mobile Block Hesian Approach to vibrational
# analysis in partially optimized systems", An Ghysels, Dimitri Van Neck and
# Michel Waroquier, Journal of Chemical Physics, Vol. 127 (16), Art. No. 164108,
# 2007
# DOI:10.1063/1.2789429
#
# "Calculating reaction rates with partial Hessians: validation of the MBH
# approach", An Ghysels, Veronique Van Speybroeck, Toon Verstraelen, Dimitri Van
# Neck and Michel Waroquier, Journal of Chemical Theory and Computation, Vol. 4
# (4), 614-625, 2008
# DOI:10.1021/ct7002836
#
# "Mobile Block Hessian approach with linked blocks: an efficient approach for
# the calculation of frequencies in macromolecules", An Ghysels, Veronique Van
# Speybroeck, Ewald Pauwels, Dimitri Van Neck, Bernard R. Brooks and Michel
# Waroquier, Journal of Chemical Theory and Computation, Vol. 5 (5), 1203-1215,
# 2009
# DOI:10.1021/ct800489r
#
# "Normal modes for large molecules with arbitrary link constraints in the
# mobile block Hessian approach", An Ghysels, Dimitri Van Neck, Bernard R.
# Brooks, Veronique Van Speybroeck and Michel Waroquier, Journal of Chemical
# Physics, Vol. 130 (18), Art. No. 084107, 2009
# DOI:10.1063/1.3071261
#
# TAMkin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --

from tamkin.data import Molecule

from molmod import angstrom, amu, calorie, avogadro
from molmod.periodic import periodic

import numpy


__all__ = ["load_molecule_qchem"]

def load_molecule_qchem(qchemfile, hessfile = None, multiplicity=1, is_periodic = False):
    """reading molecule from Q-Chem frequency run"""
    f = file(qchemfile)
    # get coords
    for line in f:
        if line.strip().startswith("Standard Nuclear Orientation (Angstroms)"):
            break
    f.next()
    f.next()
    positions = []
    symbols = []
    for line in f:
        if line.strip().startswith("----"): break
        words = line.split()
        symbols.append(words[1])
        coor = [float(words[2]),float(words[3]),float(words[4])]
        positions.append(coor)
    positions = numpy.array(positions)*angstrom
    N = len(positions)    #nb of atoms

    numbers = numpy.zeros(N,int)
    for i, symbol in enumerate(symbols):
        numbers[i] = periodic[symbol].number
    #masses = numpy.zeros(N,float)
    #for i, symbol in enumerate(symbols):
    #    masses[i] = periodic[symbol].mass

    # grep the SCF energy
    energy = None
    for line in f:
        if line.strip().startswith("Cycle       Energy         DIIS Error"):
            break
    for line in f:
        if line.strip().endswith("met"):
            energy = float(line.split()[1]) # in hartree
            break

    # get Hessian
    hessian = numpy.zeros((3*N,3*N),float)
    if hessfile is None:
      for line in f:
          if line.strip().startswith("Hessian of the SCF Energy") or line.strip().startswith("Final Hessian"):
              break
      nb = int(numpy.ceil(N*3/6))
      for i in range(nb):
          f.next()
          row = 0
          for line in f:
              words = line.split()
              hessian[row, 6*i:6*(i+1)] = numpy.array(sum([[float(word)] for word in words[1:]],[])) #/ angstrom**2
              row += 1
              if row >= 3*N : break

    # get masses
    masses = numpy.zeros(N,float)
    for line in f:
        if line.strip().startswith("Zero point vibrational"):
            break
    f.next()
    count=0
    for line in f:
        masses[count] = float(line.split()[-1])*amu
        count += 1
        if count >= N : break

    # get Symm Nb
    for line in f:
        if line.strip().startswith("Rotational Symmetry Number is"):
            break
    symmetry_number = float(line.split()[-1])
    f.close()

    # or get Hessian from other file
    if hessfile is not None:
      f = file(hessfile)
      row = 0
      col = 0
      for line in f:
          hessian[row,col] = float(line.split()[0]) *1000*calorie/avogadro /angstrom**2
          col += 1
          if col >= 3*N:
              row += 1
              col = row
      f.close()
      for i in range(len(hessian)):
          for j in range(0,i):
              hessian[i,j] = hessian[j,i]

    # get gradient   TODO
    gradient = numpy.zeros((N,3), float)

    return Molecule(
        numbers, positions, masses, energy, gradient, hessian, multiplicity,
        symmetry_number, is_periodic
    )


