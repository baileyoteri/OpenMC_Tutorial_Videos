# Bailey Oteri 
# November 7, 2025
# OpenMC Pincell Example 

# ===========================
# Initialization: 
# ===========================
import os
import openmc

# Path to cross section library file cross_section.xml
library_path = "/home/bailey/Desktop/cross_section_libs/lib80x_hdf5/cross_sections.xml"
os.environ['OPENMC_CROSS_SECTIONS'] = library_path

# ===========================
# Materials: 
# ===========================

fuel = openmc.Material(name = "UO2 Fuel Enriched 1.5%")
fuel.set_density('g/cm3', 10.313)
fuel.add_element('U', 1.0, enrichment=1.5)
fuel.add_element('O', 2.0)

cladding = openmc.Material(name = "Zircaloy Cladding")
cladding.set_density('g/cm3', 6.55)
cladding.add_element('Zr', 0.98335, 'wo')
cladding.add_element('Sn', 0.014, 'wo')
cladding.add_element('Fe', 0.00165, 'wo')
cladding.add_element('Cr', 0.001, 'wo')

moderator = openmc.Material(name = "H2O Moderator")
moderator.set_density('g/cm3', 0.7405)
moderator.add_element('H', 2.0)
moderator.add_element('O', 1.0)
moderator.add_s_alpha_beta('c_H_in_H2O')

materials = openmc.Materials([fuel, cladding, moderator])

# need to add cross section path if using OpenMC Plotter
materials.cross_sections = library_path

materials.export_to_xml()

# ===========================
# Geometry: 
# ===========================
# Create shapes needed for pincell 
fuel_OR = openmc.ZCylinder(r = 0.375, name = "Fuel Outer Radius")
clad_OR = openmc.ZCylinder(r = 0.4, name = "Cladding Outer Radius")
# Width and height of our pincell (in cm)
pitch = 1.2
box = openmc.model.RectangularPrism(pitch, pitch, boundary_type='reflective')

# Create a universe for the fuel pin to go into: 
pincell_universe = openmc.Universe(name = "Fuel Pin Universe")

# Create cells for our fuel, cladding, and moderator 
fuel_cell = openmc.Cell(name = "Fuel Cell", fill = fuel, region = -fuel_OR)
pincell_universe.add_cell(fuel_cell)

clad_cell = openmc.Cell(name = "Cladding Cell", fill = cladding, region = +fuel_OR & -clad_OR)
pincell_universe.add_cell(clad_cell)

mod_cell = openmc.Cell(name = "Moderator Cell", fill = moderator, region = +clad_OR)
pincell_universe.add_cell(mod_cell)

# Put pincell universe into a 'root cell' and put that cell in a 'root universe'

root_cell = openmc.Cell(name = "Root Cell", fill = pincell_universe)
root_cell.region = -box

root_universe = openmc.Universe(universe_id=0, name = "Root Universe")
root_universe.add_cell(root_cell)

geometry = openmc.Geometry(root_universe)
geometry.export_to_xml()

# ===========================
# Settings: 
# ===========================
settings = openmc.Settings()

# Set how many particles we want to simulate
# Total particals simulated = batches * particles
settings.batches = 100
settings.inactive = 10
settings.particles = 5000

# Tell OpenMC where we want the neutrons to origionally come from (neutron source)
bounds = [-pitch/2, -pitch/2, -pitch/2, pitch/2, pitch/2, pitch/2]
uniform_dist = openmc.stats.Box(bounds[:3], bounds[3:], only_fissionable = True)
settings.source = openmc.IndependentSource(space = uniform_dist)

settings.export_to_xml()

# ===========================
# Tallies: 
# ===========================
# Tell OpenMC what additional data we want it to keep track of, and how
tallies = openmc.Tallies()

# Create a mesh to discretize our geometry for keeping track of our tallies 
mesh = openmc.RegularMesh()
mesh.dimension = [100, 100] # The resolution of our output tallies essentailly
mesh.lower_left = [-pitch/2, -pitch/2]
mesh.upper_right = [pitch/2, pitch/2]

mesh_filter = openmc.MeshFilter(mesh)

# Create a tally that uses the mesh we made to score flux per square in the mesh
tally = openmc.Tally(name = "Flux")
tally.filters = [mesh_filter]
tally.scores = ['flux', 'fission']
tallies.append(tally)

tallies.export_to_xml()

# ===========================
# Run OpenMC! 
# ===========================

openmc.run()
