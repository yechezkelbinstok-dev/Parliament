"""Realms, provinces and the border network of Middle-earth in the late Third Age.

Coordinates are PDF points (page 2448 x 1728, y down), the same space as the base map.
Provinces are grown from their seed points (Voronoi inside each compartment of the
border network), so extra seeds shape a province without drawing its border.
"""

# Water realms are flagged so coasts are never drawn as borders.
WATER = {'belegaer', 'bay_belfalas', 'gulf_lhun', 'ice_bay', 'nenuial_lake', 'long_lake', 'sea_rhun', 'nurnen'}

REALMS = {
    # North-west
    'lindon': 'Lindon', 'ered_luin': 'Ered Luin', 'forochel': 'Forochel', 'forodwaith': 'Forodwaith',
    'arthedain': 'Arthedain', 'shire': 'The Shire', 'bree': 'Bree-land', 'old_forest': 'Old Forest',
    'cardolan': 'Cardolan', 'rhudaur': 'Rhudaur', 'angmar': 'Angmar', 'imladris': 'Imladris',
    # Mountains and the west
    'hithaeglir': 'Misty Mountains', 'gundabad': 'Gundabad', 'moria': 'Khazad-dûm', 'eregion': 'Eregion',
    'dunland': 'Dunland', 'enedwaith': 'Enedwaith', 'druwaith': 'Drúwaith Iaur', 'isengard': 'Isengard',
    # Rhovanion
    'fangorn': 'Fangorn', 'lorien': 'Lothlórien', 'anduin_vales': 'Vales of Anduin',
    'woodland_realm': 'Woodland Realm', 'woodmen': 'Woodmen', 'mirkwood': 'Mirkwood', 'dol_guldur': 'Dol Guldur',
    'ered_mithrin': 'Ered Mithrin', 'erebor': 'Erebor', 'dale': 'Dale', 'iron_hills': 'Iron Hills',
    'rhovanion': 'Rhovanion', 'brown_lands': 'Brown Lands', 'emyn_muil': 'Emyn Muil', 'dagorlad': 'Dagorlad',
    # South
    'rohan': 'Rohan', 'gondor': 'Gondor', 'druedain': 'Drúadan Forest', 'harondor': 'Harondor',
    'mordor': 'Mordor', 'near_harad': 'Near Harad', 'khand': 'Khand', 'rhun': 'Rhûn',
    # Waters
    'belegaer': 'Belegaer', 'bay_belfalas': 'Bay of Belfalas', 'gulf_lhun': 'Gulf of Lhûn',
    'ice_bay': 'Ice Bay of Forochel', 'nenuial_lake': 'Lake Nenuial', 'long_lake': 'Long Lake',
    'sea_rhun': 'Sea of Rhûn', 'nurnen': 'Sea of Nurnen',
}

# id, name, realm, seeds
_P = [
    # ---------------- Lindon ----------------
    ('forlindon', 'Forlindon', 'lindon', [(105, 330), (110, 440), (205, 400), (240, 460), (170, 330)]),
    ('forlindon_north', 'Northern Forlindon', 'lindon', [(210, 200), (230, 160), (235, 262)]),
    ('himling', 'Himling', 'lindon', [(110, 175)]),
    ('lhun_vale', 'Lhûn Vale', 'lindon', [(440, 200), (445, 290), (440, 380)]),
    ('mithlond', 'Mithlond', 'lindon', [(455, 470), (452, 548), (478, 520)]),
    ('harlindon', 'Harlindon', 'lindon', [(290, 600), (255, 680), (320, 770), (420, 785), (300, 740)]),
    ('emyn_beraid', 'Emyn Beraid', 'lindon', [(482, 525), (490, 575), (505, 600)]),
    # ---------------- Ered Luin ----------------
    ('ered_luin_north', 'Northern Ered Luin', 'ered_luin', [(330, 130), (350, 230), (340, 330), (350, 430)]),
    ('ered_luin_south', 'Southern Ered Luin', 'ered_luin', [(400, 580), (360, 640), (420, 690), (520, 645)]),
    # ---------------- Forochel / Forodwaith ----------------
    ('forochel', 'Forochel Shore', 'forochel', [(470, 80), (500, 180), (600, 175), (700, 170)]),
    ('forochel_east', 'Eastern Forochel', 'forochel', [(790, 80), (800, 160)]),
    ('forodwaith_west', 'Western Forodwaith', 'forodwaith', [(900, 80), (1000, 100), (880, 130)]),
    ('forodwaith_north', 'Northern Waste', 'forodwaith', [(1150, 90), (1250, 120)]),
    ('dragon_wastes', 'Dragon Wastes', 'forodwaith', [(1450, 120), (1600, 110), (1550, 160)]),
    ('forodwaith_east', 'Eastern Forodwaith', 'forodwaith', [(1800, 100), (1760, 180), (1900, 120)]),
    ('forodwaith_far', 'Far Forodwaith', 'forodwaith', [(2100, 100), (2300, 90), (2200, 170)]),
    # ---------------- Arthedain ----------------
    ('lhun_marches', 'Lhûn Marches', 'arthedain', [(505, 230), (515, 330), (520, 420), (520, 470)]),
    ('emyn_uial', 'Emyn Uial', 'arthedain', [(580, 250), (550, 320), (630, 290)]),
    ('nenuial', 'Nenuial', 'arthedain', [(625, 385), (650, 395), (575, 395)]),
    ('northern_marches', 'Northern Marches', 'arthedain', [(680, 230), (750, 230), (700, 300)]),
    ('north_downs', 'North Downs', 'arthedain', [(790, 330), (830, 335), (760, 360)]),
    ('upper_baranduin', 'Upper Baranduin', 'arthedain', [(720, 400), (740, 440), (705, 455)]),
    ('weather_hills', 'Weather Hills', 'arthedain', [(890, 440), (905, 475)]),
    ('midgewater', 'Midgewater Marshes', 'arthedain', [(845, 475), (860, 490)]),
    ('lone_lands', 'Lone-lands', 'rhudaur', [(960, 470), (975, 520), (1000, 480)]),
    # ---------------- The Shire ----------------
    ('westfarthing', 'Westfarthing', 'shire', [(580, 485), (620, 495), (560, 505)]),
    ('northfarthing', 'Northfarthing', 'shire', [(600, 440), (640, 440), (570, 450)]),
    ('eastfarthing', 'Eastfarthing', 'shire', [(668, 505), (670, 480), (675, 525)]),
    ('southfarthing', 'Southfarthing', 'shire', [(620, 560), (660, 570), (600, 575)]),
    ('buckland', 'Buckland', 'shire', [(690, 492), (694, 507), (697, 522)]),
    ('westmarch', 'Westmarch', 'shire', [(522, 505), (530, 540), (520, 470)]),
    # ---------------- Bree-land / Old Forest ----------------
    ('bree', 'Bree-land', 'bree', [(785, 500), (775, 490), (800, 510)]),
    ('chetwood', 'Chetwood', 'bree', [(796, 482)]),
    ('old_forest', 'Old Forest', 'old_forest', [(715, 500), (722, 520), (708, 534)]),
    ('sarn_ford', 'Sarn Ford', 'arthedain', [(640, 630), (700, 640), (590, 625)]),
    ('brandywine_marches', 'Brandywine Marches', 'arthedain', [(720, 470), (745, 480), (740, 500)]),
    # ---------------- Cardolan ----------------
    ('barrow_downs', 'Barrow-downs', 'cardolan', [(755, 515), (770, 535)]),
    ('south_downs', 'South Downs', 'cardolan', [(830, 545), (880, 548), (930, 555)]),
    ('baranduin_vale', 'Baranduin Vale', 'cardolan', [(745, 580), (760, 640), (730, 700)]),
    ('cardolan_heart', 'Inner Cardolan', 'cardolan', [(820, 600), (880, 620), (930, 620), (840, 670)]),
    ('gwathlo_vale', 'Gwathló Vale', 'cardolan', [(840, 720), (880, 690), (800, 760)]),
    ('minhiriath', 'Minhiriath', 'cardolan', [(650, 760), (620, 840), (700, 830), (580, 760)]),
    ('minhiriath_coast', 'Minhiriath Coast', 'cardolan', [(560, 760), (600, 900), (660, 905)]),
    ('eryn_vorn', 'Eryn Vorn', 'cardolan', [(515, 860), (520, 830)]),
    # ---------------- Rhudaur / Imladris / Angmar ----------------
    ('trollshaws', 'Trollshaws', 'rhudaur', [(1090, 462), (1075, 430)]),
    ('the_angle', 'The Angle', 'rhudaur', [(1050, 560), (1090, 520), (1030, 590)]),
    ('ettenmoors', 'Ettenmoors', 'rhudaur', [(1120, 345), (1150, 380), (1100, 370)]),
    ('coldfells', 'Coldfells', 'rhudaur', [(1050, 400), (1060, 360), (1080, 410)]),
    ('hoarwell_fells', 'Hoarwell Fells', 'rhudaur', [(980, 380), (1000, 420), (960, 340)]),
    ('rivendell', 'Imladris', 'imladris', [(1180, 474), (1165, 495), (1195, 490)]),
    ('carn_dum', 'Carn Dûm', 'angmar', [(955, 170), (985, 185)]),
    ('angmar_plains', 'Angmar Wastes', 'angmar', [(880, 220), (850, 270), (930, 250)]),
    ('angmar_marches', 'Angmar Marches', 'angmar', [(950, 310), (1020, 320), (880, 310)]),
    ('mount_gram', 'Mount Gram', 'angmar', [(1060, 275), (1110, 290)]),
    ('mountains_of_angmar', 'Mountains of Angmar', 'angmar', [(1040, 165), (1120, 185), (1170, 205)]),
    # ---------------- Misty Mountains, Gundabad, Moria ----------------
    ('gundabad', 'Mount Gundabad', 'gundabad', [(1220, 215), (1245, 230)]),
    ('hithaeglir_north', 'Northern Hithaeglir', 'hithaeglir', [(1235, 290), (1240, 360)]),
    ('high_pass', 'High Pass', 'hithaeglir', [(1235, 440), (1250, 470), (1220, 410)]),
    ('hithaeglir_central', 'Central Hithaeglir', 'hithaeglir', [(1210, 530), (1200, 590), (1220, 620)]),
    ('khazad_dum', 'Khazad-dûm', 'moria', [(1150, 670), (1160, 700), (1170, 650)]),
    ('dimrill_dale', 'Dimrill Dale', 'moria', [(1185, 712)]),
    ('hithaeglir_south', 'Southern Hithaeglir', 'hithaeglir', [(1125, 790), (1110, 840), (1090, 880)]),
    ('methedras', 'Methedras', 'hithaeglir', [(1080, 930), (1070, 960)]),
    # ---------------- Eregion, Dunland, Enedwaith ----------------
    ('eregion_north', 'Northern Eregion', 'eregion', [(1040, 620), (1080, 600), (1000, 640)]),
    ('hollin', 'Hollin', 'eregion', [(1030, 690), (1070, 680), (990, 690)]),
    ('glanduin_vale', 'Glanduin Vale', 'eregion', [(1050, 740), (980, 735)]),
    ('swanfleet', 'Swanfleet', 'eregion', [(915, 715), (940, 725)]),
    ('dunland_north', 'North Dunland', 'dunland', [(980, 790), (1040, 790), (930, 800)]),
    ('dunland_south', 'South Dunland', 'dunland', [(990, 900), (1040, 960), (950, 950)]),
    ('dunland_hills', 'Dunland Hills', 'dunland', [(1060, 850), (1050, 900)]),
    ('enedwaith_north', 'Northern Enedwaith', 'enedwaith', [(820, 830), (880, 810), (780, 870)]),
    ('enedwaith', 'Enedwaith', 'enedwaith', [(820, 950), (900, 980), (780, 1010)]),
    ('lond_daer', 'Lond Daer', 'enedwaith', [(715, 935), (740, 960)]),
    ('isen_mouths', 'Isen Mouths', 'enedwaith', [(720, 1050), (780, 1060), (850, 1060)]),
    ('druwaith', 'Drúwaith Iaur', 'druwaith', [(760, 1160), (840, 1150), (720, 1200), (900, 1150)]),
    # ---------------- Isengard, Fangorn, Lórien ----------------
    ('isengard', 'Nan Curunír', 'isengard', [(1050, 985), (1055, 1010)]),
    ('fangorn', 'Fangorn Forest', 'fangorn', [(1180, 920), (1220, 880), (1150, 960)]),
    ('lorien', 'Lothlórien', 'lorien', [(1250, 770), (1270, 790)]),
    ('nimrodel', 'Nimrodel', 'lorien', [(1200, 760), (1205, 785)]),
    ('celebrant_field', 'Field of Celebrant', 'lorien', [(1300, 840), (1280, 820), (1340, 870)]),
    # ---------------- Vales of Anduin ----------------
    ('anduin_springs', 'Anduin Springs', 'anduin_vales', [(1300, 270), (1310, 320)]),
    ('carrock', 'Carrock', 'anduin_vales', [(1320, 410), (1340, 440), (1320, 370)]),
    ('western_vale', 'Western Vale', 'anduin_vales', [(1300, 500), (1295, 550)]),
    ('eastern_vale', 'Eastern Vale', 'anduin_vales', [(1360, 520), (1360, 570), (1365, 480)]),
    ('gladden_fields', 'Gladden Fields', 'anduin_vales', [(1320, 625), (1350, 610), (1290, 610)]),
    ('anduin_south_vale', 'Southern Vale', 'anduin_vales', [(1300, 690), (1340, 720), (1360, 660)]),
    # ---------------- Mirkwood ----------------
    ('northern_mirkwood', 'Northern Mirkwood', 'woodland_realm', [(1380, 300), (1440, 310), (1500, 300), (1370, 360)]),
    ('thranduil', 'Halls of Thranduil', 'woodland_realm', [(1550, 340), (1590, 360), (1520, 370)]),
    ('mountains_of_mirkwood', 'Mountains of Mirkwood', 'woodland_realm', [(1520, 415), (1580, 420), (1470, 415)]),
    ('woodmen', 'Woodmen-lands', 'woodmen', [(1390, 440), (1410, 500), (1440, 460)]),
    ('rhosgobel', 'Rhosgobel', 'woodmen', [(1385, 470)]),
    ('central_mirkwood', 'Central Mirkwood', 'mirkwood', [(1480, 520), (1520, 580), (1450, 600)]),
    ('eastern_mirkwood', 'Eastern Mirkwood', 'mirkwood', [(1600, 480), (1610, 540), (1560, 470)]),
    ('dol_guldur', 'Amon Lanc', 'dol_guldur', [(1415, 745), (1400, 720)]),
    ('southern_mirkwood', 'Southern Mirkwood', 'dol_guldur', [(1470, 700), (1520, 760), (1450, 650), (1560, 720)]),
    # ---------------- North-east ----------------
    ('grey_west', 'Western Ered Mithrin', 'ered_mithrin', [(1300, 215), (1380, 220), (1450, 225)]),
    ('grey_east', 'Eastern Ered Mithrin', 'ered_mithrin', [(1500, 205), (1560, 200), (1530, 250)]),
    ('withered_heath', 'Withered Heath', 'ered_mithrin', [(1600, 232), (1640, 238), (1680, 240)]),
    ('erebor', 'Erebor', 'erebor', [(1615, 315)]),
    ('dale', 'Dale', 'dale', [(1630, 340), (1660, 310), (1700, 330)]),
    ('esgaroth', 'Esgaroth', 'dale', [(1600, 380), (1630, 395), (1595, 400)]),
    ('celduin_vale', 'Celduin Vale', 'dale', [(1700, 420), (1760, 460), (1660, 420)]),
    ('dale_north', 'Northern Dale-lands', 'dale', [(1720, 270), (1780, 260)]),
    ('iron_hills', 'Iron Hills', 'iron_hills', [(1850, 325), (1950, 320)]),
    ('iron_hills_south', 'Iron Foothills', 'iron_hills', [(1830, 400), (1800, 380), (1860, 440)]),
    ('carnen_vale', 'Carnen Vale', 'rhun', [(1900, 420), (1920, 500), (1960, 380)]),
    # ---------------- Rhovanion plains ----------------
    ('east_bight', 'East Bight', 'rhovanion', [(1565, 650), (1600, 640)]),
    ('rhovanion_north', 'Northern Rhovanion', 'rhovanion', [(1700, 520), (1780, 540), (1660, 480)]),
    ('rhovanion_east', 'Eastern Rhovanion', 'rhovanion', [(1850, 600), (1850, 680), (1900, 620)]),
    ('rhovanion_south', 'Southern Rhovanion', 'rhovanion', [(1660, 640), (1700, 720), (1650, 800)]),
    ('rhovanion_steppe', 'Rhovanion Steppe', 'rhovanion', [(1800, 760), (1820, 860), (1780, 680)]),
    ('brown_lands', 'Brown Lands', 'brown_lands', [(1480, 900), (1540, 860), (1500, 970), (1440, 960)]),
    ('undeeps', 'The Undeeps', 'brown_lands', [(1400, 880), (1420, 930), (1390, 840)]),
    ('brown_lands_east', 'Eastern Brown Lands', 'brown_lands', [(1600, 920), (1620, 990), (1580, 860)]),
    ('emyn_muil', 'Emyn Muil', 'emyn_muil', [(1450, 1045), (1500, 1060), (1410, 1070)]),
    ('nindalf', 'Nindalf', 'emyn_muil', [(1500, 1150), (1490, 1120)]),
    ('dead_marshes', 'Dead Marshes', 'dagorlad', [(1560, 1095), (1590, 1120), (1540, 1070)]),
    ('dagorlad', 'Dagorlad', 'dagorlad', [(1640, 1070), (1690, 1060), (1620, 1040)]),
    ('dagorlad_north', 'North Dagorlad', 'dagorlad', [(1700, 990), (1660, 960), (1760, 1020)]),
    # ---------------- Rohan ----------------
    ('rohan_westmarch', 'Westmarch of Rohan', 'rohan', [(960, 1105), (1020, 1120), (920, 1095)]),
    ('gap_of_rohan', 'Gap of Rohan', 'rohan', [(1080, 1040), (1110, 1050)]),
    ('westfold', 'Westfold', 'rohan', [(1110, 1095), (1150, 1100), (1085, 1110)]),
    ('westemnet', 'West Emnet', 'rohan', [(1230, 1030), (1220, 1070), (1180, 1010)]),
    ('eastemnet', 'East Emnet', 'rohan', [(1310, 1050), (1340, 1080), (1300, 1015)]),
    ('the_wold', 'The Wold', 'rohan', [(1320, 950), (1350, 910), (1310, 990)]),
    ('folde', 'Folde', 'rohan', [(1215, 1135), (1245, 1140), (1195, 1150)]),
    ('harrowdale', 'Harrowdale', 'rohan', [(1170, 1140), (1160, 1165)]),
    ('eastfold', 'Eastfold', 'rohan', [(1280, 1160), (1310, 1175), (1265, 1180)]),
    ('fenmarch', 'Fenmarch', 'rohan', [(1340, 1180), (1360, 1170)]),
    ('entwash_mouths', 'Mouths of Entwash', 'rohan', [(1390, 1150), (1420, 1165), (1410, 1135)]),
    ('firien_wood', 'Firien Wood', 'rohan', [(1330, 1210), (1352, 1214)]),
    # ---------------- Gondor ----------------
    ('anorien', 'Anórien', 'gondor', [(1420, 1205), (1470, 1205), (1510, 1220), (1390, 1195), (1543, 1223)]),
    ('pelennor', 'Pelennor', 'gondor', [(1535, 1290), (1525, 1275)]),
    ('n_ithilien', 'North Ithilien', 'gondor', [(1580, 1200), (1570, 1160), (1590, 1250)]),
    ('s_ithilien', 'South Ithilien', 'gondor', [(1590, 1380), (1600, 1450), (1575, 1330)]),
    ('lossarnach', 'Lossarnach', 'gondor', [(1490, 1320), (1470, 1300), (1505, 1345)]),
    ('lebennin', 'Lebennin', 'gondor', [(1400, 1400), (1450, 1410), (1370, 1370), (1420, 1360)]),
    ('ethir_anduin', 'Ethir Anduin', 'gondor', [(1360, 1470), (1400, 1490), (1430, 1470)]),
    ('belfalas', 'Belfalas', 'gondor', [(1260, 1450), (1220, 1500), (1300, 1420)]),
    ('dor_en_ernil', 'Dor-en-Ernil', 'gondor', [(1170, 1400), (1200, 1375), (1220, 1420)]),
    ('lamedon', 'Lamedon', 'gondor', [(1265, 1285), (1300, 1300), (1240, 1260)]),
    ('ringlo_vale', 'Ringló Vale', 'gondor', [(1265, 1335), (1300, 1345)]),
    ('morthond', 'Morthond Vale', 'gondor', [(1165, 1280), (1185, 1240), (1170, 1320)]),
    ('pinnath_gelin', 'Pinnath Gelin', 'gondor', [(950, 1305), (1050, 1310)]),
    ('anfalas', 'Anfalas', 'gondor', [(900, 1355), (1000, 1345), (1100, 1340), (880, 1300), (1120, 1310)]),
    ('lefnui_vale', 'Lefnui Vale', 'gondor', [(830, 1290), (900, 1230), (960, 1215)]),
    ('andrast', 'Andrast', 'gondor', [(760, 1300), (700, 1420), (790, 1400), (720, 1250)]),
    ('tolfalas', 'Tolfalas', 'gondor', [(1258, 1535)]),
    ('ered_nimrais_west', 'Western Ered Nimrais', 'gondor', [(920, 1180), (990, 1185), (1040, 1180)]),
    ('dwimorberg', 'Dwimorberg', 'gondor', [(1120, 1190), (1200, 1200)]),
    ('druadan', 'Drúadan Forest', 'druedain', [(1478, 1250)]),
    # ---------------- Harondor / Harad / Khand ----------------
    ('harondor_north', 'Northern Harondor', 'harondor', [(1520, 1540), (1600, 1530), (1460, 1530)]),
    ('harondor_coast', 'Harondor Coast', 'harondor', [(1360, 1600), (1400, 1660), (1340, 1550)]),
    ('harondor_south', 'Southern Harondor', 'harondor', [(1520, 1640), (1620, 1630), (1460, 1600), (1680, 1660)]),
    ('harnen_vale', 'Harnen Vale', 'near_harad', [(1790, 1620), (1775, 1665), (1830, 1650)]),
    ('near_harad', 'Harad Marches', 'near_harad', [(1900, 1620), (2000, 1640), (2080, 1610)]),
    ('khand_north', 'Northern Khand', 'khand', [(2300, 1380), (2350, 1450)]),
    ('khand', 'Central Khand', 'khand', [(2250, 1530), (2350, 1550), (2180, 1580)]),
    ('khand_south', 'Southern Khand', 'khand', [(2200, 1650), (2330, 1650), (2120, 1650)]),
    # ---------------- Mordor ----------------
    ('udun', 'Udûn', 'mordor', [(1640, 1135)]),
    ('gorgoroth', 'Gorgoroth', 'mordor', [(1720, 1250), (1790, 1265), (1750, 1200)]),
    ('lithlad', 'Lithlad', 'mordor', [(2090, 1235), (2160, 1225), (2050, 1215)]),
    ('nurn_west', 'Western Nurn', 'mordor', [(1720, 1370), (1740, 1440), (1700, 1480)]),
    ('nurn', 'Nurn', 'mordor', [(1850, 1400), (1820, 1470), (1900, 1350)]),
    ('eastern_nurn', 'Eastern Nurn', 'mordor', [(2120, 1335), (2170, 1365), (2080, 1385)]),
    ('southern_nurn', 'Southern Nurn', 'mordor', [(1950, 1485), (2020, 1478)]),
    ('morgai', 'The Morgai', 'mordor', [(1628, 1200), (1632, 1235)]),
    ('ephel_north', 'Northern Ephel Dúath', 'mordor', [(1603, 1180), (1606, 1240), (1610, 1140)]),
    ('morgul_vale', 'Imlad Morgul', 'mordor', [(1605, 1292)]),
    ('ephel_south', 'Southern Ephel Dúath', 'mordor', [(1620, 1380), (1630, 1460), (1640, 1530)]),
    ('mountains_of_shadow', 'Mountains of Shadow', 'mordor', [(1760, 1545), (1880, 1555), (1990, 1545)]),
    ('ephel_east', 'Eastern Ephel Dúath', 'mordor', [(2120, 1462), (2180, 1425), (2060, 1500)]),
    ('ered_lithui_west', 'Western Ered Lithui', 'mordor', [(1720, 1120), (1820, 1120), (1700, 1160)]),
    ('ered_lithui_east', 'Eastern Ered Lithui', 'mordor', [(1950, 1120), (2080, 1110), (2200, 1105)]),
    ('ered_lithui_spur', 'Inner Ash Spur', 'mordor', [(1900, 1260), (1960, 1220)]),
    # ---------------- Rhûn ----------------
    ('rhun_north', 'Northern Rhûn', 'rhun', [(2050, 330), (2120, 420), (2000, 260)]),
    ('rhun_northeast', 'North-eastern Rhûn', 'rhun', [(2280, 320), (2350, 250), (2300, 420)]),
    ('rhun_heart', 'Heart of Rhûn', 'rhun', [(2150, 520), (2200, 600), (2100, 470)]),
    ('rhun_east', 'Eastern Rhûn', 'rhun', [(2350, 500), (2360, 620), (2300, 450)]),
    ('rhun_forest', 'Forest of Rhûn', 'rhun', [(2240, 645), (2300, 700)]),
    ('dorwinion', 'Dorwinion', 'rhun', [(2030, 720), (2020, 780)]),
    ('lower_celduin', 'Lower Celduin', 'rhun', [(1960, 640), (2020, 660), (1930, 590)]),
    ('rhun_hills', 'Hills of Rhûn', 'rhun', [(2030, 870), (1980, 880)]),
    ('rhun_east_shore', 'Eastern Shore', 'rhun', [(2340, 800), (2330, 880), (2370, 720)]),
    ('rhun_south_shore', 'Southern Shore', 'rhun', [(2180, 960), (2280, 940), (2120, 920)]),
    ('wainrider_plains', 'Wainrider Plains', 'rhun', [(1850, 960), (1950, 1010), (1800, 1050)]),
    ('rhun_south', 'Southern Rhûn', 'rhun', [(2100, 1040), (2300, 1050), (2200, 980)]),
    ('rhun_southeast', 'South-eastern Rhûn', 'rhun', [(2330, 1200), (2340, 1300), (2280, 1250)]),
    # ---------------- Waters ----------------
    ('northern_sea', 'Northern Sea', 'belegaer', [(100, 100), (200, 70), (70, 160)]),
    ('forlindon_sea', 'Sea of Forlindon', 'belegaer', [(68, 300), (68, 420), (80, 520)]),
    ('harlindon_sea', 'Sea of Harlindon', 'belegaer', [(150, 650), (180, 780), (300, 830), (110, 560)]),
    ('minhiriath_sea', 'Sea of Minhiriath', 'belegaer', [(460, 880), (500, 960), (545, 900), (560, 990)]),
    ('enedwaith_sea', 'Sea of Enedwaith', 'belegaer', [(640, 1060), (630, 1150), (600, 1250)]),
    ('great_sea', 'Great Sea', 'belegaer', [(150, 950), (300, 1050), (150, 1120)]),
    ('belegaer_deeps', 'Belegaer Deeps', 'belegaer', [(150, 1250), (400, 1250), (300, 1350)]),
    ('southern_sea', 'Southern Belegaer', 'belegaer', [(150, 1550), (400, 1600), (300, 1480)]),
    ('andrast_sea', 'Sea of Andrast', 'belegaer', [(600, 1500), (650, 1620), (550, 1430)]),
    ('bay_belfalas_w', 'Western Bay of Belfalas', 'bay_belfalas', [(800, 1500), (850, 1620), (760, 1450)]),
    ('bay_belfalas', 'Bay of Belfalas', 'bay_belfalas', [(950, 1450), (1000, 1560), (1100, 1450), (1050, 1650), (950, 1650)]),
    ('tolfalas_sound', 'Tolfalas Sound', 'bay_belfalas', [(1180, 1560), (1300, 1500), (1200, 1650), (1290, 1640)]),
    ('gulf_lhun', 'Gulf of Lhûn', 'gulf_lhun', [(250, 520), (300, 530), (350, 520), (400, 500)]),
    ('ice_bay', 'Ice Bay of Forochel', 'ice_bay', [(560, 110), (620, 105), (700, 65)]),
    ('nenuial_lake', 'Lake Nenuial', 'nenuial_lake', [(618, 367)]),
    ('long_lake', 'Long Lake', 'long_lake', [(1610, 370)]),
    ('sea_rhun_n', 'Northern Sea of Rhûn', 'sea_rhun', [(2150, 740), (2230, 720)]),
    ('sea_rhun_s', 'Southern Sea of Rhûn', 'sea_rhun', [(2120, 830), (2220, 820)]),
    ('nurnen', 'Sea of Nurnen', 'nurnen', [(1970, 1420)]),
]

PROV = {}
for pid, name, realm, seeds in _P:
    assert pid not in PROV, pid
    assert realm in REALMS, realm
    PROV[pid] = dict(name=name, realm=realm, seeds=seeds)

# Wide empty lands get somewhat larger districts
for pid in ('forodwaith_far', 'forodwaith_east', 'dragon_wastes', 'forodwaith_north', 'rhun_north', 'rhun_northeast',
            'rhun_south', 'rhun_heart', 'rhun_east', 'wainrider_plains', 'rhun_southeast'):
    PROV[pid]['scale'] = 1.6

# Islands and split provinces that may have several parts
for pid in ('anfalas', 'ethir_anduin', 'belfalas'):
    PROV[pid]['multi'] = True

S = (650, 494)  # Three-Farthing Stone

LINES = [
    # Lune: Lindon's eastern border, from its springs to the Gulf
    ('lhun_10', ('river', 10)),
    ('lhun_9', ('river', 9)),
    ('lhun_8', ('river', 8)),
    ('lhun_head', ('hand', [(405, 132), (402, 118), (398, 104)])),
    # Ered Luin
    ('ered_luin_n', ('range_at', (350, 300))),
    ('ered_luin_s', ('range_at', (374, 624), {'minus': [[(447, 470), (540, 470), (540, 556), (452, 556)]]})),
    # Brandywine and the Shire
    ('brandywine_19', ('river', 19)),
    ('brandywine_16', ('river', 16)),
    ('shire_outer', ('hand', [(676, 426), (655, 416), (625, 413), (595, 419), (568, 432), (550, 452), (543, 478),
                              (541, 505), (546, 532), (556, 556), (575, 577), (603, 592), (640, 601), (685, 605), (722, 601)])),
    ('shire_wn', ('hand', [S, (630, 478), (605, 468), (575, 462), (546, 460)])),
    ('shire_ne', ('hand', [S, (660, 476), (667, 462), (671, 448)])),
    ('shire_es', ('hand', [S, (652, 507), (641, 521)])),
    ('shirebourn', ('river', 528)),
    ('shire_ws', ('hand', [S, (630, 512), (605, 532), (578, 550), (558, 561)])),
    # Greyflood, Hoarwell, Bruinen, Glanduin
    ('greyflood_726', ('river', 726)),
    ('greyflood_54', ('river', 54)),
    ('hoarwell', ('river', 727)),
    ('bruinen', ('river', 728)),
    ('glanduin', ('river', 731)),
    ('glanduin_up', ('river', 5494)),
    # Misty Mountains (with the Grey Mountains and the Mountains of Angmar)
    ('hithaeglir', ('range_at', (1230, 500))),
    # Isen and Adorn
    ('isen_low', ('river', 4441)),
    ('isen_up', ('river', 4472)),
    ('adorn', ('river', 4473)),
    # Anduin and its tributaries
    ('anduin_1892', ('river', 1892)),
    ('anduin_1891', ('river', 1891)),
    ('anduin_1890', ('river', 1890)),
    ('anduin_4605', ('river', 4605)),
    ('anduin_4594', ('river', 4594)),
    ('anduin_4593', ('river', 4593)),
    ('anduin_lower', ('anduin_axis',)),
    ('limlight', ('river', 1902)),
    ('entwash_a', ('river', 1788)),
    ('entwash_b', ('river', 4604)),
    ('snowbourn', ('river', 5012)),
    ('mering', ('river', 4937)),
    ('poros', ('river', 4588)),
    ('harnen', ('river', 5118)),
    ('celduin', ('river', 723)),
    ('celduin_low', ('river', 4106)),
    ('carnen', ('river', 4107)),
    ('forest_river', ('river', 817)),
    # Forests that are borders
    ('mirkwood', ('forest_at', (1500, 550))),
    ('fangorn', ('forest_at', (1180, 920))),
    ('lorien_wood', ('forest_at', (1250, 770))),
    ('firien', ('forest_at', (1330, 1210))),
    ('druadan', ('forest_at', (1478, 1250))),
    ('trollshaws', ('forest_at', (1090, 462))),
    ('chetwood', ('forest_at', (796, 482))),
    ('eryn_vorn', ('forest_at', (515, 860))),
    ('rhun_forest', ('forest_at', (2240, 645))),
    # Hills and ranges that are borders
    ('mordor_ranges', ('range_at', (1620, 1400))),
    ('mordor_east', ('hand', [(2246, 1113), (2236, 1170), (2224, 1240), (2218, 1300), (2222, 1360), (2215, 1410)])),
    ('emyn_muil', ('range_at', (1460, 1050))),
    ('iron_hills', ('range_at', (1973, 328))),
    ('erebor', ('range_at', (1615, 315))),
    ('north_downs', ('range_at', (790, 330))),
    ('weather_hills', ('range_at', (895, 450))),
    ('pinnath_gelin', ('range_at', (950, 1310))),
    ('mts_mirkwood', ('range_at', (1520, 415))),
    ('rhun_hills', ('range_at', (2030, 870))),
]

SNAP = {}  # per-line snap tolerance overrides

# District names: a point names whichever district it falls in (earlier entries win).
HINTS = [
    # Lindon, Ered Luin, Forochel
    (472, 505, 'Mithlond'), (246, 482, 'Forlond'), (310, 583, 'Harlond'), (485, 540, 'Elostirion'),
    (110, 175, 'Himling'), (330, 175, 'Ruins of Belegost'), (420, 700, 'Ruins of Nogrod'), (410, 420, "Thorin's Halls"),
    (520, 640, 'Ered Luin Spur'), (205, 205, 'Cape of Forlindon'),
    # The Shire and Buckland
    (553, 500, 'Michel Delving'), (634, 489, 'Hobbiton'), (655, 482, 'Bywater'), (600, 525, 'Tookland'),
    (612, 545, 'Green Hill Country'), (565, 470, 'Little Delving'), (605, 455, 'Needlehole'), (615, 428, 'Long Cleeve'),
    (645, 445, 'Bindbole Wood'), (665, 432, 'Oatbarton'), (668, 462, 'Scary'), (672, 487, 'Frogmorton'),
    (683, 503, 'Stock'), (680, 520, 'The Marish'), (650, 522, 'Woody End'), (590, 565, 'Pincup'), (640, 580, 'Longbottom'),
    (680, 560, 'Southfarthing Marshes'), (697, 497, 'Bucklebury'), (699, 512, 'Crickhollow'), (703, 530, 'Haysend'),
    (530, 520, 'Westmarch'), (545, 545, 'Far Downs'), (732, 620, 'Sarn Ford'),
    # Bree-land, Arthedain, Cardolan
    (786, 497, 'Bree'), (795, 506, 'Staddle and Combe'), (797, 480, 'Archet'), (840, 472, 'Midgewater'),
    (920, 480, 'Weathertop'), (770, 372, "Deadmen's Dike"), (643, 386, 'Annúminas'), (705, 520, 'Withywindle'),
    (760, 505, 'Barrow-downs'), (790, 560, 'Andrath'), (858, 732, 'Tharbad'), (910, 744, 'Swanfleet'),
    (703, 940, 'Lond Daer'), (690, 745, 'Mouths of the Baranduin'), (575, 900, 'Minhiriath Shore'),
    # Rhudaur, Imladris, Angmar
    (1039, 502, 'Last Bridge'), (1105, 442, 'Trollshaws'), (1150, 510, 'Ford of Bruinen'), (1187, 474, 'Rivendell'),
    (1132, 338, 'Ettenmoors'), (958, 170, 'Carn Dûm'), (1076, 265, 'Mount Gram'), (1222, 212, 'Mount Gundabad'),
    (1272, 463, 'High Pass'), (1235, 450, 'Goblin-town'), (1290, 500, 'Eagles\' Eyrie'),
    # Eregion, Moria, Dunland, Enedwaith
    (1100, 696, 'West-gate of Moria'), (1149, 664, 'Redhorn Gate'), (1168, 693, 'Kheled-zâram'), (1031, 733, 'Sirannon'),
    (1015, 690, 'Ost-in-Edhil'), (1155, 640, 'Caradhras'), (1185, 690, 'Zirakzigil'), (1170, 735, 'Fanuidhol'),
    (1000, 915, 'Dunland Woods'), (1045, 1008, 'Isengard'), (1040, 1060, 'Fords of Isen'), (1063, 1035, 'Gap of Rohan'),
    (1075, 950, 'Methedras'),
    # Rohan
    (1082, 1092, "Helm's Deep"), (1075, 1110, 'Thrihyrne'), (1192, 1126, 'Edoras'), (1180, 1136, 'Dunharrow'),
    (1172, 1158, 'Starkhorn'), (1268, 1111, 'Entwade'), (1290, 1170, 'Aldburg'), (1340, 1200, 'Mering Stream'),
    (1365, 1217, 'Halifirien'), (1395, 1140, 'Entwash Delta'),
    # Gondor
    (1190, 1231, 'Erech'), (1200, 1195, 'Dwimorberg'), (1221, 1222, "Tarlang's Neck"), (1278, 1300, 'Calembel'),
    (1292, 1298, 'Ethring'), (1157, 1357, 'Edhellond'), (1157, 1417, 'Dol Amroth'), (1313, 1426, 'Linhir'),
    (1495, 1431, 'Pelargir'), (1534, 1290, 'Minas Tirith'), (1560, 1272, 'Osgiliath'), (1599, 1294, 'Minas Morgul'),
    (1560, 1335, 'Emyn Arnen'), (1543, 1222, 'Cair Andros'), (1592, 1203, 'Henneth Annûn'), (1491, 1322, 'Crossings of Erui'),
    (1591, 1486, 'Crossings of Poros'), (1517, 1247, 'Amon Dîn'), (1480, 1258, 'Stonewain Valley'), (1387, 1222, 'Calenhad'),
    (1415, 1232, 'Min-Rimmon'), (1447, 1244, 'Nardol'), (1479, 1234, 'Eilenach'), (1360, 1470, 'Ethir Anduin'),
    (1258, 1535, 'Tolfalas'), (1513, 1280, 'Mindolluin'), (1470, 1330, 'Lossarnach'), (1250, 1430, 'Belfalas Heights'),
    (1180, 1300, 'Blackroot Vale'), (900, 1360, 'Langstrand'), (735, 1420, 'Ras Morthil'), (840, 1365, 'Mouth of Lefnui'),
    (1543, 1631, 'Harad Road'),
    # Rhovanion
    (1631, 309, 'Erebor'), (1626, 342, 'Dale'), (1612, 365, 'Esgaroth'), (1570, 343, "Thranduil's Halls"),
    (1357, 430, "Beorn's House"), (1322, 435, 'Carrock'), (1354, 479, 'Old Ford'), (1368, 453, 'Rhosgobel'),
    (1415, 745, 'Dol Guldur'), (1320, 630, 'Loeg Ningloron'), (1324, 866, 'Field of Celebrant'), (1384, 900, 'North Undeep'),
    (1420, 945, 'South Undeep'), (1423, 1095, 'Tol Brandir'), (1395, 1105, 'Amon Hen'), (1446, 1074, 'Amon Lhaw'),
    (1413, 1064, 'Sarn Gebir'), (1506, 1153, 'Wetwang'), (1560, 1094, 'Dead Marshes'), (1628, 1075, 'Battle Plain'),
    (1250, 770, 'Caras Galadhon'), (1280, 790, 'Egladil'), (1200, 765, 'Nimrodel'), (1557, 653, 'East Bight'),
    (1480, 375, 'Enchanted River'), (1520, 455, 'Old Forest Road'), (1290, 290, 'Langflood'),
    # Mordor and the east
    (1642, 1105, 'Morannon'), (1668, 1177, 'Isenmouthe'), (1627, 1166, 'Durthang'), (1700, 1210, 'Orodruin'),
    (1765, 1200, 'Barad-dûr'), (1632, 1263, 'Cirith Ungol'), (1650, 1135, 'Udûn'), (2069, 728, 'Dorwinion'),
    (1604, 232, 'Withered Heath'), (2035, 1400, 'Núrnen Shore'),
]

# Manual district seeds for provinces that should not be split automatically.
DISTRICTS = {}

# Ends of the broad lower Anduin (Osgiliath to the head of the Ethir)
ANDUIN_AXIS = ((1565, 1284), (1380, 1488))

# Target sizes in square points (1 pt is about 0.8 miles); water areas are WATER_FACTOR times coarser.
DISTRICT_AREA = 3200
CELL_AREA = 500
WATER_FACTOR = 4

# River names (by path in the map file), used to name districts a river runs through.
RIVERS = {
    8: 'Lhûn', 9: 'Lhûn', 10: 'Lhûn', 16: 'Baranduin', 19: 'Baranduin', 545: 'Water', 546: 'Water', 547: 'Water',
    528: 'Shirebourn', 5566: 'Withywindle', 54: 'Gwathló', 726: 'Gwathló', 727: 'Mitheithel', 728: 'Bruinen',
    729: 'Bruinen', 730: 'Bruinen', 731: 'Glanduin', 5494: 'Sirannon', 4441: 'Isen', 4472: 'Isen', 4473: 'Adorn',
    4442: 'Lefnui', 4477: 'Morthond', 4474: 'Ringló', 4475: 'Ringló', 4476: 'Ciril', 4470: 'Gilrain', 4469: 'Gilrain',
    4471: 'Serni', 4589: 'Sirith', 4590: 'Sirith', 4591: 'Celos', 4592: 'Erui', 4588: 'Poros', 5118: 'Harnen',
    1788: 'Entwash', 4604: 'Entwash', 5012: 'Snowbourn', 4937: 'Mering', 1902: 'Limlight', 1904: 'Silverlode',
    1903: 'Nimrodel', 1899: 'Gladden', 1900: 'Gladden', 1901: 'Gladden', 1892: 'Anduin', 1891: 'Anduin', 1890: 'Anduin',
    4605: 'Anduin', 4594: 'Anduin', 4593: 'Anduin', 5499: 'Langwell', 1894: 'Greylin', 1895: 'Greylin', 1896: 'Rhimdath',
    1897: 'Rhimdath', 1898: 'Rhimdath', 2998: 'Enchanted River', 817: 'Forest River', 816: 'Forest River',
    815: 'River Running', 723: 'Celduin', 4106: 'Celduin', 4107: 'Carnen',
}
