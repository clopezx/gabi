"""
EARM 1.3 (extrinsic apoptosis reaction model)

Gaudet S, Spencer SL, Chen WW, Sorger PK (2012) Exploring the Contextual
Sensitivity of Factors that Determine Cell-to-Cell Variability in
Receptor-Mediated Apoptosis. PLoS Comput Biol 8(4): e1002482.
doi:10.1371/journal.pcbi.1002482

http://www.ploscompbiol.org/article/info:doi/10.1371/journal.pcbi.1002482
"""

# This model is mostly an extension to EARM 1.0 from Albeck et al. Instead of
# duplicating the body of that model here, we'll start this model off as a copy
# of that one then modify and add components as necessary.

import re
from pysb import *
import pysb.bng
import pysb.examples.earm_1_0

# Load in EARM 1.0 components
# ==========

# FIXME this exec business is awful and confuses a lot of pysb internals. maybe
# we need a model.copy or something like that.
with open(re.sub('c$', '', pysb.examples.earm_1_0.__file__)) as sourcefile:
    exec(sourcefile.read())
model.name = 'pysb.examples.earm_1_3'

# Rename all instances of Bcl2c to Mcl1, which was determined as a more accurate
# description of that monomer based on its role in the model
# ==========

# monomer
Bcl2c.rename('Mcl1')
# initial condition parameter
Bcl2c_0.rename('Mcl1_0')
# rule
inhibit_tBid_by_Bcl2c.rename('inhibit_tBid_by_Mcl1')

# Add one novel reaction
# ==========

# degrade DISC
Parameter('kf31', 0.001)
Rule('DISC_deg', DISC(b=None) >> L(b=None) + pR(b=None), kf31)
# NOTE: In the original model this is a reversible reaction with kr31 as its
# reverse rate constant, but kr31 was set to 0. This was ostensibly done so all
# reactions had the same symmetric form, but I see no reason not to make it
# irreversible here and eliminate kr31. -JLM

# Change some initial condition values
# ==========

pR_0.value = 1000
flip_0.value = 2000
pC8_0.value = 10000
Bid_0.value = 60000
Bax_0.value = 80000
Bcl2_0.value = 30000

# Change some rate constants
# ==========

kr1.value = 1e-6
kc1.value = 1e-2
kf3.value = 1e-7
kf6.value = 1e-7
kf7.value = 1e-7
kr9.value = 0.001
kc9.value = 20
kr13.value = 1
kf14.value = 1e-6
kf15.value = 1e-6
kf16.value = 1e-6
kf17.value = 1e-6
kf18.value = 1e-6
kf19.value = 1e-6
kf20.value = 2e-6
kf21.value = 2e-6
kf22.value = 1
kf26.value = 1

# Add synthesis and degradation rules and parameters
# ==========

# generate species list and make a copy
pysb.bng.generate_equations(model)
all_species = list(model.species)
model.reset_equations()

# add some components for use in synthesis and degradation rules
Monomer('_SynthesisDummy')
Monomer('_Trash')
Parameter('_SynthesisDummy_0', 1.0)
Initial(_SynthesisDummy(), _SynthesisDummy_0)

def synthesize(name, species, ks):
    """Synthesize species with rate ks"""
    Rule(name, _SynthesisDummy() >> species, ks)

def degrade(name, species, kdeg):
    """Degrade species with rate kdeg"""
    Rule(name, species >> _Trash(), kdeg)

# almost all degradation rates use this one value
kdeg_generic = 2.9e-6
# and these are the three exceptions
Parameter('kdeg_Mcl1', 0.0001)
Parameter('kdeg_AMito', 0.0001)
Parameter('kdeg_C3_U', 0)
# fraction by which synthesis rates should be scaled (to mimic the effects of
# treating HeLa cells wth 2.5 ug/ml of cycloheximide as per Table S2, Note 2)
syn_base = 0.15
# synthesis rates are all syn_base*kdeg*IC, except for L which is 0
Parameter('ks_L', 0)

# Even though the degradation of AMito is counted as a degradation reaction, it
# is different from the others in that the reactant species is not destroyed but
# rather converted to another species. So we have to declare this one
# explicitly.
Rule('AMito_deg', AMito(b=None) >> Mito(b=None), kdeg_AMito)

# loop over all species and create associated synthesis and degradation rates
# and reactions
for species in all_species:
    species_name = '_'.join(mp.monomer.name for mp in species.monomer_patterns)
    ks_name = 'ks_' + species_name
    kdeg_name = 'kdeg_' + species_name
    syn_rule_name = species_name + '_syn'
    deg_rule_name = species_name + '_deg'
    ic_name = species_name + '_0'
    ks = model.parameters.get(ks_name)
    kdeg = model.parameters.get(kdeg_name)
    syn_rule = model.rules.get(syn_rule_name)
    deg_rule = model.rules.get(deg_rule_name)
    ic = model.parameters.get(ic_name)
    if kdeg is None:
        kdeg = Parameter(kdeg_name, kdeg_generic)
    if ks is None:
        ks_value = 0
        if ic is not None:
            ks_value = syn_base * kdeg.value * ic.value
        ks = Parameter(ks_name, ks_value)
    if syn_rule is None:
        synthesize(syn_rule_name, species, ks)
    if deg_rule is None:
        degrade(deg_rule_name, species, kdeg)


# ========================================


def show_species():
    """Print a table of species like Table S2"""
    for i, species in enumerate(all_species, 1):
        mp_names = [mp.monomer.name for mp in species.monomer_patterns]
        name = '_'.join(mp_names)
        display_name = ':'.join(mp_names)
        ks = model.parameters.get('ks_' + name)
        kdeg = model.parameters.get('kdeg_' + name)
        ic = model.parameters.get(name + '_0')
        if ic is not None:
            ic_value = ic.value
        else:
            ic_value = 0
        if ks.value != 0 and kdeg.value != 0:
            ic_calc = round(ks.value/kdeg.value/syn_base)
            ks_expr = '%4.2f*kdeg*%7d' % (syn_base, ic_calc)
        else:
            ks_expr = '0'
        values = (i, display_name, ic_value, ks_expr, kdeg.value)
        print '%2d | %-12s %8d %20s %10g' % values

def show_rates():
    """Print a table of rate parameters like Table S4"""
    print ("%-20s        " * 3) % ('forward', 'reverse', 'catalytic')
    print '-' * (9 + 17 + 8) * 3
    for i in range(1,29) + [31]:
        for t in ('f', 'r', 'c'):
            n = 'k%s%d' % (t,i)
            p = model.parameters.get(n)
            if p is not None:
                print "%-9s%11g       " % (p.name, p.value),
        print
