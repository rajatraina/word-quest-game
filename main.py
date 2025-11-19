word_scores = {}
math_scores = {}

import os
import json
import random
import subprocess
import argparse
import threading
import socket
from math import gcd
from flask import Flask, render_template, jsonify, request
import requests

# Game configuration
WORDS_FILE = "words.json"
SCORES_FILE = "scores.json"

# Name to grade mapping for math questions
NAME_TO_GRADE = {
    'mira': 4,
    'mira5': 5,
    'mira3': 3,
    'mira6': 6,
    'raya': 6,
    'vik': 6,
    'rajat': 12,
    'penka': 12
}

# Periodic table elements for leveling system
# Each element requires 25 points to unlock (starting at 0 for Hydrogen)
PERIODIC_ELEMENTS = [
    {'symbol': 'H', 'name': 'Hydrogen', 'atomic_number': 1, 'atomic_mass': 1.008, 
     'electron_config': '1s¹', 'facts': ['lightest element', 'most abundant in universe', 'used in rocket fuel', 'makes up water molecules']},
    {'symbol': 'He', 'name': 'Helium', 'atomic_number': 2, 'atomic_mass': 4.003, 
     'electron_config': '1s²', 'facts': ['second lightest element', 'used in balloons', 'makes voice sound funny', 'found in stars']},
    {'symbol': 'Li', 'name': 'Lithium', 'atomic_number': 3, 'atomic_mass': 6.941, 
     'electron_config': '[He]2s¹', 'facts': ['lightest metal', 'used in batteries', 'found in phones', 'treats bipolar disorder']},
    {'symbol': 'Be', 'name': 'Beryllium', 'atomic_number': 4, 'atomic_mass': 9.012, 
     'electron_config': '[He]2s²', 'facts': ['very light metal', 'used in X-ray machines', 'found in emeralds', 'toxic to humans']},
    {'symbol': 'B', 'name': 'Boron', 'atomic_number': 5, 'atomic_mass': 10.81, 
     'electron_config': '[He]2s²2p¹', 'facts': ['used in glass', 'found in detergents', 'makes things stronger', 'used in nuclear reactors']},
    {'symbol': 'C', 'name': 'Carbon', 'atomic_number': 6, 'atomic_mass': 12.01, 
     'electron_config': '[He]2s²2p²', 'facts': ['basis of all life', 'found in diamonds', 'makes up coal', 'used in pencils']},
    {'symbol': 'N', 'name': 'Nitrogen', 'atomic_number': 7, 'atomic_mass': 14.01, 
     'electron_config': '[He]2s²2p³', 'facts': ['makes up 78% of air', 'used in fertilizers', 'keeps food frozen', 'found in DNA']},
    {'symbol': 'O', 'name': 'Oxygen', 'atomic_number': 8, 'atomic_mass': 16.00, 
     'electron_config': '[He]2s²2p⁴', 'facts': ['we need it to breathe', 'makes up 21% of air', 'found in water', 'used in hospitals']},
    {'symbol': 'F', 'name': 'Fluorine', 'atomic_number': 9, 'atomic_mass': 19.00, 
     'electron_config': '[He]2s²2p⁵', 'facts': ['most reactive element', 'used in toothpaste', 'prevents cavities', 'very dangerous']},
    {'symbol': 'Ne', 'name': 'Neon', 'atomic_number': 10, 'atomic_mass': 20.18, 
     'electron_config': '[He]2s²2p⁶', 'facts': ['used in bright signs', 'glows red-orange', 'found in advertising', 'noble gas']},
    {'symbol': 'Na', 'name': 'Sodium', 'atomic_number': 11, 'atomic_mass': 22.99, 
     'electron_config': '[Ne]3s¹', 'facts': ['found in table salt', 'explodes in water', 'used in streetlights', 'keeps us healthy']},
    {'symbol': 'Mg', 'name': 'Magnesium', 'atomic_number': 12, 'atomic_mass': 24.31, 
     'electron_config': '[Ne]3s²', 'facts': ['burns very bright', 'found in fireworks', 'used in medicine', 'makes bones strong']},
    {'symbol': 'Al', 'name': 'Aluminum', 'atomic_number': 13, 'atomic_mass': 26.98, 
     'electron_config': '[Ne]3s²3p¹', 'facts': ['lightweight metal', 'used in cans', 'found in airplanes', 'recyclable']},
    {'symbol': 'Si', 'name': 'Silicon', 'atomic_number': 14, 'atomic_mass': 28.09, 
     'electron_config': '[Ne]3s²3p²', 'facts': ['used in computers', 'found in sand', 'makes glass', 'second most common element']},
    {'symbol': 'P', 'name': 'Phosphorus', 'atomic_number': 15, 'atomic_mass': 30.97, 
     'electron_config': '[Ne]3s²3p³', 'facts': ['glows in the dark', 'found in matches', 'used in fertilizers', 'important for life']},
    {'symbol': 'S', 'name': 'Sulfur', 'atomic_number': 16, 'atomic_mass': 32.07, 
     'electron_config': '[Ne]3s²3p⁴', 'facts': ['smells like rotten eggs', 'used in gunpowder', 'found in volcanoes', 'makes things yellow']},
    {'symbol': 'Cl', 'name': 'Chlorine', 'atomic_number': 17, 'atomic_mass': 35.45, 
     'electron_config': '[Ne]3s²3p⁵', 'facts': ['used in pools', 'kills bacteria', 'found in bleach', 'poisonous gas']},
    {'symbol': 'Ar', 'name': 'Argon', 'atomic_number': 18, 'atomic_mass': 39.95, 
     'electron_config': '[Ne]3s²3p⁶', 'facts': ['used in light bulbs', 'noble gas', 'found in air', 'prevents oxidation']},
    {'symbol': 'K', 'name': 'Potassium', 'atomic_number': 19, 'atomic_mass': 39.10, 
     'electron_config': '[Ar]4s¹', 'facts': ['found in bananas', 'used in fertilizers', 'explodes in water', 'keeps heart healthy']},
    {'symbol': 'Ca', 'name': 'Calcium', 'atomic_number': 20, 'atomic_mass': 40.08, 
     'electron_config': '[Ar]4s²', 'facts': ['makes bones strong', 'found in milk', 'used in chalk', 'important for teeth']},
    {'symbol': 'Sc', 'name': 'Scandium', 'atomic_number': 21, 'atomic_mass': 44.96, 
     'electron_config': '[Ar]3d¹4s²', 'facts': ['rare earth metal', 'used in sports equipment', 'found in meteors', 'makes things lighter']},
    {'symbol': 'Ti', 'name': 'Titanium', 'atomic_number': 22, 'atomic_mass': 47.87, 
     'electron_config': '[Ar]3d²4s²', 'facts': ['very strong metal', 'used in airplanes', 'found in paint', 'lightweight and strong']},
    {'symbol': 'V', 'name': 'Vanadium', 'atomic_number': 23, 'atomic_mass': 50.94, 
     'electron_config': '[Ar]3d³4s²', 'facts': ['makes steel stronger', 'found in tools', 'used in batteries', 'colorful compounds']},
    {'symbol': 'Cr', 'name': 'Chromium', 'atomic_number': 24, 'atomic_mass': 52.00, 
     'electron_config': '[Ar]3d⁵4s¹', 'facts': ['makes things shiny', 'used in chrome', 'found in stainless steel', 'colorful compounds']},
    {'symbol': 'Mn', 'name': 'Manganese', 'atomic_number': 25, 'atomic_mass': 54.94, 
     'electron_config': '[Ar]3d⁵4s²', 'facts': ['used in batteries', 'found in nuts', 'makes steel strong', 'important for health']},
    {'symbol': 'Fe', 'name': 'Iron', 'atomic_number': 26, 'atomic_mass': 55.85, 
     'electron_config': '[Ar]3d⁶4s²', 'facts': ['used in steel', 'found in blood', 'makes things strong', 'most common metal']},
    {'symbol': 'Co', 'name': 'Cobalt', 'atomic_number': 27, 'atomic_mass': 58.93, 
     'electron_config': '[Ar]3d⁷4s²', 'facts': ['used in magnets', 'found in batteries', 'makes things blue', 'important for health']},
    {'symbol': 'Ni', 'name': 'Nickel', 'atomic_number': 28, 'atomic_mass': 58.69, 
     'electron_config': '[Ar]3d⁸4s²', 'facts': ['used in coins', 'found in batteries', 'makes things shiny', 'resists rust']},
    {'symbol': 'Cu', 'name': 'Copper', 'atomic_number': 29, 'atomic_mass': 63.55, 
     'electron_config': '[Ar]3d¹⁰4s¹', 'facts': ['used in wires', 'found in pennies', 'conducts electricity', 'turns green when old']},
    {'symbol': 'Zn', 'name': 'Zinc', 'atomic_number': 30, 'atomic_mass': 65.38, 
     'electron_config': '[Ar]3d¹⁰4s²', 'facts': ['used in batteries', 'prevents rust', 'found in sunscreen', 'important for health']},
    {'symbol': 'Ga', 'name': 'Gallium', 'atomic_number': 31, 'atomic_mass': 69.72, 
     'electron_config': '[Ar]3d¹⁰4s²4p¹', 'facts': ['melts in your hand', 'used in LEDs', 'found in phones', 'shiny metal']},
    {'symbol': 'Ge', 'name': 'Germanium', 'atomic_number': 32, 'atomic_mass': 72.63, 
     'electron_config': '[Ar]3d¹⁰4s²4p²', 'facts': ['used in computers', 'found in fiber optics', 'semiconductor', 'makes things faster']},
    {'symbol': 'As', 'name': 'Arsenic', 'atomic_number': 33, 'atomic_mass': 74.92, 
     'electron_config': '[Ar]3d¹⁰4s²4p³', 'facts': ['very poisonous', 'found in nature', 'used in old paint', 'dangerous element']},
    {'symbol': 'Se', 'name': 'Selenium', 'atomic_number': 34, 'atomic_mass': 78.97, 
     'electron_config': '[Ar]3d¹⁰4s²4p⁴', 'facts': ['used in photocopiers', 'found in nuts', 'important for health', 'makes things work']},
    {'symbol': 'Br', 'name': 'Bromine', 'atomic_number': 35, 'atomic_mass': 79.90, 
     'electron_config': '[Ar]3d¹⁰4s²4p⁵', 'facts': ['red-brown liquid', 'used in fire retardants', 'smells bad', 'found in pools']},
    {'symbol': 'Kr', 'name': 'Krypton', 'atomic_number': 36, 'atomic_mass': 83.80, 
     'electron_config': '[Ar]3d¹⁰4s²4p⁶', 'facts': ['noble gas', 'used in lights', 'found in air', 'glows when electrified']},
    {'symbol': 'Rb', 'name': 'Rubidium', 'atomic_number': 37, 'atomic_mass': 85.47, 
     'electron_config': '[Kr]5s¹', 'facts': ['very reactive', 'used in research', 'found in space', 'explodes in water']},
    {'symbol': 'Sr', 'name': 'Strontium', 'atomic_number': 38, 'atomic_mass': 87.62, 
     'electron_config': '[Kr]5s²', 'facts': ['used in fireworks', 'found in bones', 'makes red flames', 'found in nature']},
    {'symbol': 'Y', 'name': 'Yttrium', 'atomic_number': 39, 'atomic_mass': 88.91, 
     'electron_config': '[Kr]4d¹5s²', 'facts': ['rare earth metal', 'used in LEDs', 'found in TVs', 'makes things glow']},
    {'symbol': 'Zr', 'name': 'Zirconium', 'atomic_number': 40, 'atomic_mass': 91.22, 
     'electron_config': '[Kr]4d²5s²', 'facts': ['used in nuclear reactors', 'found in jewelry', 'resists heat', 'very strong']},
    {'symbol': 'Nb', 'name': 'Niobium', 'atomic_number': 41, 'atomic_mass': 92.91, 
     'electron_config': '[Kr]4d⁴5s¹', 'facts': ['used in superconductor magnets', 'found in alloys', 'very rare', 'makes things strong']},
    {'symbol': 'Mo', 'name': 'Molybdenum', 'atomic_number': 42, 'atomic_mass': 95.95, 
     'electron_config': '[Kr]4d⁵5s¹', 'facts': ['used in steel', 'found in enzymes', 'makes things hard', 'important for life']},
    {'symbol': 'Tc', 'name': 'Technetium', 'atomic_number': 43, 'atomic_mass': 98.00, 
     'electron_config': '[Kr]4d⁵5s²', 'facts': ['first artificial element', 'radioactive', 'used in medicine', 'very rare']},
    {'symbol': 'Ru', 'name': 'Ruthenium', 'atomic_number': 44, 'atomic_mass': 101.07, 
     'electron_config': '[Kr]4d⁷5s¹', 'facts': ['precious metal', 'used in electronics', 'very hard', 'resists corrosion']},
    {'symbol': 'Rh', 'name': 'Rhodium', 'atomic_number': 45, 'atomic_mass': 102.91, 
     'electron_config': '[Kr]4d⁸5s¹', 'facts': ['precious metal', 'used in jewelry', 'very expensive', 'shiny and rare']},
    {'symbol': 'Pd', 'name': 'Palladium', 'atomic_number': 46, 'atomic_mass': 106.42, 
     'electron_config': '[Kr]4d¹⁰', 'facts': ['precious metal', 'used in cars', 'catalyzes reactions', 'found in jewelry']},
    {'symbol': 'Ag', 'name': 'Silver', 'atomic_number': 47, 'atomic_mass': 107.87, 
     'electron_config': '[Kr]4d¹⁰5s¹', 'facts': ['shiny metal', 'used in jewelry', 'conducts electricity best', 'used in photography']},
    {'symbol': 'Cd', 'name': 'Cadmium', 'atomic_number': 48, 'atomic_mass': 112.41, 
     'electron_config': '[Kr]4d¹⁰5s²', 'facts': ['used in batteries', 'toxic metal', 'found in paint', 'yellow color']},
    {'symbol': 'In', 'name': 'Indium', 'atomic_number': 49, 'atomic_mass': 114.82, 
     'electron_config': '[Kr]4d¹⁰5s²5p¹', 'facts': ['used in touchscreens', 'very soft', 'found in phones', 'makes things work']},
    {'symbol': 'Sn', 'name': 'Tin', 'atomic_number': 50, 'atomic_mass': 118.71, 
     'electron_config': '[Kr]4d¹⁰5s²5p²', 'facts': ['used in cans', 'found in bronze', 'makes things shiny', 'resists rust']},
    {'symbol': 'Sb', 'name': 'Antimony', 'atomic_number': 51, 'atomic_mass': 121.76, 
     'electron_config': '[Kr]4d¹⁰5s²5p³', 'facts': ['used in batteries', 'found in matches', 'makes things hard', 'toxic element']},
    {'symbol': 'Te', 'name': 'Tellurium', 'atomic_number': 52, 'atomic_mass': 127.60, 
     'electron_config': '[Kr]4d¹⁰5s²5p⁴', 'facts': ['used in solar cells', 'found in nature', 'makes things work', 'rare element']},
    {'symbol': 'I', 'name': 'Iodine', 'atomic_number': 53, 'atomic_mass': 126.90, 
     'electron_config': '[Kr]4d¹⁰5s²5p⁵', 'facts': ['used in medicine', 'found in salt', 'purple vapor', 'important for health']},
    {'symbol': 'Xe', 'name': 'Xenon', 'atomic_number': 54, 'atomic_mass': 131.29, 
     'electron_config': '[Kr]4d¹⁰5s²5p⁶', 'facts': ['noble gas', 'used in lights', 'found in air', 'glows blue']},
    {'symbol': 'Cs', 'name': 'Cesium', 'atomic_number': 55, 'atomic_mass': 132.91, 
     'electron_config': '[Xe]6s¹', 'facts': ['most reactive metal', 'used in atomic clocks', 'explodes in water', 'very soft']},
    {'symbol': 'Ba', 'name': 'Barium', 'atomic_number': 56, 'atomic_mass': 137.33, 
     'electron_config': '[Xe]6s²', 'facts': ['used in X-rays', 'found in nature', 'makes green flames', 'heavy metal']},
    {'symbol': 'La', 'name': 'Lanthanum', 'atomic_number': 57, 'atomic_mass': 138.91, 
     'electron_config': '[Xe]5d¹6s²', 'facts': ['rare earth metal', 'used in cameras', 'found in nature', 'makes things work']},
    {'symbol': 'Ce', 'name': 'Cerium', 'atomic_number': 58, 'atomic_mass': 140.12, 
     'electron_config': '[Xe]4f¹5d¹6s²', 'facts': ['rare earth metal', 'used in lighters', 'found in nature', 'most common rare earth']},
    {'symbol': 'Pr', 'name': 'Praseodymium', 'atomic_number': 59, 'atomic_mass': 140.91, 
     'electron_config': '[Xe]4f³6s²', 'facts': ['rare earth metal', 'used in magnets', 'found in nature', 'green color']},
    {'symbol': 'Nd', 'name': 'Neodymium', 'atomic_number': 60, 'atomic_mass': 144.24, 
     'electron_config': '[Xe]4f⁴6s²', 'facts': ['rare earth metal', 'used in strong magnets', 'found in headphones', 'purple color']},
    {'symbol': 'Pm', 'name': 'Promethium', 'atomic_number': 61, 'atomic_mass': 145.00, 
     'electron_config': '[Xe]4f⁵6s²', 'facts': ['radioactive element', 'used in batteries', 'very rare', 'glows in dark']},
    {'symbol': 'Sm', 'name': 'Samarium', 'atomic_number': 62, 'atomic_mass': 150.36, 
     'electron_config': '[Xe]4f⁶6s²', 'facts': ['rare earth metal', 'used in magnets', 'found in nature', 'yellow color']},
    {'symbol': 'Eu', 'name': 'Europium', 'atomic_number': 63, 'atomic_mass': 151.96, 
     'electron_config': '[Xe]4f⁷6s²', 'facts': ['rare earth metal', 'used in TVs', 'makes red color', 'very reactive']},
    {'symbol': 'Gd', 'name': 'Gadolinium', 'atomic_number': 64, 'atomic_mass': 157.25, 
     'electron_config': '[Xe]4f⁷5d¹6s²', 'facts': ['rare earth metal', 'used in MRI machines', 'magnetic', 'found in nature']},
    {'symbol': 'Tb', 'name': 'Terbium', 'atomic_number': 65, 'atomic_mass': 158.93, 
     'electron_config': '[Xe]4f⁹6s²', 'facts': ['rare earth metal', 'used in green phosphors', 'found in nature', 'makes things glow']},
    {'symbol': 'Dy', 'name': 'Dysprosium', 'atomic_number': 66, 'atomic_mass': 162.50, 
     'electron_config': '[Xe]4f¹⁰6s²', 'facts': ['rare earth metal', 'used in magnets', 'found in nature', 'very magnetic']},
    {'symbol': 'Ho', 'name': 'Holmium', 'atomic_number': 67, 'atomic_mass': 164.93, 
     'electron_config': '[Xe]4f¹¹6s²', 'facts': ['rare earth metal', 'used in magnets', 'found in nature', 'most magnetic element']},
    {'symbol': 'Er', 'name': 'Erbium', 'atomic_number': 68, 'atomic_mass': 167.26, 
     'electron_config': '[Xe]4f¹²6s²', 'facts': ['rare earth metal', 'used in fiber optics', 'found in nature', 'pink color']},
    {'symbol': 'Tm', 'name': 'Thulium', 'atomic_number': 69, 'atomic_mass': 168.93, 
     'electron_config': '[Xe]4f¹³6s²', 'facts': ['rare earth metal', 'rarest stable element', 'used in X-rays', 'very rare']},
    {'symbol': 'Yb', 'name': 'Ytterbium', 'atomic_number': 70, 'atomic_mass': 173.05, 
     'electron_config': '[Xe]4f¹⁴6s²', 'facts': ['rare earth metal', 'used in atomic clocks', 'found in nature', 'silver color']},
    {'symbol': 'Lu', 'name': 'Lutetium', 'atomic_number': 71, 'atomic_mass': 174.97, 
     'electron_config': '[Xe]4f¹⁴5d¹6s²', 'facts': ['rare earth metal', 'rarest element', 'used in research', 'very expensive']},
    {'symbol': 'Hf', 'name': 'Hafnium', 'atomic_number': 72, 'atomic_mass': 178.49, 
     'electron_config': '[Xe]4f¹⁴5d²6s²', 'facts': ['used in nuclear reactors', 'found with zirconium', 'very dense', 'resists heat']},
    {'symbol': 'Ta', 'name': 'Tantalum', 'atomic_number': 73, 'atomic_mass': 180.95, 
     'electron_config': '[Xe]4f¹⁴5d³6s²', 'facts': ['used in electronics', 'found in phones', 'resists corrosion', 'very hard']},
    {'symbol': 'W', 'name': 'Tungsten', 'atomic_number': 74, 'atomic_mass': 183.84, 
     'electron_config': '[Xe]4f¹⁴5d⁴6s²', 'facts': ['highest melting point', 'used in light bulbs', 'very hard', 'found in tools']},
    {'symbol': 'Re', 'name': 'Rhenium', 'atomic_number': 75, 'atomic_mass': 186.21, 
     'electron_config': '[Xe]4f¹⁴5d⁵6s²', 'facts': ['very rare metal', 'used in jet engines', 'very expensive', 'resists heat']},
    {'symbol': 'Os', 'name': 'Osmium', 'atomic_number': 76, 'atomic_mass': 190.23, 
     'electron_config': '[Xe]4f¹⁴5d⁶6s²', 'facts': ['densest element', 'used in pens', 'very hard', 'toxic metal']},
    {'symbol': 'Ir', 'name': 'Iridium', 'atomic_number': 77, 'atomic_mass': 192.22, 
     'electron_config': '[Xe]4f¹⁴5d⁷6s²', 'facts': ['precious metal', 'used in spark plugs', 'very dense', 'resists corrosion']},
    {'symbol': 'Pt', 'name': 'Platinum', 'atomic_number': 78, 'atomic_mass': 195.08, 
     'electron_config': '[Xe]4f¹⁴5d⁹6s¹', 'facts': ['precious metal', 'used in jewelry', 'catalyzes reactions', 'very expensive']},
    {'symbol': 'Au', 'name': 'Gold', 'atomic_number': 79, 'atomic_mass': 196.97, 
     'electron_config': '[Xe]4f¹⁴5d¹⁰6s¹', 'facts': ['precious metal', 'used in jewelry', 'never tarnishes', 'found in electronics']},
    {'symbol': 'Hg', 'name': 'Mercury', 'atomic_number': 80, 'atomic_mass': 200.59, 
     'electron_config': '[Xe]4f¹⁴5d¹⁰6s²', 'facts': ['only liquid metal', 'used in thermometers', 'very toxic', 'silver liquid']},
    {'symbol': 'Tl', 'name': 'Thallium', 'atomic_number': 81, 'atomic_mass': 204.38, 
     'electron_config': '[Xe]4f¹⁴5d¹⁰6s²6p¹', 'facts': ['very toxic', 'used in research', 'found in nature', 'dangerous element']},
    {'symbol': 'Pb', 'name': 'Lead', 'atomic_number': 82, 'atomic_mass': 207.2, 
     'electron_config': '[Xe]4f¹⁴5d¹⁰6s²6p²', 'facts': ['very heavy', 'used in batteries', 'toxic metal', 'found in old paint']},
    {'symbol': 'Bi', 'name': 'Bismuth', 'atomic_number': 83, 'atomic_mass': 208.98, 
     'electron_config': '[Xe]4f¹⁴5d¹⁰6s²6p³', 'facts': ['used in medicine', 'found in nature', 'colorful crystals', 'expands when frozen']},
    {'symbol': 'Po', 'name': 'Polonium', 'atomic_number': 84, 'atomic_mass': 209.00, 
     'electron_config': '[Xe]4f¹⁴5d¹⁰6s²6p⁴', 'facts': ['very radioactive', 'found by Marie Curie', 'very dangerous', 'glows in dark']},
    {'symbol': 'At', 'name': 'Astatine', 'atomic_number': 85, 'atomic_mass': 210.00, 
     'electron_config': '[Xe]4f¹⁴5d¹⁰6s²6p⁵', 'facts': ['rarest natural element', 'very radioactive', 'used in research', 'extremely rare']},
    {'symbol': 'Rn', 'name': 'Radon', 'atomic_number': 86, 'atomic_mass': 222.00, 
     'electron_config': '[Xe]4f¹⁴5d¹⁰6s²6p⁶', 'facts': ['radioactive gas', 'found in basements', 'very dangerous', 'noble gas']},
    {'symbol': 'Fr', 'name': 'Francium', 'atomic_number': 87, 'atomic_mass': 223.00, 
     'electron_config': '[Rn]7s¹', 'facts': ['most reactive metal', 'very radioactive', 'extremely rare', 'lasts only minutes']},
    {'symbol': 'Ra', 'name': 'Radium', 'atomic_number': 88, 'atomic_mass': 226.00, 
     'electron_config': '[Rn]7s²', 'facts': ['very radioactive', 'found by Marie Curie', 'glows in dark', 'used in old watches']},
    {'symbol': 'Ac', 'name': 'Actinium', 'atomic_number': 89, 'atomic_mass': 227.00, 
     'electron_config': '[Rn]6d¹7s²', 'facts': ['radioactive element', 'used in research', 'very rare', 'glows blue']},
    {'symbol': 'Th', 'name': 'Thorium', 'atomic_number': 90, 'atomic_mass': 232.04, 
     'electron_config': '[Rn]6d²7s²', 'facts': ['radioactive element', 'used in nuclear power', 'found in nature', 'very heavy']},
    {'symbol': 'Pa', 'name': 'Protactinium', 'atomic_number': 91, 'atomic_mass': 231.04, 
     'electron_config': '[Rn]5f²6d¹7s²', 'facts': ['very rare', 'radioactive', 'used in research', 'extremely rare']},
    {'symbol': 'U', 'name': 'Uranium', 'atomic_number': 92, 'atomic_mass': 238.03, 
     'electron_config': '[Rn]5f³6d¹7s²', 'facts': ['used in nuclear power', 'very heavy', 'radioactive', 'found in Earth\'s crust']},
    {'symbol': 'Np', 'name': 'Neptunium', 'atomic_number': 93, 'atomic_mass': 237.00, 
     'electron_config': '[Rn]5f⁴6d¹7s²', 'facts': ['first transuranic element', 'artificial', 'radioactive', 'named after Neptune']},
    {'symbol': 'Pu', 'name': 'Plutonium', 'atomic_number': 94, 'atomic_mass': 244.00, 
     'electron_config': '[Rn]5f⁶7s²', 'facts': ['used in nuclear weapons', 'artificial', 'very radioactive', 'named after Pluto']},
    {'symbol': 'Am', 'name': 'Americium', 'atomic_number': 95, 'atomic_mass': 243.00, 
     'electron_config': '[Rn]5f⁷7s²', 'facts': ['used in smoke detectors', 'artificial', 'radioactive', 'found in homes']},
    {'symbol': 'Cm', 'name': 'Curium', 'atomic_number': 96, 'atomic_mass': 247.00, 
     'electron_config': '[Rn]5f⁷6d¹7s²', 'facts': ['named after Curies', 'artificial', 'very radioactive', 'used in research']},
    {'symbol': 'Bk', 'name': 'Berkelium', 'atomic_number': 97, 'atomic_mass': 247.00, 
     'electron_config': '[Rn]5f⁹7s²', 'facts': ['named after Berkeley', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Cf', 'name': 'Californium', 'atomic_number': 98, 'atomic_mass': 251.00, 
     'electron_config': '[Rn]5f¹⁰7s²', 'facts': ['named after California', 'artificial', 'very expensive', 'used in research']},
    {'symbol': 'Es', 'name': 'Einsteinium', 'atomic_number': 99, 'atomic_mass': 252.00, 
     'electron_config': '[Rn]5f¹¹7s²', 'facts': ['named after Einstein', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Fm', 'name': 'Fermium', 'atomic_number': 100, 'atomic_mass': 257.00, 
     'electron_config': '[Rn]5f¹²7s²', 'facts': ['named after Fermi', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Md', 'name': 'Mendelevium', 'atomic_number': 101, 'atomic_mass': 258.00, 
     'electron_config': '[Rn]5f¹³7s²', 'facts': ['named after Mendeleev', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'No', 'name': 'Nobelium', 'atomic_number': 102, 'atomic_mass': 259.00, 
     'electron_config': '[Rn]5f¹⁴7s²', 'facts': ['named after Nobel', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Lr', 'name': 'Lawrencium', 'atomic_number': 103, 'atomic_mass': 262.00, 
     'electron_config': '[Rn]5f¹⁴7s²7p¹', 'facts': ['named after Lawrence', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Rf', 'name': 'Rutherfordium', 'atomic_number': 104, 'atomic_mass': 267.00, 
     'electron_config': '[Rn]5f¹⁴6d²7s²', 'facts': ['named after Rutherford', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Db', 'name': 'Dubnium', 'atomic_number': 105, 'atomic_mass': 268.00, 
     'electron_config': '[Rn]5f¹⁴6d³7s²', 'facts': ['named after Dubna', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Sg', 'name': 'Seaborgium', 'atomic_number': 106, 'atomic_mass': 271.00, 
     'electron_config': '[Rn]5f¹⁴6d⁴7s²', 'facts': ['named after Seaborg', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Bh', 'name': 'Bohrium', 'atomic_number': 107, 'atomic_mass': 272.00, 
     'electron_config': '[Rn]5f¹⁴6d⁵7s²', 'facts': ['named after Bohr', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Hs', 'name': 'Hassium', 'atomic_number': 108, 'atomic_mass': 277.00, 
     'electron_config': '[Rn]5f¹⁴6d⁶7s²', 'facts': ['named after Hesse', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Mt', 'name': 'Meitnerium', 'atomic_number': 109, 'atomic_mass': 278.00, 
     'electron_config': '[Rn]5f¹⁴6d⁷7s²', 'facts': ['named after Meitner', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Ds', 'name': 'Darmstadtium', 'atomic_number': 110, 'atomic_mass': 281.00, 
     'electron_config': '[Rn]5f¹⁴6d⁸7s²', 'facts': ['named after Darmstadt', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Rg', 'name': 'Roentgenium', 'atomic_number': 111, 'atomic_mass': 282.00, 
     'electron_config': '[Rn]5f¹⁴6d⁹7s²', 'facts': ['named after Roentgen', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Cn', 'name': 'Copernicium', 'atomic_number': 112, 'atomic_mass': 285.00, 
     'electron_config': '[Rn]5f¹⁴6d¹⁰7s²', 'facts': ['named after Copernicus', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Nh', 'name': 'Nihonium', 'atomic_number': 113, 'atomic_mass': 286.00, 
     'electron_config': '[Rn]5f¹⁴6d¹⁰7s²7p¹', 'facts': ['named after Japan', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Fl', 'name': 'Flerovium', 'atomic_number': 114, 'atomic_mass': 289.00, 
     'electron_config': '[Rn]5f¹⁴6d¹⁰7s²7p²', 'facts': ['named after Flerov', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Mc', 'name': 'Moscovium', 'atomic_number': 115, 'atomic_mass': 290.00, 
     'electron_config': '[Rn]5f¹⁴6d¹⁰7s²7p³', 'facts': ['named after Moscow', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Lv', 'name': 'Livermorium', 'atomic_number': 116, 'atomic_mass': 293.00, 
     'electron_config': '[Rn]5f¹⁴6d¹⁰7s²7p⁴', 'facts': ['named after Livermore', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Ts', 'name': 'Tennessine', 'atomic_number': 117, 'atomic_mass': 294.00, 
     'electron_config': '[Rn]5f¹⁴6d¹⁰7s²7p⁵', 'facts': ['named after Tennessee', 'artificial', 'very rare', 'used in research']},
    {'symbol': 'Og', 'name': 'Oganesson', 'atomic_number': 118, 'atomic_mass': 294.00, 
     'electron_config': '[Rn]5f¹⁴6d¹⁰7s²7p⁶', 'facts': ['named after Oganessian', 'last element', 'artificial', 'very rare']},
]

POINTS_PER_LEVEL = 10  # Every 10 points unlocks a new element level

# Cat breeds for cat leveling system
CAT_BREEDS = [
    {'breed_number': 1, 'name': 'Persian', 'emoji': '🐱', 'origin': 'Iran', 'weight': '7-12 lbs', 
     'facts': ['long, luxurious fur', 'calm and gentle', 'loves to lounge', 'very quiet meow']},
    {'breed_number': 2, 'name': 'Siamese', 'emoji': '🐈', 'origin': 'Thailand', 'weight': '8-12 lbs',
     'facts': ['very vocal and chatty', 'loves attention', 'smart and curious', 'pointed coat pattern']},
    {'breed_number': 3, 'name': 'Maine Coon', 'emoji': '🐈‍⬛', 'origin': 'USA', 'weight': '10-18 lbs',
     'facts': ['largest domestic breed', 'gentle giant', 'loves water', 'very friendly']},
    {'breed_number': 4, 'name': 'Bengal', 'emoji': '🐅', 'origin': 'USA', 'weight': '8-15 lbs',
     'facts': ['wild-looking spots', 'very active', 'loves to climb', 'water-loving']},
    {'breed_number': 5, 'name': 'Ragdoll', 'emoji': '😸', 'origin': 'USA', 'weight': '10-20 lbs',
     'facts': ['goes limp when held', 'blue eyes', 'very docile', 'loves cuddles']},
    {'breed_number': 6, 'name': 'British Shorthair', 'emoji': '😺', 'origin': 'UK', 'weight': '9-18 lbs',
     'facts': ['round face and eyes', 'plush coat', 'calm personality', 'independent']},
    {'breed_number': 7, 'name': 'Abyssinian', 'emoji': '😻', 'origin': 'Ethiopia', 'weight': '6-10 lbs',
     'facts': ['ticked coat pattern', 'very active', 'loves heights', 'dog-like personality']},
    {'breed_number': 8, 'name': 'Scottish Fold', 'emoji': '🙀', 'origin': 'Scotland', 'weight': '6-13 lbs',
     'facts': ['folded ears', 'round face', 'sweet expression', 'gentle and calm']},
    {'breed_number': 9, 'name': 'Sphynx', 'emoji': '😹', 'origin': 'Canada', 'weight': '6-12 lbs',
     'facts': ['hairless breed', 'needs warmth', 'very affectionate', 'loves attention']},
    {'breed_number': 10, 'name': 'Norwegian Forest', 'emoji': '🐾', 'origin': 'Norway', 'weight': '10-18 lbs',
     'facts': ['thick double coat', 'excellent climber', 'loves cold weather', 'independent']},
    {'breed_number': 11, 'name': 'Russian Blue', 'emoji': '😼', 'origin': 'Russia', 'weight': '7-12 lbs',
     'facts': ['silver-blue coat', 'green eyes', 'shy with strangers', 'very loyal']},
    {'breed_number': 12, 'name': 'Turkish Angora', 'emoji': '😽', 'origin': 'Turkey', 'weight': '5-9 lbs',
     'facts': ['long silky coat', 'playful and active', 'loves to jump', 'very intelligent']},
    {'breed_number': 13, 'name': 'Oriental Shorthair', 'emoji': '😾', 'origin': 'Thailand', 'weight': '5-10 lbs',
     'facts': ['slender body', 'large ears', 'very vocal', 'loves to play']},
    {'breed_number': 14, 'name': 'American Shorthair', 'emoji': '😿', 'origin': 'USA', 'weight': '8-15 lbs',
     'facts': ['hardy and healthy', 'good with kids', 'adaptable', 'friendly']},
    {'breed_number': 15, 'name': 'Exotic Shorthair', 'emoji': '🙀', 'origin': 'USA', 'weight': '7-14 lbs',
     'facts': ['Persian-like face', 'short plush coat', 'calm and sweet', 'easy-going']},
    {'breed_number': 16, 'name': 'Devon Rex', 'emoji': '😸', 'origin': 'UK', 'weight': '5-10 lbs',
     'facts': ['curly soft coat', 'large ears', 'playful and mischievous', 'loves people']},
    {'breed_number': 17, 'name': 'Cornish Rex', 'emoji': '😻', 'origin': 'UK', 'weight': '6-10 lbs',
     'facts': ['wavy coat', 'very active', 'loves to jump', 'dog-like behavior']},
    {'breed_number': 18, 'name': 'Himalayan', 'emoji': '😺', 'origin': 'USA', 'weight': '7-12 lbs',
     'facts': ['Persian-Siamese mix', 'pointed colors', 'calm and gentle', 'beautiful blue eyes']},
    {'breed_number': 19, 'name': 'Burmese', 'emoji': '😹', 'origin': 'Myanmar', 'weight': '8-12 lbs',
     'facts': ['sleek coat', 'very social', 'loves attention', 'people-oriented']},
    {'breed_number': 20, 'name': 'Tonkinese', 'emoji': '😼', 'origin': 'USA', 'weight': '6-12 lbs',
     'facts': ['Siamese-Burmese mix', 'aqua eyes', 'very playful', 'loves to talk']},
]

# Cat habitat items that unlock as you progress
CAT_HABITAT_ITEMS = [
    {'score_required': 0, 'name': 'Cardboard Box', 'emoji': '📦', 'description': 'A simple box - every cat\'s favorite!'},
    {'score_required': 10, 'name': 'Scratching Post', 'emoji': '🌳', 'description': 'Perfect for stretching and sharpening claws'},
    {'score_required': 20, 'name': 'Toy Mouse', 'emoji': '🐭', 'description': 'A fun toy to chase and pounce on'},
    {'score_required': 30, 'name': 'Window Perch', 'emoji': '🪟', 'description': 'A sunny spot to watch birds and nap'},
    {'score_required': 40, 'name': 'Cat Bed', 'emoji': '🛏️', 'description': 'A cozy bed for long naps'},
    {'score_required': 50, 'name': 'Cat Tree', 'emoji': '🌲', 'description': 'Multi-level playground for climbing'},
    {'score_required': 60, 'name': 'Feather Wand', 'emoji': '🪶', 'description': 'Interactive toy for playtime'},
    {'score_required': 70, 'name': 'Catnip Plant', 'emoji': '🌿', 'description': 'Fresh catnip for extra fun'},
    {'score_required': 80, 'name': 'Laser Pointer', 'emoji': '🔴', 'description': 'Endless entertainment'},
    {'score_required': 90, 'name': 'Water Fountain', 'emoji': '⛲', 'description': 'Fresh flowing water'},
    {'score_required': 100, 'name': 'Cat Hammock', 'emoji': '🛝', 'description': 'A relaxing hammock to lounge in'},
    {'score_required': 110, 'name': 'Tunnel System', 'emoji': '🕳️', 'description': 'Maze of tunnels to explore'},
    {'score_required': 120, 'name': 'Puzzle Feeder', 'emoji': '🧩', 'description': 'Mental stimulation while eating'},
    {'score_required': 130, 'name': 'Heated Bed', 'emoji': '🔥', 'description': 'Warm and cozy for cold days'},
    {'score_required': 140, 'name': 'Outdoor Enclosure', 'emoji': '🏡', 'description': 'Safe outdoor space to explore'},
]

# Level type configuration: which users see which level types
LEVEL_TYPE_CONFIG = {
    'raya': ['chemistry', 'cat'],      # Raya sees both
    'vik': ['chemistry'],               # Vik sees only chemistry
    'mira': ['chemistry', 'cat'],      # Mira sees both
    'mira5': ['chemistry', 'cat'],
    'mira3': ['chemistry', 'cat'],
    'mira6': ['chemistry', 'cat'],
    # Default (unknown users) see both
}

def get_level_types_for_user(player_name):
    """Get the level types a user should see. Returns list of level type strings."""
    return LEVEL_TYPE_CONFIG.get(player_name.lower(), ['chemistry', 'cat'])

def get_element_level(score):
    """Get the element level based on score. Returns element info dict."""
    level_index = min(score // POINTS_PER_LEVEL, len(PERIODIC_ELEMENTS) - 1)
    element = PERIODIC_ELEMENTS[level_index].copy()
    element['level'] = level_index + 1
    element['score_required'] = level_index * POINTS_PER_LEVEL
    element['next_level_score'] = (level_index + 1) * POINTS_PER_LEVEL if level_index < len(PERIODIC_ELEMENTS) - 1 else None
    element['progress'] = (score - element['score_required']) / POINTS_PER_LEVEL if element['next_level_score'] else 1.0
    return element

def get_cat_level(score):
    """Get the cat level based on score. Returns cat breed info + habitat items dict."""
    # Get current breed
    breed_index = min(score // POINTS_PER_LEVEL, len(CAT_BREEDS) - 1)
    breed = CAT_BREEDS[breed_index].copy()
    breed['level'] = breed_index + 1
    breed['score_required'] = breed_index * POINTS_PER_LEVEL
    breed['next_level_score'] = (breed_index + 1) * POINTS_PER_LEVEL if breed_index < len(CAT_BREEDS) - 1 else None
    breed['progress'] = (score - breed['score_required']) / POINTS_PER_LEVEL if breed['next_level_score'] else 1.0
    
    # Get unlocked habitat items
    unlocked_items = [item for item in CAT_HABITAT_ITEMS if score >= item['score_required']]
    next_item = next((item for item in CAT_HABITAT_ITEMS if score < item['score_required']), None)
    
    breed['habitat_items'] = unlocked_items
    breed['next_habitat_item'] = next_item
    breed['next_habitat_score'] = next_item['score_required'] if next_item else None
    
    return breed

# Core game logic functions (no I/O)
def get_ollama_model():
    """Get the best available Ollama model. Returns model name or None."""
    import ollama
    from ollama._types import ResponseError
    
    try:
        models_response = ollama.list()
        available_models = [m.model for m in models_response.models] if hasattr(models_response, 'models') else []
        
        if available_models:
            model_names = ['mistral', 'llama2', 'llama3', 'phi', 'gemma']
            found_model = None
            
            for model_name in model_names:
                for available in available_models:
                    if model_name in available.lower():
                        found_model = available
                        break
                if found_model:
                    break
            
            if found_model:
                return found_model
            else:
                return available_models[0]
    except Exception:
        return None
    
    return None

def is_similar_to_definition(player_answer, correct_def):
    import ollama
    from ollama._types import ResponseError
    
    model_to_use = get_ollama_model()
    if not model_to_use:
        return False
    
    try:
        prompt = f"Is the following answer similar in meaning to this definition?\nDefinition: {correct_def}\nAnswer: {player_answer}\nRespond only with 'yes' or 'no'."
        response = ollama.chat(model=model_to_use, messages=[{"role": "user", "content": prompt}])
        return 'yes' in response['message']['content'].lower()
    
    except ResponseError:
        return False
    except Exception:
        return False

def warmup_ollama():
    """Warm up the Ollama model with a simple request to reduce first-request latency."""
    def _warmup():
        import ollama
        from ollama._types import ResponseError
        
        try:
            model_to_use = get_ollama_model()
            if model_to_use:
                # Make a simple warmup request
                ollama.chat(model=model_to_use, messages=[{"role": "user", "content": "Say 'yes'"}])
        except Exception:
            # Silently fail - warmup is optional
            pass
    
    # Run warmup in background thread to not block
    thread = threading.Thread(target=_warmup, daemon=True)
    thread.start()

def load_words():
    with open(WORDS_FILE, "r") as f:
        return json.load(f)

def load_scores():
    global word_scores, math_scores
    if not os.path.exists(SCORES_FILE):
        return {}
    with open(SCORES_FILE, "r") as f:
        data = json.load(f)
        word_scores = data.get('word_scores', {})
        math_scores = data.get('math_scores', {})
        return data

def save_scores(scores):
    global word_scores, math_scores
    with open(SCORES_FILE, "w") as f:
        json.dump({**scores, 'word_scores': word_scores, 'math_scores': math_scores}, f)
        f.write('\n')

def check_answer(player_name, word, player_answer, correct_def, words):
    """Check if answer is correct. Returns (is_correct, points, message, show_mc, mc_options, correct_index)"""
    global word_scores
    
    if player_answer.lower() == word.lower():
        return (False, 0, "❌ Try defining the word, not repeating it!", False, None, None)
    
    # Load scores first to get current state
    scores = load_scores()
    user_scores = word_scores.setdefault(player_name, {})
    
    # Check if answer matches definition
    if len(player_answer.lower()) > 2 and (player_answer.lower() == correct_def.lower() or is_similar_to_definition(player_answer, correct_def)):
        user_scores[word] = user_scores.get(word, 0) + 3
        scores[player_name] = scores.get(player_name, 0) + 3
        save_scores(scores)
        return (True, 3, f"✅ +3 points  [{correct_def}]", False, None, None)
    
    # Generate multiple choice options
    options = [correct_def]
    all_defs = [w["definition"] for w in words if w["definition"] != correct_def]
    options += random.sample(all_defs, k=min(3, len(all_defs)))
    random.shuffle(options)
    correct_index = options.index(correct_def)
    
    return (False, 0, "Incorrect. Choose the correct definition:", True, options, correct_index)

def check_mc_answer(player_name, word, selected_index, correct_index, correct_def):
    """Check multiple choice answer. Returns (is_correct, points, message)"""
    global word_scores
    
    # Load scores first to get current state
    scores = load_scores()
    user_scores = word_scores.setdefault(player_name, {})
    
    if selected_index == correct_index:
        user_scores[word] = user_scores.get(word, 0) + 1
        scores[player_name] = scores.get(player_name, 0) + 1
        save_scores(scores)
        return (True, 1, "✅ +1 point")
    else:
        user_scores[word] = user_scores.get(word, 0)
        save_scores(scores)
        return (False, 0, f"❌ The correct answer was: {correct_def}")

def get_next_word(player_name, words):
    """Get the next word to quiz. Returns word_info dict."""
    global word_scores
    user_word_scores = word_scores.get(player_name, {})
    
    sorted_words = sorted(words, key=lambda w: user_word_scores.get(w['word'], -float('inf')))
    weakest_words = sorted_words[:10]
    random.shuffle(weakest_words)
    return weakest_words[0]

def get_player_score(player_name, game_type='words'):
    """Get player's current score for the given game type."""
    scores = load_scores()
    if game_type == 'math':
        # Math scores are stored separately in math_scores dict
        return math_scores.get(player_name, 0)
    # Word scores are stored in the main scores dict
    return scores.get(player_name, 0)

# Math question generation functions
def get_grade_for_name(name):
    """Get grade level for a given name."""
    return NAME_TO_GRADE.get(name.lower(), 5)  # Default to grade 5

def normalize_value(value_str):
    """
    Convert a value string (integer or fraction) to a normalized tuple for comparison.
    Returns (numerator, denominator) tuple where the fraction is in simplest form.
    For integers, returns (value, 1).
    """
    if isinstance(value_str, (int, float)):
        value_str = str(int(value_str))
    
    if '/' in value_str:
        try:
            num_str, den_str = value_str.split('/')
            num = int(num_str)
            den = int(den_str)
            if den == 0:
                return (num, den)  # Invalid, but return as-is
            # Simplify the fraction
            g = gcd(abs(num), abs(den))
            num = num // g
            den = den // g
            # Normalize sign (keep sign in numerator)
            if den < 0:
                num = -num
                den = -den
            return (num, den)
        except (ValueError, ZeroDivisionError):
            return value_str  # Return as-is if can't parse
    else:
        try:
            num = int(value_str)
            return (num, 1)
        except ValueError:
            return value_str  # Return as-is if can't parse

def generate_math_question(grade):
    """Generate a math question appropriate for the given grade level. Returns (question, correct_answer, options)."""
    max_attempts = 50  # Prevent infinite loops
    
    if grade <= 2:
        # Grade 2: Simple addition/subtraction within 20
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        op = random.choice(['+', '-'])
        if op == '+':
            correct = a + b
            question = f"{a} + {b} = ?"
        else:
            # Ensure non-negative result
            if a < b:
                a, b = b, a
            correct = a - b
            question = f"{a} - {b} = ?"
        
        # Generate wrong answers, ensuring uniqueness
        wrong1 = correct + random.randint(1, 5)
        wrong2 = correct - random.randint(1, 5) if correct > 1 else correct + random.randint(6, 10)
        wrong3 = correct + random.randint(-3, 3)
        attempts = 0
        while (wrong3 == correct or wrong3 == wrong1 or wrong3 == wrong2 or wrong3 < 0) and attempts < max_attempts:
            wrong3 = correct + random.randint(-3, 3)
            attempts += 1
        
        # Ensure wrong1 and wrong2 are different
        attempts = 0
        while wrong1 == wrong2 and attempts < max_attempts:
            wrong2 = correct - random.randint(1, 5) if correct > 1 else correct + random.randint(6, 10)
            attempts += 1
        
    elif grade <= 5:
        # Grade 5: Addition/subtraction with larger numbers, simple multiplication
        op = random.choice(['+', '-', '*'])
        if op == '+':
            a = random.randint(10, 100)
            b = random.randint(10, 100)
            correct = a + b
            question = f"{a} + {b} = ?"
        elif op == '-':
            a = random.randint(50, 200)
            b = random.randint(10, a)
            correct = a - b
            question = f"{a} - {b} = ?"
        else:  # multiplication
            a = random.randint(2, 12)
            b = random.randint(2, 12)
            correct = a * b
            question = f"{a} × {b} = ?"
        
        # Generate wrong answers, ensuring uniqueness
        wrong1 = correct + random.randint(5, 15)
        wrong2 = correct - random.randint(5, 15) if correct > 10 else correct + random.randint(16, 25)
        wrong3 = correct + random.randint(-10, 10)
        attempts = 0
        while (wrong3 == correct or wrong3 == wrong1 or wrong3 == wrong2 or wrong3 < 0) and attempts < max_attempts:
            wrong3 = correct + random.randint(-10, 10)
            attempts += 1
        
        # Ensure wrong1 and wrong2 are different
        attempts = 0
        while wrong1 == wrong2 and attempts < max_attempts:
            wrong2 = correct - random.randint(5, 15) if correct > 10 else correct + random.randint(16, 25)
            attempts += 1
    
    else:  # Grade 12
        # Grade 12: Algebra, fractions, more complex operations
        question_type = random.choice(['algebra', 'fraction', 'exponent', 'sqrt'])
        
        if question_type == 'algebra':
            # Simple linear equation: ax + b = c, solve for x
            x_val = random.randint(1, 10)
            a = random.randint(2, 5)
            b = random.randint(1, 10)
            c = a * x_val + b
            correct = x_val
            question = f"If {a}x + {b} = {c}, what is x?"
            wrong1 = x_val + random.randint(1, 3)
            wrong2 = x_val - random.randint(1, 3) if x_val > 2 else x_val + random.randint(4, 6)
            wrong3 = (c - b) // a + random.randint(-2, 2)
            attempts = 0
            while (wrong3 == correct or wrong3 == wrong1 or wrong3 == wrong2 or wrong3 <= 0) and attempts < max_attempts:
                wrong3 = (c - b) // a + random.randint(-2, 2)
                attempts += 1
            
            # Ensure wrong1 and wrong2 are different
            attempts = 0
            while wrong1 == wrong2 and attempts < max_attempts:
                wrong2 = x_val - random.randint(1, 3) if x_val > 2 else x_val + random.randint(4, 6)
                attempts += 1
        
        elif question_type == 'fraction':
            # Simple fraction addition/subtraction
            num1 = random.randint(1, 5)
            den1 = random.randint(2, 6)
            num2 = random.randint(1, 5)
            den2 = random.randint(2, 6)
            # For simplicity, use common denominator
            common_den = den1 * den2
            sum_num = num1 * den2 + num2 * den1
            # Simplify (basic)
            g = gcd(sum_num, common_den)
            correct_num = sum_num // g
            correct_den = common_den // g
            correct = f"{correct_num}/{correct_den}"
            question = f"{num1}/{den1} + {num2}/{den2} = ?"
            
            # Generate wrong answers as fractions, ensuring they're numerically different
            wrong_answers = []
            seen_values = {normalize_value(correct)}  # Track normalized values, not strings
            
            attempts = 0
            while len(wrong_answers) < 3 and attempts < max_attempts:
                # Generate candidate wrong answers
                candidates = [
                    f"{sum_num + random.randint(1, 3)}/{common_den}",  # Modified numerator
                    f"{sum_num}/{common_den + random.randint(1, 3)}",  # Modified denominator
                    f"{num1 + num2}/{den1 + den2}",  # Incorrect addition
                    f"{random.randint(1, 20)}/{random.randint(2, 20)}"  # Random fraction
                ]
                
                for candidate in candidates:
                    normalized = normalize_value(candidate)
                    if normalized not in seen_values:
                        wrong_answers.append(candidate)
                        seen_values.add(normalized)
                        if len(wrong_answers) == 3:
                            break
                
                # If still need more, generate random fractions
                if len(wrong_answers) < 3:
                    new_wrong = f"{random.randint(1, 30)}/{random.randint(2, 30)}"
                    normalized = normalize_value(new_wrong)
                    if normalized not in seen_values:
                        wrong_answers.append(new_wrong)
                        seen_values.add(normalized)
                
                attempts += 1
            
            # Ensure we have 3 wrong answers
            while len(wrong_answers) < 3:
                new_wrong = f"{random.randint(1, 30)}/{random.randint(2, 30)}"
                normalized = normalize_value(new_wrong)
                if normalized not in seen_values:
                    wrong_answers.append(new_wrong)
                    seen_values.add(normalized)
            
            wrong1, wrong2, wrong3 = wrong_answers[0], wrong_answers[1], wrong_answers[2]
        
        elif question_type == 'exponent':
            base = random.randint(2, 5)
            exp = random.randint(2, 4)
            correct = base ** exp
            question = f"{base}²" if exp == 2 else f"{base}³" if exp == 3 else f"{base}^{exp}"
            wrong1 = base * exp
            wrong2 = base + exp
            wrong3 = (base + 1) ** exp
            
            # Ensure uniqueness
            attempts = 0
            while (wrong1 == correct or wrong2 == correct or wrong3 == correct or
                   wrong1 == wrong2 or wrong1 == wrong3 or wrong2 == wrong3) and attempts < max_attempts:
                wrong1 = base * exp + random.randint(-2, 2)
                wrong2 = base + exp + random.randint(-2, 2)
                wrong3 = (base + random.randint(-1, 2)) ** exp
                attempts += 1
        
        else:  # sqrt
            num = random.choice([4, 9, 16, 25, 36, 49, 64, 81, 100])
            correct = int(num ** 0.5)
            question = f"√{num} = ?"
            wrong1 = correct + 1
            wrong2 = correct - 1 if correct > 1 else correct + 2
            wrong3 = correct + 2
            
            # Ensure uniqueness
            attempts = 0
            while (wrong1 == wrong2 or wrong1 == wrong3 or wrong2 == wrong3) and attempts < max_attempts:
                wrong2 = correct - 1 if correct > 1 else correct + 2
                wrong3 = correct + random.randint(2, 3)
                attempts += 1
    
    # Create options list and ensure all are numerically unique
    options = [str(correct), str(wrong1), str(wrong2), str(wrong3)]
    
    # Final check: ensure all options are numerically unique (not just string unique)
    seen_normalized = set()
    unique_options = []
    
    for opt in options:
        normalized = normalize_value(opt)
        if normalized not in seen_normalized:
            unique_options.append(opt)
            seen_normalized.add(normalized)
    
    # If we have duplicates by value, regenerate wrong answers
    if len(unique_options) < 4:
        attempts = 0
        seen_normalized = {normalize_value(str(correct))}  # Start with correct answer
        unique_options = [str(correct)]
        
        is_fraction = isinstance(correct, str) and '/' in str(correct)
        
        while len(unique_options) < 4 and attempts < max_attempts * 2:  # More attempts for final check
            if is_fraction:  # Fraction case
                # For fractions, generate new wrong answers that are numerically different
                candidate = f"{random.randint(1, 30)}/{random.randint(2, 30)}"
                normalized = normalize_value(candidate)
                if normalized not in seen_normalized:
                    unique_options.append(candidate)
                    seen_normalized.add(normalized)
            else:  # Integer case
                if grade <= 2:
                    candidate = int(correct) + random.randint(-10, 10)
                elif grade <= 5:
                    candidate = int(correct) + random.randint(-20, 20)
                else:
                    candidate = int(correct) + random.randint(-10, 10)
                if candidate > 0:
                    normalized = normalize_value(str(candidate))
                    if normalized not in seen_normalized:
                        unique_options.append(str(candidate))
                        seen_normalized.add(normalized)
            attempts += 1
        
        # Ensure we have at least 4 options (use original if needed, but prefer unique)
        if len(unique_options) >= 2:
            options = unique_options
        # If we still don't have 4, we'll use what we have (shouldn't happen often)
    
    random.shuffle(options)
    correct_index = options.index(str(correct))
    
    return {
        'question': question,
        'correct_answer': str(correct),
        'options': options,
        'correct_index': correct_index
    }

def get_next_math_question(player_name):
    """Get the next math question for a player based on their grade."""
    grade = get_grade_for_name(player_name)
    return generate_math_question(grade)

def check_math_answer(player_name, selected_index, correct_index, correct_answer):
    """Check math multiple choice answer. Returns (is_correct, points, message)"""
    global math_scores
    
    scores = load_scores()
    
    if selected_index == correct_index:
        # Update math score separately (just one total score per player)
        math_scores[player_name] = math_scores.get(player_name, 0) + 3
        save_scores(scores)
        return (True, 3, "✅ +3 points")
    else:
        # Ensure math_scores entry exists even for incorrect answers
        if player_name not in math_scores:
            math_scores[player_name] = 0
        save_scores(scores)
        return (False, 0, f"❌ The correct answer was: {correct_answer}")

# CLI interface functions
def ask_question_cli(word, correct_def, words, player_name):
    """CLI version of ask_question. Returns points earned."""
    print(f"\nDefine: {word.upper()}")
    print("\n📝 Type your answer:")
    player_answer = input("> ").strip()
    
    is_correct, points, message, show_mc, mc_options, correct_index = check_answer(
        player_name, word, player_answer, correct_def, words
    )
    
    if is_correct:
        print(message)
        return points
    elif show_mc:
        print(message)
        for i, opt in enumerate(mc_options):
            print(f"{chr(65+i)}) {opt}")
        choice = input("Your choice (A/B/C/D): ").strip().upper()
        if len(choice) > 0 and choice in "ABCD"[:len(mc_options)]:
            selected_index = ord(choice) - 65
            is_correct, points, message = check_mc_answer(
                player_name, word, selected_index, correct_index, correct_def
            )
            print(message)
            return points
        else:
            print(f"❌ The correct answer was: \033[4m{correct_def}\033[0m")
            return 0
    else:
        print(message)
        return 0

def launch_bonus_game_cli():
    """CLI version of bonus game selection."""
    print("You've reached 50 points! Choose a bonus game:")
    print("a) Bricks")
    print("b) Dino Run")
    print("c) Gorilla Defense")
    print("d) Skip for now")
    choice = input("> ").lower()
    if choice == "a":
        subprocess.run(["python3", "bricks.py"])
        return 35
    elif choice == "b":
        subprocess.run(["python3", "dino_game.py"])
        return 35
    elif choice == "c":
        subprocess.run(["python3", "gorilla_game.py"])
        return 35
    else:
        print("Skipping bonus game.")
        return 0

def game_loop_cli(player_name, words, games_enabled=False):
    """CLI game loop."""
    scores = load_scores()
    if player_name not in scores:
        scores[player_name] = 0
    
    while True:
        word_info = get_next_word(player_name, words)
        points = ask_question_cli(word_info["word"], word_info["definition"], words, player_name)
        scores[player_name] += points
        save_scores(scores)
        print(f"Total score: {scores[player_name]}")
        
        if games_enabled and scores[player_name] >= 50 and scores[player_name] % 20 < 5:
            cost = launch_bonus_game_cli()
            scores[player_name] -= cost

# Flask web interface
from pathlib import Path
from flask import send_from_directory

app = Flask(__name__)
words = load_words()

# Serve static files from assets directory
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve static assets like cat images."""
    assets_dir = Path('assets')
    return send_from_directory(str(assets_dir), filename)

@app.route('/')
def index():
    return render_template('word_quest.html')

@app.route('/api/start', methods=['POST'])
def start_game():
    data = request.json
    player_name = data.get('name', '').strip().lower()
    game_type = data.get('game_type', 'words').strip().lower()
    
    if not player_name:
        return jsonify({'error': 'Name required'}), 400
    
    if game_type not in ['words', 'math']:
        return jsonify({'error': 'Invalid game type. Must be "words" or "math"'}), 400
    
    scores = load_scores()
    
    # Initialize scores based on game type
    if game_type == 'math':
        if player_name not in math_scores:
            math_scores[player_name] = 0
        current_score = math_scores[player_name]
    else:
        if player_name not in scores:
            scores[player_name] = 0
        current_score = scores[player_name]
    
    save_scores(scores)
    
    # Warm up Ollama model in background to reduce first-request latency (only for words)
    if game_type == 'words':
        warmup_ollama()
    
    # Get level types for this user
    level_types = get_level_types_for_user(player_name)
    levels = {}
    if 'chemistry' in level_types:
        levels['chemistry'] = get_element_level(current_score)
    if 'cat' in level_types:
        levels['cat'] = get_cat_level(current_score)
    
    return jsonify({
        'status': 'started',
        'score': current_score,
        'game_type': game_type,
        'levels': levels,
        'level_types': level_types
    })

@app.route('/api/question', methods=['GET'])
def get_question():
    player_name = request.args.get('player', '').strip().lower()
    game_type = request.args.get('game_type', 'words').strip().lower()
    
    if not player_name:
        return jsonify({'error': 'Player name required'}), 400
    
    # Get level types for this user
    level_types = get_level_types_for_user(player_name)
    levels = {}
    
    if game_type == 'math':
        current_score = get_player_score(player_name, 'math')
        math_question = get_next_math_question(player_name)
        if 'chemistry' in level_types:
            levels['chemistry'] = get_element_level(current_score)
        if 'cat' in level_types:
            levels['cat'] = get_cat_level(current_score)
        return jsonify({
            'question': math_question['question'],
            'options': math_question['options'],
            'correct_index': math_question['correct_index'],
            'correct_answer': math_question['correct_answer'],
            'score': current_score,
            'game_type': 'math',
            'levels': levels,
            'level_types': level_types
        })
    else:
        current_score = get_player_score(player_name, 'words')
        word_info = get_next_word(player_name, words)
        if 'chemistry' in level_types:
            levels['chemistry'] = get_element_level(current_score)
        if 'cat' in level_types:
            levels['cat'] = get_cat_level(current_score)
        return jsonify({
            'word': word_info['word'],
            'definition': word_info['definition'],
            'score': current_score,
            'game_type': 'words',
            'levels': levels,
            'level_types': level_types
        })

@app.route('/api/answer', methods=['POST'])
def check_answer_api():
    data = request.json
    player_name = data.get('player', '').strip().lower()
    word = data.get('word')
    answer = data.get('answer', '').strip()
    correct_def = data.get('definition')
    
    if not player_name or not word or not answer or not correct_def:
        return jsonify({'error': 'Missing required fields'}), 400
    
    is_correct, points, message, show_mc, mc_options, correct_index = check_answer(
        player_name, word, answer, correct_def, words
    )
    
    if is_correct:
        current_score = get_player_score(player_name)
        level_types = get_level_types_for_user(player_name)
        levels = {}
        if 'chemistry' in level_types:
            levels['chemistry'] = get_element_level(current_score)
        if 'cat' in level_types:
            levels['cat'] = get_cat_level(current_score)
        return jsonify({
            'correct': True,
            'points': points,
            'score': current_score,
            'message': message,
            'levels': levels,
            'level_types': level_types
        })
    elif show_mc:
        return jsonify({
            'correct': False,
            'show_mc': True,
            'options': mc_options,
            'correct_index': correct_index
        })
    else:
        return jsonify({
            'correct': False,
            'show_mc': False,
            'message': message
        })

@app.route('/api/mc_answer', methods=['POST'])
def check_mc_answer_api():
    data = request.json
    player_name = data.get('player', '').strip().lower()
    selected_index = data.get('selected_index')
    correct_index = data.get('correct_index')
    correct_def = data.get('correct_definition')
    correct_answer = data.get('correct_answer')  # For math
    word = data.get('word')
    game_type = data.get('game_type', 'words').strip().lower()
    
    if game_type == 'math':
        if not all([player_name, selected_index is not None, correct_index is not None, correct_answer]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        is_correct, points, message = check_math_answer(
            player_name, selected_index, correct_index, correct_answer
        )
        
        current_score = get_player_score(player_name, 'math')
        level_types = get_level_types_for_user(player_name)
        levels = {}
        if 'chemistry' in level_types:
            levels['chemistry'] = get_element_level(current_score)
        if 'cat' in level_types:
            levels['cat'] = get_cat_level(current_score)
        
        return jsonify({
            'correct': is_correct,
            'points': points,
            'score': current_score,
            'message': message,
            'levels': levels,
            'level_types': level_types
        })
    else:
        if not all([player_name, selected_index is not None, correct_index is not None, correct_def, word]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        is_correct, points, message = check_mc_answer(
            player_name, word, selected_index, correct_index, correct_def
        )
        
        current_score = get_player_score(player_name, 'words')
        level_types = get_level_types_for_user(player_name)
        levels = {}
        if 'chemistry' in level_types:
            levels['chemistry'] = get_element_level(current_score)
        if 'cat' in level_types:
            levels['cat'] = get_cat_level(current_score)
        
        return jsonify({
            'correct': is_correct,
            'points': points,
            'score': current_score,
            'message': message,
            'levels': levels,
            'level_types': level_types
        })

@app.route('/api/cat_images', methods=['GET'])
def get_cat_images():
    """Serve local cat breed images from assets directory."""
    breed_name = request.args.get('breed', '').strip()
    
    if not breed_name:
        return jsonify({'error': 'Breed name required'}), 400
    
    # Convert breed name to directory name (lowercase, underscores)
    breed_dir_name = breed_name.lower().replace(' ', '_').replace("'", '')
    assets_dir = Path('assets/cat_images')
    breed_dir = assets_dir / breed_dir_name
    
    images = []
    
    # Check if local images exist
    if breed_dir.exists():
        # Get all image files in the breed directory
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(breed_dir.glob(f'*{ext}'))
            image_files.extend(breed_dir.glob(f'*{ext.upper()}'))
        
        # Sort by filename to get consistent order
        image_files.sort()
        
        # Return up to 5 images as URLs
        for img_file in image_files[:5]:
            # Create URL path relative to assets
            img_path = f"cat_images/{breed_dir_name}/{img_file.name}"
            images.append(f"/assets/{img_path}")
    
    # If no local images found, return empty list (frontend will show emoji)
    # Note: Run download_cat_images.py script to populate local images
    return jsonify({'images': images[:5]})  # Return up to 5 images

# Main entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cli', action='store_true', help='Use command-line interface instead of web UI')
    parser.add_argument('--games', action='store_true', help='Enable bonus games at milestone scores')
    parser.add_argument('--port', type=int, default=5000, help='Port for web server (default: 5000)')
    args = parser.parse_args()
    
    if args.cli:
        # CLI mode
        player_name = input("Enter your name, explorer: ").strip().lower()
        game_loop_cli(player_name, words, args.games)
    else:
        # Web mode
        print(f"Starting Word Quest Game web server...")
        print(f"Open your browser to: http://localhost:{args.port}")
        
        # Get local network IP address for access from other devices
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            print(f"Access from other devices on the same network: http://{local_ip}:{args.port}")
        except Exception:
            # Fallback if we can't determine IP
            print("(To access from other devices, find this machine's IP address)")
        
        app.run(debug=False, host='0.0.0.0', port=args.port)
