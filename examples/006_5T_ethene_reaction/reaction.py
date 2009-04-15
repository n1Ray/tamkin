#!/usr/bin/env python
# TAMkin is a post-processing toolkit for thermochemistry and kinetics analysis.
# Copyright (C) 2008-2009 Toon Verstraelen <Toon.Verstraelen@UGent.be>,
# Matthias Vandichel <Matthias.Vandichel@UGent.be> and
# An Ghysels <An.Ghysels@UGent.be>
#
# This file is part of TAMkin.
#
# TAMkin is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
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


# Import the tamkin library.
from tamkin import *

# Load the gaussian data:
mol_react = load_molecule_g03fchk("5Te_etheen_react_deel2.fchk")
mol_trans = load_molecule_g03fchk("5Te_etheen_ts_deel2_punt108_freq.fchk")
# Perform the normal mode analysis
nma_react = NMA(mol_react, ConstrainExt(1e-3))
nma_trans = NMA(mol_trans, ConstrainExt(1e-3))
# Construct the two partition functions.
pf_react = PartFun(nma_react, [ExternalTranslation(), ExternalRotation(1)])
pf_trans = PartFun(nma_trans, [ExternalTranslation(), ExternalRotation(1)])

# Analyze the chemical reaction. These are the arguments:
#  1) a list of reactant partition functions
#     (one for unimolecular, two for bimolecular, ...)
#  2) the transition state partition function
#  3) the starting temperature for the fit
#  4) the final temperature for the fit
# The following are optional arguments:
#  6) temp_step: The interval on the temperature grid in Kelvin, 10 is default
#  5) mol_volume: a function that returns the molecular volume (inverse of the
#     concentration) for a given temperature. If not given, it assumes that
#     this is given: FixedVolume(temp=298.15*K, pressure=1*atm)
#  7) tunneling: a tunneling correction object
ra = ReactionAnalysis([pf_react], pf_trans, 670, 770)
ra.plot("arrhenius.png") # make the Arrhenius plot

# Estimate the error on the kinetic parameters due to level of theory artifacts
# with Monte Carlo sampling. The monte_carlo method takes three optional
# arguments:
#  1) freq_error: the relative systematic error on the frequencies
#  2) freq_energy: the relative error on the energy
#  4) num_iter: the number of monte carlo samples
ra.monte_carlo(0.05, 0.00, 100)
# plot the parameters, this includes the monte carlo results
ra.plot_parameters("parameters.png")
# write all results to a file.
ra.write_to_file("reaction.txt") # summary of the analysis

