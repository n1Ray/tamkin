# TAMkin is a post-processing toolkit for thermochemistry and kinetics analysis.
# Copyright (C) 2008-2009 Toon Verstraelen <Toon.Verstraelen@UGent.be>,
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

import numpy
from molmod.units import cm
from molmod.constants import lightspeed
from molmod.units import angstrom, amu, cm


__all__ = [
           "load_coordinates_charmm", "load_modes_charmm",
           "calculate_overlap_nma", "calculate_overlap", "write_overlap",
           "get_delta_vector", "get_delta_vector_charmmcor",
           "calculate_sensitivity_freq",
           "create_blocks_peptide_charmm", "create_subs_peptide_charmm",
           "BlocksPeptideMBH", "SubsPeptideVSA",
           "blocks_write_to_file", "subs_write_to_file",
          ]



def load_coordinates_charmm(filename):
    """Read coordinates from a standard CHARMM coordinate file."""

    # skip the lines that start with * comments
    f = open(filename,'r')
    for line in f:
        if not line.startswith("*"): break
    N = int(line.split()[0])   # nb of atoms

    # store coordinates in Nbx3 matrix
    symbols = ['']*N
    coordinates = numpy.zeros((N,3),float)
    masses = numpy.zeros(N,float)
    count = 0
    for line in f:
        words = line.split()
        symbols[count]       = words[3]
        coordinates[count,:] = numpy.array([float(word) for word in words[4:7]])*angstrom
        masses[count]        = float(words[9])*amu
        count += 1
        if count >= N: break
    f.close()
    return symbols, coordinates, masses



def load_modes_charmm(filename):
    """Read modes and frequencies from a standard CHARMM-modes-file generated by the VIBRAN module in CHARMM.
    The function returns the frequencies in atomic units and the modes (in columns).
    Charmm modes are already mass weighted and normalized.
    """
    f = file(filename)

    # skip the lines that start with * comments
    for line in f:
        if not line.strip().startswith("*"): break

    # read nb of atoms and nbfreqs (if not yet specified by user)
    words = line.split()        # the current line does not start with a *
    nbfreqs = int(words[0])
    N       = int(words[1])/3   # nb of atoms

    # skip lines with masses, 6 masses on each line
    nblines = int(numpy.ceil(N/6.0))
    masses = numpy.zeros(N,float)
    count = 0
    for line in f:
        words = line.split()
        n = len(words)
        masses[count:count+n] = numpy.array([float(word) for word in words])
        count += n
        if count >= N: break

    # read nbfreqs freqs
    CNVFRQ = 2045.5/(2.99793*6.28319)  # conversion factor, see c36a0/source/fcm/consta.fcm in charmm code
    nblines = int(numpy.ceil(nbfreqs/6.0))
    freqs = numpy.zeros(nbfreqs, float)
    countline = 0
    countfreq = 0
    for line in f:
        words = line.split()
        for word in words:
            # do conversion
            freq_sq = float(word) #squared value
            if freq_sq > 0.0:  freq =  numpy.sqrt( freq_sq)
            else:              freq = -numpy.sqrt(-freq_sq) #actually imaginary
            freqs[countfreq] = freq * CNVFRQ * lightspeed/cm # conversion factor CHARMM, put into Tamkin internal units
            countfreq += 1
        countline += 1
        if countline >= nblines: break
    if countfreq != nbfreqs:
        raise ValueError("should have read "+str(nbfreqs)+" frequencies, but read "+str(countfreq))

    # read the nbfreqs modes
    mat = numpy.zeros((3*N,nbfreqs),float)
    row = 0
    col = 0
    for line in f:
        words = line.split()
        n = len(words)
        mat[row:row+n,col] = numpy.array([float(word) for word in words])
        row += n
        if row == 3*N:
            col += 1
            row = 0

    f.close()
    return freqs, mat


def calculate_overlap_nma(nma1, nma2, filename=None):
    """Calculate overlap of modes of NMA objects, and print to file if requested."""
    overlap = calculate_overlapmatrix(nma1.modes, nma2.modes)
    if filename is not None:
        write_overlap(nma1.freqs, nma2.freqs, overlap, filename=filename)
    return overlap

def calculate_overlap(mat1, freqs1, mat2, freqs2, filename=None):
    """Calculate overlap of matrices (with corresponding frequencies), and write to file if requested."""
    overlap = calculate_overlapmatrix(mat1, mat2)
    if filename is not None:
        write_overlap(freqs1, freqs2, overlap, filename=filename)
    return overlap

def calculate_overlapmatrix(mat1, mat2):
    """Calculate overlap of matrices."""
    # check dimensions
    if mat1.shape[0] != mat2.shape[0] :
        raise ValueError("Length of columns in mat1 and mat2 should be equal, but found "+str(mat1.shape[0])+" and "+str(mat2.shape[0]) )
    # calculate overlap
    return numpy.dot(numpy.transpose(mat1), mat2)


def write_overlap(freqs1, freqs2, overlap, filename=None):
    """Write overlap matrix to a file, default is overlap.csv. Format:
    ------------------------
           | freqs2
    ------------------------
    freqs1 | mat1^T . mat2
    ------------------------
    """
    #freqs1 = freqs1 /lightspeed*cm
    #freqs2 = freqs2 /lightspeed*cm

    # write to file
    if filename==None:
        filename="overlap.csv"   # TODO sys.currentdir

    to_append="w+"   # not append, just overwrite
    f = file(filename,to_append)

    [rows,cols] = overlap.shape

    # 1. row of freqs2
    print >> f, ";"+";".join(str(g) for g in freqs2)  #this is the same

    # 2. start each row with freq of freqs1 and continue with overlaps
    for r in range(rows):
        print >> f, str(freqs1[r])+";"+";".join(str(g) for g in overlap[r,:].tolist())
    f.close()


def get_delta_vector(coor1, coor2, masses = None, normalize = False, normthreshold = 1e-10):
    """Calculate mass weighted delta vector between two conformations.
    It is assumed that the structures have been aligned (center of mass, orientation) previously.
    Optional:
    massweight  --  Whether delta vector should be mass weighted. Default is True.
    normalize  --  Whether delta vector should be normalized. Default is False."""
    # check consistency
    if len(coor1) != len(coor2):
        raise ValueError("coordinates should have same length: found "+str(len(coor1))+" and "+str(len(coor2)))

    delta = numpy.ravel(coor1 - coor2)
    if not masses is None:  #Mass-weighting delta vector
        for i,mass in enumerate(masses):
            delta[3*i:3*(i+1)] *=  numpy.sqrt(mass)
    if normalize:   #Normalizing delta vector
        norm = numpy.sum(delta**2)
        if norm < normthreshold:
            raise ValueError("Can not normalize delta vector, because norm (squared) it too small: "+str(norm))
        delta /= numpy.sqrt(norm)
    return numpy.reshape(delta, (-1,1))


def get_delta_vector_charmmcor(charmmcorfile1, charmmcorfile2, massweight = True, normalize = False):
    """Calculate mass weighted delta vector between two charmm conformations.
       Masses from first coordinate file are used.
       Optional:
       massweight  --  Whether delta vector should be mass weighted. Default is True.
       normalize  --  Whether delta vector should be normalized. Default is False."""
    symb1,coor1,masses1 = load_coordinates_charmm(charmmcorfile1)
    symb2,coor2,masses2 = load_coordinates_charmm(charmmcorfile2)
    # check consistency
    if not symb1 == symb2:
        raise ValueError("not the same atom symbols in both coordinate files: comparison makes no sense.")
    #if not masses1 == masses2:
    #    raise ValueError("not the same atom masses in both coordinate files: comparison makes no sense.")
    if massweight:
        return get_delta_vector(coor1, coor2, masses = masses1, normalize = normalize)
    else:
        return get_delta_vector(coor1, coor2, normalize = normalize)


#def get_delta_vector_molecules(molecule1, molecule2, massweight = True, normalize = False):
#    """Calculate mass weighted delta vector between two charmm conformations.
#    Optional:
#    massweight  --  Whether delta vector should be mass weighted. Default is True.
#    normalize  --  Wihether delta vector should be normalized. Default is False."""
#    # check consistency
#    if molecule1.size != molecule2.size:
#        raise ValueError("Nb of atoms is not the same in the two molecules. Found "+str(molecule1)+" (1) and "+str(molecule)+" (2).")
#    for i in range(molecule1.size):
#        if molecule1.numbers[i] != molecule2.numbers[i]:
#            raise ValueError("Atoms of molecule1 differ from those of molecule2 (different atomic numbers), but should be the same.")
#    if not molecule1.masses == molecule2.masses:
#        raise ValueError("not the same atom masses in both coordinate files: comparison makes no sense.")
#
#    if massweight:
#        return get_delta_vector(molecule1.coordinates, molecule2.coordinates,
#                    masses = molecule1.masses, normalize = normalize)
#    else:
#        return get_delta_vector(molecule1.coordinates, molecule2.coordinates, normalize = normalize)



def calculate_sensitivity_freq(nma, index, symmetric = False, massweight = True):
    """Calculate the sensity of the index-th frequency to changes of
    the mass-weighted Hessian elements.
    Optional:
    symmetric  --  Slightly different formula if symmetry of matrix is taken into account. Default False.
    massweight  --  Whether mass-weighted or un-mass-weighted Hessian is considered."""
    L = 3*len(nma.masses)
    mode = nma.modes[:,index]
    if not massweight: # un-mass-weight the mode
        for at,mass in enumerate(nma.masses):
            mode[3*at:3*(at+1)] /= numpy.sqrt(mass)
        mode = mode / numpy.sqrt(numpy.sum(mode**2))  # renormalization necessary

    mat = numpy.dot( numpy.reshape(mode,(L,1)), numpy.reshape(mode,(1,L)) )
    if symmetric:
        mat *= 2
        for i in range(L):
             mat[i,i] -= mode[i]**2
    return mat


#############################################################################
# In the following part: create atoms in blocks or atoms in subsystem for a
# standard peptide chain created in CHARMM
#
# Warning: first and last blocks are to be checked, because the atom order
# of the first and last residue are less predictable.


class BlocksPeptideMBH(object):
    # TODO add references

    def __init__(self, label=None, blocksize=1):
        self.label = label
        self.blocksize = blocksize    # the nb of residues per block, in RTB

    def calc_blocks(self, N, CA, PRO, Carbon, Oxigen, Nitrogen):
        if self.label is "RTB":
            return self.calc_blocks_RTB(N, CA, PRO, Carbon, Oxigen, Nitrogen)
        elif self.label is "dihedral":
            return self.calc_blocks_dihedral(N, CA, PRO, Carbon, Oxigen, Nitrogen)
        elif self.label is "RHbending":
            return self.calc_blocks_RHbending(N, CA, PRO, Carbon, Oxigen, Nitrogen)
        elif self.label is "normal" or self.label is None:
            return self.calc_blocks_normal(N, CA, PRO, Carbon, Oxigen, Nitrogen)
        else:
            raise NotImplementedError

    def calc_blocks_RTB(self, N, CA, PRO, Carbon, Oxigen, Nitrogen):
        """Rotation-Translation Blocks scheme of Tama et al.
        This amounts to applying the Mobile Block Hessian with
        one or more residues per block."""
        pept = []
        k = self.blocksize           # number of residues per block
        n = len(CA)/self.blocksize   # number of complete RTB-blocks

        # do for first block : ... (CA,R) x self.size - CO
        if CA[k-1] > 1:
            if CA[k-1] in PRO:
                pept.append(range(1,CA[k-1]-4))
            else:
                pept.append(range(1,CA[k-1]-2))

        # for next blocks :  (N - CA,R - CO) x self.size
        for i in xrange(1,n):   # do n-1 times
            # from first N till next N
            if CA[i*k-1] in PRO:
                if CA[(i+1)*k-1] in PRO:
                    pept.append(range(CA[i*k-1]-4,CA[(i+1)*k-1]-4))
                    #print "(side chain) proline found! (1,2)", CA[i*k-1],CA[(i+1)*k-1]
                else:
                    pept.append(range(CA[i*k-1]-4,CA[(i+1)*k-1]-2))
                    #print "(side chain) proline found! (1)", CA[i*k-1]
            else:
                if CA[(i+1)*k-1] in PRO:
                    pept.append(range(CA[i*k-1]-2,CA[(i+1)*k-1]-4))
                    #print "(side chain) proline found! (2)", CA[(i+1)*k-1]
                else:
                    pept.append(range(CA[i*k-1]-2,CA[(i+1)*k-1]-2))

        # for last block : N - CA,R
        if n*k-1 < len(CA):
            if CA[n*k-1] in PRO:
                pept.append(range(CA[n*k-1]-4,N+1))
                #print "(side chain) proline found! (1)", CA[n*k-1]
            else:
                pept.append(range(CA[n*k-1]-2,N+1))
        return pept


    def calc_blocks_dihedral(self, N, CA, PRO, Carbon, Oxigen, Nitrogen):
        """MBH scheme with linked blocks that selects the characteristic Phi and Psi
        dihedral angles of the protein backbone as variables, while other
        degrees of freedom are fixed. """
        pept = get_pept_linked(N, CA, PRO)
        res  = []

        # start with an ending :   ... CA_0,R - C
        if CA[1] in PRO:
            res.append( range(1,CA[1]-5) )
            #print "proline found!", CA[1]
        else:
            res.append( range(1,CA[1]-3) )
        # continue with normal residues : N - CA,R - C
        for i in xrange(1,len(CA)-1):
            if CA[i] in PRO:
                if CA[i+1] in PRO:
                    res.append( [CA[i]-4]+range(CA[i],CA[i+1]-5) )
                    #print "(side chain) proline found! (1,2)", CA[i],CA[i+1]
                else:
                    res.append( [CA[i]-4]+range(CA[i],CA[i+1]-3) )
                    #print "(side chain) proline found! (1)", CA[i]
            else:
                if CA[i+1] in PRO:
                    res.append( [CA[i]-2]+range(CA[i],CA[i+1]-5) )
                    #print "(side chain) proline found! (2)", CA[i+1]
                else:
                    res.append( [CA[i]-2]+range(CA[i],CA[i+1]-3) )
        # finish with another ending : N - CA,R
        if CA[-1] in PRO:
            res.append([CA[-1]-4]+range(CA[-1],N+1))
            #print "(side chain) proline found!", CA[-1]
        else:
            res.append([CA[-1]-2]+range(CA[-1],N+1))
        return res + pept


    def calc_blocks_RHbending(self, N, CA, PRO, Carbon, Oxigen, Nitrogen):
        """MBH scheme in which the CA-H bond is considered as a seperate block."""
        pept = get_pept_linked(N, CA, PRO)
        res  = []
        CH   = []

        # start with an ending
        if CA[1] in PRO:
           res.append( range(1,CA[1]-6) )
           #print "(side chain) proline found!", CA[1]
        else:
           res.append( range(1,CA[1]-4) )
        # continue with normal residues
        for i in xrange(1,len(CA)-1):  # CA and HA
            CH.append( [CA[i],CA[i]+1] )
        for i in xrange(1,len(CA)-1):  # CA and rest of residue
            if CA[i+1] in PRO:
                res.append( [CA[i]]+range(CA[i]+2,CA[i+1]-6) )
                #print "(side chain) proline found!", CA[i+1]
            else:
                res.append( [CA[i]]+range(CA[i]+2,CA[i+1]-4) )
        # finish with another ending
        CH.append([CA[-1],CA[-1]+1]) # CA and HA
        res.append([CA[-1]]+range(CA[-1]+2,N+1)) # CA and rest of residue

        return res + pept + CH

    def calc_blocks_normal(self, N, CA, PRO, Carbon, Oxigen, Nitrogen):
        """MBH scheme with linked blocks where each side chain is
        considered as a block attached to the CA atom."""
        pept = get_pept_linked(N, CA, PRO)
        res  = []

        # start with an ending
        if CA[1] in PRO:
           res.append( range(1,CA[1]-6) )
           #print "(side chain) proline found!", CA[1]
        else:
           res.append( range(1,CA[1]-4) )
        # continue with normal residues
        for i in xrange(1,len(CA)-1):
            if CA[i+1] in PRO:
                res.append( range(CA[i],CA[i+1]-6) )
                #print "(side chain) proline found!", CA[i+1]
            else:
                res.append( range(CA[i],CA[i+1]-4) )
        # finish with another ending
        res.append(range(CA[-1],N+1))

        return res + pept


def get_pept_linked(N, CA, PRO):
        # PEPT bonds = CA + CONH + CA = 6 atoms
        pept = []
        for i in xrange(1,len(CA)):
            if CA[i] in PRO:
                pept.append( [CA[i-1]] + range(CA[i]-6,CA[i]+1) )
                #print "proline found!", CA[i]
            else:
                pept.append( [CA[i-1]] + range(CA[i]-4,CA[i]+1) )
        return pept



class SubsPeptideVSA(object):

    def __init__(self, atomtype=["CA"], frequency=1):
        """VSA subsystem/environment for peptides.
        Optional:
        atomtype  --  list of strings. Let only these atom types be part of the subsystem.
        frequency  --  let only one out of every *frequency* residues participate"""
        self.atomtype = atomtype
        self.frequency = frequency

    def calc_subs(self, N, CA, PRO, Carbon, Oxigen, Nitrogen):
        subs = []
        if "C" in self.atomtype:
            subs.extend(Carbon)
        if "O" in self.atomtype:
            subs.extend(Oxigen)
        if "N" in self.atomtype:
            subs.extend(Nitrogen)
        if "CA" in self.atomtype:
            subs.extend( numpy.take(CA, range(0,len(CA),self.frequency)).tolist() )
        else:
            raise NotImplementedError
        return subs


def create_subs_peptide_charmm(charmmfile_crd, blockchoice):
    N, CA, PRO, Carbon, Oxigen, Nitrogen = select_info_peptide_charmm(charmmfile_crd)
    return blockchoice.calc_subs(N, CA, PRO, Carbon, Oxigen, Nitrogen)


def create_blocks_peptide_charmm(charmmfile_crd, blockchoice):
    N, CA, PRO, Carbon, Oxigen, Nitrogen = select_info_peptide_charmm(charmmfile_crd)
    return blockchoice.calc_blocks(N, CA, PRO, Carbon, Oxigen, Nitrogen)


def select_info_peptide_charmm(charmmfile_crd):
    # Reading from charmmfile
    f = file(charmmfile_crd)
    # nb of atoms
    for i,line in enumerate(f):
        words = line.split()
        if words[0]!="*":
            N = int(words[0])
            break
    # find CA atoms, PRO residues, Carbons, Oxigens, Nitrogens
    PRO = []
    CA = []
    Carbon = []
    Oxigen = []
    Nitrogen = []
    for i,line in enumerate(f):
        words = line.split()
        if words[3].startswith("CA"):
            CA.append(int(words[0]))
            if words[2]=="PRO":
                PRO.append(int(words[0]))
        if words[3]=="C":
            Carbon.append(int(words[0]))
        if words[3]=="O":
            Oxigen.append(int(words[0]))
        if words[3]=="N":
            Nitrogen.append(int(words[0]))
    f.close()
    return N, CA, PRO, Carbon, Oxigen, Nitrogen


def blocks_write_to_file(blocks, filename):
    f = file(filename, "w")
    for bl in blocks:
        for at in bl:
            print >> f, at
        print >> f, ""
    f.close()

def subs_write_to_file(subs, filename):
    f = file(filename, "w")
    for at in subs:
        print >> f, at
    print >> f, ""
    f.close()

