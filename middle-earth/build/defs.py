"""Realms, provinces and the border lines of Middle-earth at the end of the Third Age.

Coordinates are PDF points (page 2448 x 1728, y down), the same space as the base map.
Every realm and province border is a line in LINES: a river, a road, a mountain foot or
crest, a forest edge, the coast, or (where lore names no feature) a drawn line between
landmarks. Each province is the region its label points fall in. Provinces marked 'free'
(open sea, the empty north and east) may share a region and are split by nearness.
"""

WATER = {'belegaer', 'bay_belfalas', 'gulf_lhun', 'ice_bay', 'nenuial_lake', 'long_lake', 'sea_rhun', 'nurnen'}

REALMS = {
    'lindon': 'Lindon', 'ered_luin': 'Ered Luin', 'forochel': 'Forochel', 'forodwaith': 'Forodwaith',
    'arthedain': 'Arthedain', 'shire': 'The Shire', 'bree': 'Bree-land', 'cardolan': 'Cardolan',
    'rhudaur': 'Rhudaur', 'angmar': 'Angmar', 'imladris': 'Imladris',
    'misty': 'Misty Mountains', 'gundabad': 'Gundabad', 'moria': 'Khazad-dûm', 'eregion': 'Eregion',
    'dunland': 'Dunland', 'enedwaith': 'Enedwaith', 'druwaith': 'Drúwaith Iaur', 'isengard': 'Isengard',
    'fangorn': 'Fangorn', 'lorien': 'Lothlórien', 'anduin_vales': 'Vales of Anduin',
    'woodland_realm': 'Woodland Realm', 'woodmen': 'Woodmen', 'mirkwood': 'Mirkwood', 'dol_guldur': 'Dol Guldur',
    'eotheod': 'Éothéod', 'beornings': 'Beornings',
    'ered_mithrin': 'Ered Mithrin', 'erebor': 'Erebor', 'dale': 'Dale', 'iron_hills': 'Iron Hills',
    'rhovanion': 'Rhovanion', 'brown_lands': 'Brown Lands', 'emyn_muil': 'Emyn Muil', 'dagorlad': 'Dagorlad',
    'rohan': 'Rohan', 'gondor': 'Gondor', 'harondor': 'Harondor', 'mordor': 'Mordor',
    'near_harad': 'Near Harad', 'khand': 'Khand', 'rhun': 'Rhûn', 'dorwinion': 'Dorwinion',
    'belegaer': 'Belegaer', 'bay_belfalas': 'Bay of Belfalas', 'gulf_lhun': 'Gulf of Lhûn',
    'ice_bay': 'Ice Bay of Forochel', 'nenuial_lake': 'Lake Evendim', 'long_lake': 'Long Lake',
    'sea_rhun': 'Sea of Rhûn', 'nurnen': 'Sea of Núrnen',
}

# id, name, realm, label points
_P = [
    # ---------------- Lindon: west of the Blue Mountains and the Lhûn ----------------
    ('forlindon', 'Forlindon', 'lindon', [(160, 400), (220, 200), (210, 300)]),
    ('harlindon', 'Harlindon', 'lindon', [(280, 650), (300, 760)]),
    ('lhun_vale', 'Lhûn Vale', 'lindon', [(440, 300), (425, 420)]),
    ('mithlond', 'Mithlond', 'lindon', [(437, 495), (440, 470)]),
    ('emyn_beraid', 'Emyn Beraid', 'lindon', [(482, 520)]),
    ('himling', 'Himling', 'lindon', [(116, 174)]),
    # ---------------- Ered Luin; north of the Little Lune the land is the Dwarves' (Lindon ends at its inflow) ----------------
    ('ered_luin_north', 'Northern Ered Luin', 'ered_luin', [(330, 300), (430, 95)]),
    ('upper_lhun', 'Upper Lhûn', 'ered_luin', [(430, 220), (400, 240)]),
    ('ered_luin_south', 'Southern Ered Luin', 'ered_luin', [(380, 640), (530, 645)]),
    # ---------------- Forochel: the Lossoth by the Ice Bay ----------------
    ('cape_forochel', 'Cape of Forochel', 'forochel', [(495, 150), (470, 125), (420, 82)]),
    ('forochel', 'Forochel', 'forochel', [(620, 178), (740, 140)]),
    # ---------------- Arthedain: between the Lune and the Brandywine, and north of the Road to the Weather Hills ----------------
    ('emyn_uial', 'Emyn Uial', 'arthedain', [(580, 300), (520, 250), (575, 400)]),
    ('north_arthedain', 'Northern Arthedain', 'arthedain', [(760, 250), (720, 210)]),
    ('north_downs', 'North Downs', 'arthedain', [(800, 340), (820, 400), (760, 360)]),
    ('upper_baranduin', 'Upper Baranduin', 'arthedain', [(730, 420), (720, 380)]),
    ('westmarch', 'Westmarch', 'arthedain', [(505, 470), (510, 530), (505, 430)]),
    ('midgewater', 'Midgewater Marshes', 'arthedain', [(840, 470)]),
    ('weather_hills', 'Weather Hills', 'arthedain', [(870, 455)]),
    ('lower_baranduin', 'Lower Baranduin', 'arthedain', [(560, 600), (650, 625), (700, 615)]),
    ('baranduin_mouths', 'Mouths of Baranduin', 'arthedain', [(560, 700), (520, 700)]),
    # ---------------- The Shire: forty leagues from the Far Downs to the Brandywine Bridge, fifty from the
    # northern moors to the southern marshes; the Farthings meet at the Three-Farthing Stone ----------------
    ('westfarthing', 'Westfarthing', 'shire', [(600, 500), (575, 470), (610, 485)]),
    ('northfarthing', 'Northfarthing', 'shire', [(620, 435), (560, 425), (650, 440)]),
    ('eastfarthing', 'Eastfarthing', 'shire', [(665, 495), (660, 470), (660, 520)]),
    ('southfarthing', 'Southfarthing', 'shire', [(630, 570), (680, 590), (600, 560)]),
    ('buckland', 'Buckland', 'shire', [(686, 500)]),
    # ---------------- Bree-land ----------------
    ('bree', 'Bree-land', 'bree', [(795, 480), (790, 495)]),
    # ---------------- Cardolan: between the Brandywine, the Greyflood and the Great Road ----------------
    ('old_forest', 'Old Forest', 'cardolan', [(712, 520), (705, 495), (725, 535)]),
    ('barrow_downs', 'Barrow-downs', 'cardolan', [(755, 530), (750, 580)]),
    ('south_downs', 'South Downs', 'cardolan', [(850, 550), (950, 560), (920, 620)]),
    ('gwathlo_vale', 'Gwathló Vale', 'cardolan', [(900, 680), (885, 715)]),
    ('minhiriath', 'Minhiriath', 'cardolan', [(700, 760), (620, 840), (780, 700), (700, 880)]),
    ('eryn_vorn', 'Eryn Vorn', 'cardolan', [(506, 868)]),
    # ---------------- Rhudaur: between the Ettenmoors, the Weather Hills and the Misty Mountains, and the Angle ----------------
    ('lone_lands', 'Lone-lands', 'rhudaur', [(960, 440), (990, 400)]),
    ('ettenmoors', 'Ettenmoors', 'rhudaur', [(1000, 335), (1150, 350)]),
    ('coldfells', 'Coldfells', 'rhudaur', [(1120, 400), (1160, 410)]),
    ('trollshaws', 'Trollshaws', 'rhudaur', [(1090, 465), (1070, 445)]),
    ('the_angle', 'The Angle', 'rhudaur', [(1050, 540), (1080, 520)]),
    # ---------------- Imladris ----------------
    ('imladris', 'Imladris', 'imladris', [(1170, 470)]),
    # ---------------- Angmar ----------------
    ('north_angmar', 'Northern Angmar', 'angmar', [(900, 160), (860, 113), (960, 150)]),
    ('angmar_wastes', 'Angmar Wastes', 'angmar', [(870, 250), (950, 270), (840, 240)]),
    ('mountains_of_angmar', 'Mountains of Angmar', 'angmar', [(1060, 175), (1000, 150)]),
    ('mount_gram', 'Mount Gram', 'angmar', [(1060, 300), (1110, 305), (1100, 245), (1060, 240)]),
    # ---------------- Misty Mountains, Gundabad, Khazad-dûm ----------------
    ('gundabad', 'Mount Gundabad', 'gundabad', [(1195, 235)]),
    ('misty_north', 'Northern Misty Mountains', 'misty', [(1230, 330), (1240, 400), (1190, 331)]),
    ('misty_central', 'Central Misty Mountains', 'misty', [(1220, 560), (1230, 500)]),
    ('khazad_dum', 'Khazad-dûm', 'moria', [(1160, 710), (1200, 705)]),
    ('misty_south', 'Southern Misty Mountains', 'misty', [(1120, 830), (1080, 940)]),
    # ---------------- Ered Mithrin and Forodwaith ----------------
    ('grey_west', 'Western Ered Mithrin', 'ered_mithrin', [(1300, 232)]),
    ('grey_east', 'Eastern Ered Mithrin', 'ered_mithrin', [(1430, 235)]),
    ('withered_heath', 'Withered Heath', 'ered_mithrin', [(1560, 240), (1612, 230), (1520, 200)]),
    ('western_forodwaith', 'Western Forodwaith', 'forodwaith', [(880, 70), (950, 90)]),
    ('central_forodwaith', 'Central Forodwaith', 'forodwaith', [(1250, 120), (1100, 100)]),
    ('eastern_forodwaith', 'Eastern Forodwaith', 'forodwaith', [(1750, 150), (1600, 130)]),
    ('far_forodwaith', 'Far Forodwaith', 'forodwaith', [(2200, 150)]),
    # ---------------- The old land of the Éothéod: between the Misty Mountains and the Forest River,
    # down to the meeting of the Greylin and the Langwell (empty since they rode south) ----------------
    ('eotheod', 'Éothéod', 'eotheod', [(1310, 280), (1345, 270)]),
    # ---------------- The Beornings: the upper vales between the mountains and Mirkwood ----------------
    ('upper_vale', 'Upper Vale', 'beornings', [(1285, 330), (1320, 330)]),
    ('carrock', 'Carrock', 'beornings', [(1325, 430), (1300, 420), (1352, 430)]),
    ('western_vale', 'Western Vale', 'beornings', [(1300, 530), (1315, 520)]),
    ('eastern_vale', 'Eastern Vale', 'beornings', [(1370, 530), (1365, 480)]),
    # ---------------- Vales of Anduin (south of the Gladden, largely deserted), Lothlórien, Fangorn ----------------
    ('gladden_fields', 'Gladden Fields', 'anduin_vales', [(1300, 640), (1270, 700), (1330, 620)]),
    ('southern_vale', 'Southern Vale', 'anduin_vales', [(1360, 700), (1340, 780), (1380, 640)]),
    ('field_of_celebrant', 'Field of Celebrant', 'anduin_vales', [(1300, 850), (1250, 830)]),
    ('nimrodel', 'Nimrodel', 'lorien', [(1250, 795), (1215, 785), (1190, 750)]),
    ('egladil', 'Egladil', 'lorien', [(1250, 755), (1270, 765), (1225, 735)]),
    ('fangorn_forest', 'Fangorn Forest', 'fangorn', [(1183, 918), (1220, 900)]),
    # ---------------- Mirkwood ----------------
    # Thranduil holds the north-east beyond the Enchanted River; the Mountains are haunted, the rest is wild;
    # the Woodmen live south of the Old Forest Road near the western eaves
    ('woodland_realm', 'Woodland Realm', 'woodland_realm', [(1570, 380), (1560, 340), (1525, 362)]),
    ('northern_mirkwood', 'Northern Mirkwood', 'mirkwood', [(1420, 330), (1475, 390), (1380, 300), (1470, 266), (1400, 430)]),
    ('mountains_of_mirkwood', 'Mountains of Mirkwood', 'mirkwood', [(1549, 417)]),
    ('woodmen', 'Woodmen-lands', 'woodmen', [(1400, 500), (1420, 600)]),
    ('central_mirkwood', 'Central Mirkwood', 'mirkwood', [(1520, 520), (1580, 440), (1500, 620)]),
    ('amon_lanc', 'Amon Lanc', 'dol_guldur', [(1412, 744), (1440, 700)]),
    ('southern_mirkwood', 'Southern Mirkwood', 'dol_guldur', [(1520, 740), (1500, 790)]),
    ('east_bight', 'East Bight', 'rhovanion', [(1570, 652)]),
    # ---------------- Eregion ----------------
    ('hollin', 'Hollin', 'eregion', [(1050, 650), (1000, 680), (1100, 600), (915, 705)]),
    ('sirannon', 'Sirannon', 'eregion', [(1050, 755), (1080, 735)]),
    # ---------------- Dunland, Enedwaith, Isengard, Drúwaith Iaur ----------------
    ('swanfleet', 'Swanfleet', 'dunland', [(915, 745), (950, 750)]),
    ('northern_dunland', 'Northern Dunland', 'dunland', [(960, 820), (1000, 800), (930, 800)]),
    ('southern_dunland', 'Southern Dunland', 'dunland', [(950, 950), (975, 1015), (940, 900)]),
    ('nan_curunir', 'Nan Curunír', 'isengard', [(1055, 1012)]),
    ('lond_daer', 'Lond Daer', 'enedwaith', [(740, 960), (760, 1050), (745, 920)]),
    ('enedwaith', 'Enedwaith', 'enedwaith', [(870, 900), (900, 1000), (840, 800)]),
    ('druwaith_iaur', 'Drúwaith Iaur', 'druwaith', [(760, 1160), (900, 1130), (900, 1185), (1023, 1165)]),
    # ---------------- Rohan ----------------
    ('wold', 'The Wold', 'rohan', [(1300, 950), (1250, 960), (1350, 970)]),
    ('eastemnet', 'Eastemnet', 'rohan', [(1300, 1070), (1350, 1050), (1295, 1030)]),
    ('westemnet', 'Westemnet', 'rohan', [(1180, 1040), (1120, 1030), (1240, 1070)]),
    # the Westfold: the slopes and fields between Thrihyrne and Edoras; the Folde: around Edoras;
    # Harrowdale: the Snowbourn's dale in the mountains, Edoras at its mouth and Dunharrow at its head
    ('westfold', 'Westfold', 'rohan', [(1120, 1068), (1160, 1090), (1090, 1100), (1120, 1135)]),
    ('west_march', 'West-march', 'rohan', [(950, 1090), (1000, 1100), (1040, 1075)]),
    ('harrowdale', 'Harrowdale', 'rohan', [(1190, 1150), (1200, 1170)]),
    ('folde', 'Folde', 'rohan', [(1240, 1150), (1230, 1110), (1197, 1121)]),
    ('eastfold', 'Eastfold', 'rohan', [(1290, 1160), (1290, 1215), (1235, 1200)]),
    ('fenmarch', 'Fenmarch', 'rohan', [(1345, 1190)]),
    ('entwash_mouths', 'Mouths of Entwash', 'rohan', [(1420, 1160), (1400, 1172)]),
    # ---------------- Gondor ----------------
    ('andrast', 'Andrast', 'druwaith', [(760, 1300), (720, 1400)]),  # never settled by Gondor
    ('pinnath_gelin', 'Pinnath Gelin', 'gondor', [(950, 1310), (950, 1282), (1000, 1225)]),
    ('anfalas', 'Anfalas', 'gondor', [(950, 1345), (1050, 1340), (870, 1360)]),
    ('morthond_vale', 'Morthond Vale', 'gondor', [(1100, 1250), (1150, 1240), (1080, 1190), (1190, 1250)]),
    # Lamedon: the upper Ciril; Ringló Vale: the Ringló's valley (Ethring at its foot);
    # Belfalas: the Prince's fief between the mouths of the Ringló and the Gilrain (Dor-en-Ernil)
    ('lamedon', 'Lamedon', 'gondor', [(1240, 1300), (1180, 1310), (1222, 1250), (1260, 1235)]),
    ('ringlo_vale', 'Ringló Vale', 'gondor', [(1300, 1300), (1320, 1265)]),
    ('belfalas', 'Belfalas', 'gondor', [(1220, 1480), (1320, 1390), (1290, 1420), (1312, 1358), (1200, 1370),
                                        (1170, 1420), (1240, 1360), (1218, 1397)]),
    ('lebennin', 'Lebennin', 'gondor', [(1420, 1400), (1480, 1380), (1400, 1320), (1430, 1290)]),
    ('lossarnach', 'Lossarnach', 'gondor', [(1495, 1305), (1480, 1285), (1525, 1335)]),
    ('pelennor', 'Pelennor', 'gondor', [(1545, 1280), (1527, 1272)]),
    ('anorien', 'Anórien', 'gondor', [(1420, 1200), (1380, 1215), (1450, 1220), (1400, 1250)]),
    ('druadan', 'Drúadan Forest', 'gondor', [(1470, 1240), (1490, 1262)]),
    ('ethir_anduin', 'Ethir Anduin', 'gondor', [(1400, 1480), (1350, 1500)]),
    ('tolfalas', 'Tolfalas', 'gondor', [(1262, 1535)]),
    ('north_ithilien', 'North Ithilien', 'gondor', [(1570, 1200), (1575, 1235), (1600, 1180)]),
    ('south_ithilien', 'South Ithilien', 'gondor', [(1580, 1380), (1560, 1440), (1600, 1340), (1565, 1310)]),
    # ---------------- Harondor ----------------
    ('west_harondor', 'Western Harondor', 'harondor', [(1400, 1550), (1350, 1600), (1450, 1640)]),
    ('east_harondor', 'Eastern Harondor', 'harondor', [(1650, 1620), (1600, 1520), (1700, 1600), (1630, 1510)]),
    # ---------------- Mordor ----------------
    ('imlad_morgul', 'Imlad Morgul', 'mordor', [(1602, 1280), (1615, 1275)]),
    ('udun', 'Udûn', 'mordor', [(1635, 1135)]),
    ('morgai', 'The Morgai', 'mordor', [(1620, 1195)]),
    ('ephel_duath', 'Ephel Dúath', 'mordor', [(1650, 1400)]),
    ('gorgoroth', 'Gorgoroth', 'mordor', [(1740, 1250), (1700, 1200)]),
    ('w_lithui', 'Western Ered Lithui', 'mordor', [(1800, 1160), (1900, 1165), (1880, 1270)]),
    ('e_lithui', 'Eastern Ered Lithui', 'mordor', [(2100, 1130), (2200, 1110)]),
    ('lithlad', 'Lithlad', 'mordor', [(2080, 1220), (2150, 1230)]),
    ('w_nurn', 'Western Nurn', 'mordor', [(1800, 1420), (1760, 1480)]),
    ('e_nurn', 'Eastern Nurn', 'mordor', [(2130, 1350), (2090, 1400)]),
    ('s_ephel', 'Southern Ephel Dúath', 'mordor', [(1800, 1555), (2100, 1500)]),
    # ---------------- Near Harad, Khand ----------------
    ('near_harad', 'Near Harad', 'near_harad', [(1900, 1640), (1800, 1620), (2050, 1620)]),
    ('khand', 'Khand', 'khand', [(2250, 1550), (2300, 1460)]),
    # ---------------- Rhûn (east of the Carnen and of Mordor), Dorwinion ----------------
    ('western_rhun', 'Western Rhûn', 'rhun', [(1950, 450), (2000, 550), (1960, 620)]),
    ('southeast_rhun', 'South-eastern Rhûn', 'rhun', [(2320, 1250), (2300, 1180)]),
    ('southern_rhun', 'Southern Rhûn', 'rhun', [(2100, 1000), (2000, 1050)]),
    ('eastern_rhun', 'Eastern Rhûn', 'rhun', [(2350, 900), (2330, 1000)]),
    ('northern_rhun', 'Northern Rhûn', 'rhun', [(2200, 450), (2300, 550), (2100, 600)]),
    ('forest_of_rhun', 'Forest of Rhûn', 'rhun', [(2290, 650)]),
    ('hills_of_rhun', 'Hills of Rhûn', 'rhun', [(2030, 860)]),
    ('dorwinion', 'Dorwinion', 'dorwinion', [(2030, 720), (2020, 770)]),
    # ---------------- Erebor, Dale, the Iron Hills: the Mountain and the Hills are their own outlines;
    # Brand's realm reached far south and east of Esgaroth, to the Carnen ----------------
    ('erebor', 'Erebor', 'erebor', [(1612, 317)]),
    ('dale', 'Dale-lands', 'dale', [(1640, 350), (1700, 300), (1650, 280)]),
    ('celduin_vale', 'Celduin Vale', 'dale', [(1700, 440), (1800, 480), (1680, 540), (1630, 431)]),
    ('iron_hills', 'Iron Hills', 'iron_hills', [(1900, 330)]),
    # ---------------- Rhovanion, the Brown Lands, Dagorlad, Emyn Muil ----------------
    ('n_rhovanion', 'Northern Rhovanion', 'rhovanion', [(1700, 650), (1800, 650), (1650, 625)]),
    ('s_rhovanion', 'Southern Rhovanion', 'rhovanion', [(1750, 850), (1850, 950), (1700, 1000)]),
    ('n_brown', 'North Brown Lands', 'brown_lands', [(1450, 860), (1550, 850)]),
    ('s_brown', 'South Brown Lands', 'brown_lands', [(1500, 980), (1450, 1000), (1580, 980)]),
    ('dagorlad', 'Dagorlad', 'dagorlad', [(1650, 1070), (1700, 1050)]),
    ('dead_marshes', 'Dead Marshes', 'dagorlad', [(1560, 1100), (1580, 1125)]),
    ('w_emyn_muil', 'Western Emyn Muil', 'emyn_muil', [(1395, 1085)]),
    ('e_emyn_muil', 'Eastern Emyn Muil', 'emyn_muil', [(1470, 1060), (1510, 1025)]),
    ('nindalf', 'Nindalf', 'emyn_muil', [(1490, 1150), (1470, 1130)]),
    # ---------------- Seas and lakes ----------------
    ('ice_bay', 'Ice Bay of Forochel', 'ice_bay', [(620, 90)]),
    ('gulf_of_lhun', 'Gulf of Lhûn', 'gulf_lhun', [(250, 530), (330, 540)]),
    ('n_belegaer', 'Northern Belegaer', 'belegaer', [(150, 110), (90, 300), (300, 75)]),
    ('w_belegaer', 'Western Belegaer', 'belegaer', [(120, 700), (300, 850)]),
    ('belegaer', 'Belegaer', 'belegaer', [(400, 1150), (250, 1050)]),
    ('s_belegaer', 'Southern Belegaer', 'belegaer', [(300, 1550), (550, 1550)]),
    ('belfalas_bay', 'Bay of Belfalas', 'bay_belfalas', [(1050, 1450), (900, 1480), (900, 1620)]),
    ('lake_evendim', 'Lake Evendim', 'nenuial_lake', [(610, 370)]),
    ('long_lake', 'Long Lake', 'long_lake', [(1610, 367)]),
    ('sea_of_rhun', 'Sea of Rhûn', 'sea_rhun', [(2150, 800)]),
    ('sea_of_nurnen', 'Sea of Núrnen', 'nurnen', [(1980, 1420)]),
]

S = (642.3, 502.1)  # the Three-Farthing Stone, on the East Road about five miles south-east of Bywater
N = (642.3, 488.2)  # the Northfarthing's southernmost point, about eleven miles north of the Stone

LINES = [
    # ---------- Lindon, Ered Luin, Forochel ----------
    ('ered_luin_n', ('range_at', (327, 276))),
    ('ered_luin_s', ('range_at', (374, 623))),
    ('tower_neck', ('poly', [(459, 550), (468, 559)])),
    ('mithlond_w', ('poly', [(409, 535), (396, 518)])),
    ('forochel_w', ('poly', [(385, 111), (378, 84)])),
    ('harlindon_e', ('hand', [(432, 749), (430, 790), (428, 828)])),
    ('lhun_10', ('river', 10)),
    ('little_lune', ('river', 12, (360.7, 278.0), (462.9, 275.4))),
    ('lhun_9', ('river', 9)),
    ('lhun_8', ('river', 8)),
    ('mithlond_e', ('hand', [(452, 430), (463, 452), (473, 474), (480, 496)])),
    ('forochel_s', ('hand', [(468, 192), (500, 201), (560, 203), (630, 199), (700, 192), (738, 178), (752, 122)])),
    ('forochel_cape', ('hand', [(516, 136), (519, 168), (521, 205)])),
    ('forochel_e', ('hand', [(778, 103), (765, 84), (767, 44)], 0.5)),
    # ---------- Angmar, Arthedain, Rhudaur ----------
    ('angmar_hills', ('range_at', (859, 113))),
    ('angmar_w', ('hand', [(742, 180), (772, 215), (800, 255), (832, 285), (866, 300), (896, 305)])),
    ('angmar_rhudaur', ('hand', [(896, 305), (932, 312), (972, 311), (1005, 300), (1024, 292)])),
    ('rhudaur_w', ('hand', [(896, 305), (886, 335), (871, 365), (856, 392), (846, 408)])),
    ('weathertop_s', ('poly', [(895, 490), (897, 509)])),
    ('weather_hills', ('range_at', (869, 452))),
    ('evendim_e', ('hand', [(705, 194), (703, 240), (700, 290), (701, 340), (699, 390)])),
    ('brandywine_up', ('river', 19)),
    ('evendim_s', ('hand', [(476, 409), (500, 400), (527.1, 389.1)])),
    ('moors_s', ('hand', [(701, 325), (735, 321), (770, 312), (805, 302), (850, 300), (896, 305)])),
    ('downs_w', ('hand', [(735, 321), (736, 340), (737, 356), (738.5, 368), (743, 375.5), (751, 376.5)])),  # Fornost on the Downs
    ('greenway_n', ('road', 65)),
    ('bree_ring', ('hand', [(777, 456), (797, 451), (816, 457), (828, 472), (829, 488), (827, 503)])),
    ('downs_s', ('hand', [(797, 451), (815, 441), (832, 428)])),
    ('east_road', ('road', 74, (682, 486), (1143, 494))),
    ('westmarch_s', ('hand', [(562.1, 555.6), (540, 566), (505, 573), (440, 581)])),
    ('lhun_vale_s', ('poly', [(402.4, 469.4), (402, 498)])),
    ('mouths_n', ('hand', [(572, 655), (596, 663), (626, 678)])),
    # ---------- The Shire ----------
    ('shire_n', ('foot', (580, 400), (527.1, 389.1), (676.4, 406.0), (590, 418))),  # the foot of the Hills of Evendim
    ('shire_ne', ('hand', [(676.4, 406.0), (683, 409.5), (691, 413.2)], 0.4)),
    ('shire_w', ('hand', [(527.1, 389.1), (528.5, 420), (530, 455), (530.5, 490), (531.7, 515.7)], 0.6)),
    ('far_downs_w', ('foot', (560, 530), (531.7, 515.7), (562.1, 555.6), (535.9, 530.4))),  # the Far Downs' western foot
    ('shire_sw', ('hand', [(562.1, 555.6), (575, 566), (590, 575), (615, 590), (650, 603), (690, 609), (736, 603)])),
    ('farthing_we', ('hand', [S, (645.5, 495.5), N], 0.3)),  # Bywater, at the Pool, is the Westfarthing's
    ('farthing_wn', ('hand', [N, (636, 479), (628, 470), (618, 462), (606, 452), (595, 443), (582, 437), (565, 434),
                             (545, 433), (530, 432)])),
    ('farthing_ne', ('hand', [N, (649, 477), (655, 465), (661, 453), (669.0, 441)])),
    ('farthing_ws', ('hand', [S, (628, 512), (610, 525), (590, 540), (570, 551), (562.1, 555.6)])),
    ('farthing_es', ('hand', [S, (640.5, 513), (637.9, 524.2)], 0.4)),
    ('shirebourn', ('river', 528)),
    ('high_hay', ('hand', [(690, 479), (693, 490), (694.5, 500), (692.5, 509), (688, 516), (683, 521)], 0.4)),
    ('old_forest_e', ('hand', [(737, 479), (741, 500), (739, 522), (728, 543)])),
    # ---------- Cardolan ----------
    ('brandywine_low', ('river', 16)),
    ('sarn_road', ('road', 4478, (735, 604), (781, 627))),
    ('greenway_s', ('road', 4478, (781, 627), (878, 736))),
    ('hoarwell', ('river', 727, (1118, 360), (1007, 623))),
    ('bruinen', ('river', 728)),
    ('bruinen_up', ('river', 730)),
    ('mitheithel', ('river', 726)),
    ('greyflood', ('river', 54)),
    ('tharbad_n', ('hand', [(832, 662), (870, 663), (905, 668), (938, 668)])),
    ('eryn_vorn', ('forest_at', (506, 868))),
    # ---------- Rhudaur, Imladris ----------
    ('ettenmoors_s', ('hand', [(872, 362), (920, 369), (975, 368), (1030, 366), (1080, 369), (1118, 360)])),
    ('coldfells_n', ('hand', [(1118, 360), (1150, 371), (1203, 382)])),
    ('trollshaws_n', ('hand', [(1048, 428), (1095, 431), (1140, 436), (1203, 438)])),
    ('imladris_w', ('hand', [(1141, 435), (1146, 462), (1144, 486)])),
    # ---------- Misty Mountains ----------
    ('misty', ('range_at', (1195, 584))),
    ('gram_cut', ('poly', [(1154, 287), (1178, 315), (1196, 347)])),
    # ---------- Misty Mountains, Gundabad, the Grey Mountains ----------
    ('angmar_arm_cut', ('poly', [(1168, 203), (1158, 222), (1147, 244)])),
    ('grey_cut', ('poly', [(1236, 214), (1237, 233), (1240, 253)])),
    ('gundabad_s', ('poly', [(1146, 258), (1190, 258), (1236, 262)])),
    ('carn_dum_n', ('poly', [(958, 113), (970, 120), (982, 127)])),
    ('carn_dum_s', ('hand', [(783, 232), (840, 214), (900, 204), (950, 192), (986, 176)])),
    ('gram_vale_w', ('hand', [(1000, 183), (1006, 240), (1021, 291)])),
    ('high_pass', ('poly', [(1200, 470), (1235, 468), (1275, 466)])),
    ('redhorn', ('poly', [(1113, 655), (1150, 662), (1216, 668)])),
    ('moria_s', ('poly', [(1090, 778), (1130, 778), (1177, 776)])),
    ('bruinen_src', ('poly', [(1189, 486), (1204, 487)])),
    ('grey_w_cut', ('poly', [(1381, 214.9), (1383, 249.5)])),
    ('heath_cut', ('poly', [(1480, 175), (1480, 211.5), (1482, 249)])),
    ('heath_e', ('hand', [(1626.5, 213), (1639, 228), (1650.5, 242.3)], 0.5)),
    # ---------- Forodwaith ----------
    ('forod_1', ('hand', [(1000, 44), (991, 75), (1003, 105), (1004, 135)])),
    ('forod_2', ('hand', [(1480, 44), (1470, 90), (1486, 130), (1480, 175)])),
    # the waste comes down to the Iron Hills' northern foot
    ('forod_s_w', ('hand', [(1680, 256), (1722, 259), (1765, 263)])),
    ('forod_s_e', ('hand', [(2060, 261.5), (2150, 257), (2250, 252), (2406, 248)])),
    ('forod_3', ('hand', [(2000, 44), (1990, 100), (2008, 150), (1995, 205), (2003, 255), (2000, 299)])),
    # ---------- Vales of Anduin, Lothlórien, Fangorn ----------
    ('eotheod_s', ('hand', [(1288.7, 301.7), (1310, 302), (1332, 301), (1354, 300)])),
    ('forest_river_up', ('river', 817, (1327.0, 250.1), (1389.6, 288.7))),
    ('carrock_n', ('hand', [(1262, 372), (1290, 373), (1305, 375), (1325, 380), (1346, 384)])),
    ('anduin_upper', ('river', 1892, (1305, 375), (1347, 604))),
    ('anduin_middle', ('river', 1891)),
    ('anduin_lower', ('river', 1890)),
    ('forest_road_w', ('road', 4103, (1272, 466), (1450.2, 457.0))),
    ('gladden', ('river', 1899)),
    ('gladden_up', ('river', 1900)),
    ('east_vale_s', ('hand', [(1350, 603), (1372, 604), (1425, 603)])),
    ('silverlode', ('river', 1904, (1181, 718), (1289, 794))),
    ('lorien_n', ('hand', [(1238, 723), (1260, 732), (1285, 738), (1305.7, 737)])),
    ('lorien_s', ('hand', [(1166.3, 800), (1195, 806), (1230, 811), (1265, 811), (1301, 813)])),
    ('limlight', ('river', 1902)),
    ('fangorn', ('forest_at', (1183, 918), {'minus_at': [('range', (1195, 584))]})),
    ('brown_n', ('hand', [(1302, 826), (1340, 816), (1380, 802), (1396, 797)])),
    # ---------- Mirkwood ----------
    ('mirkwood', ('union_at', 'forest', [('forest', (1422, 364)), ('forest', (1486, 636)), ('range', (1549, 417))], 5)),
    ('elf_path', ('road', 5534)),
    ('enchanted_river', ('river', 2998)),
    ('mts_mirkwood', ('range_at', (1549, 417))),
    ('woodmen_e2', ('hand', [(1455, 426), (1446, 470), (1455, 520), (1443, 570), (1449, 620), (1440, 663)])),
    ('narrows', ('hand', [(1415, 663), (1470, 660), (1520, 657), (1552, 655)])),
    ('dol_guldur_e', ('hand', [(1470, 660), (1455, 700), (1465, 745), (1448, 790), (1442, 822)])),
    ('bight_e', ('poly', [(1585, 625), (1598, 650), (1585, 678)])),
    ('thranduil_n', ('poly', [(1526, 351), (1538, 338), (1548, 325)])),
    # ---------- Eregion ----------
    ('glanduin', ('river', 731, (892, 723), (1006, 747))),
    ('glanduin_up', ('river', 5494)),
    ('sirannon', ('river', 731, (1006, 747), (1107, 704))),
    # ---------- Seas ----------
    ('ice_bay_w', ('poly', [(482, 57), (482, 47)])),
    ('gulf_mouth', ('poly', [(186, 537), (203, 565)])),
    ('belfalas_mouth', ('hand', [(650, 1453.8), (651, 1520), (655, 1600), (652, 1692)])),
    # ---------- Dunland, Enedwaith, Isengard, Drúwaith Iaur ----------
    ('greenway_sw', ('road', 4478, (878, 736), (1058, 1058.7))),
    ('isen', ('river', 4472, (1064.7, 1006.4), (889, 1082))),
    ('isen_mouth', ('river', 4441)),
    ('adorn', ('river', 4473)),
    ('curunir_s', ('poly', [(1042.8, 1036.1), (1055, 1020), (1067.8, 1002.1)])),
    ('swanfleet_s', ('hand', [(890.2, 775), (920, 782), (950, 777), (980, 768), (1006, 747)])),
    ('dunland_mid', ('hand', [(914.5, 870), (940, 880), (965, 866), (990, 876), (1014.6, 870)])),
    ('lond_daer_e', ('hand', [(760.9, 830), (775, 880), (785, 950), (790, 1010), (790, 1083.6)])),
    ('white_mts', ('range_at', (1113, 1152))),
    ('west_arm_cut', ('poly', [(980.2, 1171.8), (977.5, 1185), (974.9, 1197.8)])),
    ('lefnui', ('river', 4442, (834, 1371), (974.9, 1197.8))),
    ('andrast_w', ('hand', [(690.5, 1252), (708, 1254), (727.2, 1255.0)])),
    ('andrast_n', ('foot', (760, 1300), (727.2, 1255.0), (832.0, 1235.8), (787.8, 1202.5))),
    ('andrast_e', ('poly', [(832.0, 1235.8), (834, 1245), (836.1, 1254.6)])),
    # ---------- the White Mountains: the crest parts north from south ----------
    ('nimrais_crest', ('crest', (1113, 1152), [(977.5, 1185), (1009, 1184), (1031, 1173), (1063, 1166), (1113, 1152),
                                              (1162, 1168), (1203, 1182), (1220, 1210), (1234, 1222), (1288, 1240),
                                              (1338, 1245), (1360, 1255), (1383, 1263), (1437, 1272), (1487, 1276),
                                              (1520, 1275)])),
    ('adorn_spur', ('poly', [(1049.8, 1138.7), (1052, 1158), (1055, 1176.8)])),
    ('harrowdale_e', ('hand', [(1219.1, 1179.9), (1217, 1191), (1214, 1201)])),
    ('folde_e', ('hand', [(1270, 1129), (1256, 1143), (1243, 1155), (1231, 1168), (1219.1, 1179.9)])),
    ('halifirien', ('poly', [(1339.9, 1223.5), (1340, 1235), (1340, 1247)])),
    ('tail_cut', ('poly', [(1034, 1177.5), (1035, 1192), (1035.9, 1208.2)])),
    ('blackroot_w', ('hand', [(1029.8, 1239.8), (1031, 1260), (1033.5, 1280.1)])),
    ('pinnath_hills', ('range_at', (950, 1310))),
    ('pinnath_w', ('hand', [(858.1, 1326.8), (845, 1340), (837.4, 1358.7)])),
    ('blackroot_s', ('hand', [(1108.5, 1316.5), (1130, 1305), (1155, 1293), (1177, 1281.4)])),
    ('morthond_low', ('river', 4477, (1133, 1302), (1186, 1344))),
    ('tarlang', ('crest', (1113, 1152), [(1220, 1210), (1212, 1238), (1200, 1256), (1200, 1266), (1200.7, 1288.9)])),
    ('ciril_ringlo', ('hand', [(1235.6, 1327.8), (1246, 1318), (1255, 1308), (1264, 1298), (1272, 1287), (1279, 1275),
                               (1284, 1262), (1288, 1250), (1291, 1240)])),  # the watershed of the Ciril and the Ringló
    ('ringlo_low', ('river', 4474)),
    ('ringlo_s', ('hand', [(1236, 1328), (1260, 1338), (1284, 1350), (1300, 1362)])),
    ('belfalas_arm', ('crest', (1113, 1152), [(1360, 1255), (1356, 1298), (1342, 1316), (1324, 1334), (1300, 1362)])),
    ('gilrain', ('river', 4470)),
    ('gilrain_mouth', ('river', 4469)),
    ('gilrain_src', ('poly', [(1388, 1283), (1389, 1278), (1390, 1273.1)])),
    # ---------- Rohan ----------
    ('fords_s', ('poly', [(1058, 1058.7), (1060, 1067), (1062.4, 1075.3)])),
    ('westfold_n', ('hand', [(1063.6, 1045), (1100, 1047), (1140, 1055), (1186, 1073)])),
    ('folde_n', ('hand', [(1186, 1073), (1210, 1081), (1238, 1089), (1267.4, 1094)])),
    ('westfold_e', ('hand', [(1186, 1073), (1187, 1092), (1188, 1108), (1188, 1119), (1186.5, 1127), (1180, 1140),
                             (1172, 1152), (1165, 1161), (1160, 1167)])),
    ('harrowdale_n', ('hand', [(1187.5, 1126), (1196, 1128.3), (1207, 1126)], 0.3)),
    ('entwash', ('river', 1788, (1212.9, 977.9), (1270, 1129))),
    ('entwash_low', ('river', 4604)),
    ('delta_n1', ('river', 4596)),
    ('delta_n2', ('river', 4597)),
    ('delta_s1', ('river', 4600)),
    ('delta_s2', ('river', 4602)),
    ('mering', ('river', 4937)),
    ('fenmarch_w', ('hand', [(1318, 1152), (1310, 1172), (1317, 1192), (1312, 1210)])),
    ('wold_s', ('hand', [(1240, 990), (1280, 1004), (1330, 996), (1375, 1009), (1415.3, 1005)])),
    ('emyn_muil', ('range_at', (1470, 1060))),
    ('anduin_rauros', ('river', 4594)),
    ('anduin_cair', ('river', 4593, (1563, 1285), (1516, 1205))),
    # ---------- Gondor east of the mountains ----------
    ('rammas', ('hand', [(1563, 1250), (1548, 1252), (1535, 1257), (1524.6, 1262.5), (1520, 1275), (1514.1, 1287.4),
                         (1525, 1298), (1538, 1305), (1547, 1307)])),
    ('sirith_up', ('river', 4590)),
    ('sirith_src', ('poly', [(1474, 1286), (1475, 1280), (1476, 1273)])),
    ('lossarnach_s', ('hand', [(1458, 1344), (1475, 1337), (1493, 1326), (1510.7, 1315.5)])),
    ('erui_low', ('river', 4592, (1510.7, 1315.5), (1542, 1362))),
    ('anduin_axis', ('axis', [(1563, 1285), (1552, 1300), (1536, 1320), (1542, 1350), (1543, 1370), (1535, 1400),
                              (1515, 1428)])),
    ('ethir_n', ('river', 3)),
    ('ethir_s', ('river', 4)),
    ('druadan_wood', ('forest_at', (1470, 1240))),
    ('ithilien_n', ('hand', [(1516, 1205), (1535, 1182), (1558, 1172), (1572, 1152), (1588.1, 1140.3)])),
    ('morgul_road', ('road', 4910, (1567.4, 1278.9), (1593.5, 1276.6))),
    ('morgul_mouth', ('poly', [(1591.9, 1262.1), (1593.5, 1278), (1596.1, 1295.8)])),
    ('morgul_n', ('hand', [(1600, 1263.7), (1612, 1258), (1625.8, 1255)])),
    ('morgul_s', ('hand', [(1604.5, 1294.8), (1620, 1299), (1636, 1300)])),
    ('poros', ('river', 4588)),
    ('poros_src', ('poly', [(1606.3, 1457.0), (1625, 1457), (1642.8, 1457)])),
    ('harad_road', ('road', 4479, (1572.9, 1471.2), (1548, 1690))),
    ('harnen', ('river', 5118)),
    # ---------- Mordor ----------
    ('mordor_mts', ('range_at', (1640, 1400))),
    ('ephel_crest', ('crest', (1640, 1400), [(1611.3, 1115.7), (1613.7, 1146), (1610.3, 1180), (1609, 1201),
                                             (1613.7, 1231), (1620.6, 1242), (1634, 1260), (1636.6, 1281),
                                             (1635.4, 1309), (1638.9, 1343), (1642.8, 1365), (1645.4, 1391),
                                             (1642.8, 1432), (1642.8, 1468), (1650.5, 1489), (1653.1, 1530),
                                             (1642.8, 1540), (1637.7, 1556), (1630.9, 1568.5)])),
    ('udun_w', ('hand', [(1611.3, 1115.7), (1622, 1135), (1633, 1150), (1642.7, 1162.8)])),
    ('udun_e', ('hand', [(1640.0, 1110.3), (1648, 1130), (1654, 1146), (1659.8, 1159.9)])),
    ('morgai_s', ('poly', [(1630.9, 1268), (1645, 1269), (1659.7, 1270)])),
    ('ephel_corner', ('poly', [(1653.1, 1530), (1670, 1515), (1685.7, 1502.3)])),
    ('gorgoroth_s', ('hand', [(1836, 1322), (1800, 1335), (1758.6, 1350)])),
    ('lithui_cut', ('poly', [(2000, 1125.2), (2012, 1160), (2025, 1190.3)])),
    ('lithlad_s', ('hand', [(1957, 1262), (2000, 1260), (2050, 1258), (2110, 1262), (2170, 1265), (2229, 1268)])),
    ('nurn_n', ('river', 5122)),
    ('nurn_s', ('river', 5123)),
    ('mordor_east', ('hand', [(2256.3, 1112.3), (2245, 1170), (2232, 1240), (2226, 1300), (2232, 1360), (2240.5, 1420.3)])),
    # ---------- Near Harad, Khand, Rhûn ----------
    ('harad_khand', ('hand', [(2070, 1554.8), (2100, 1590), (2105, 1630), (2135, 1660), (2150, 1692)])),
    ('khand_n', ('hand', [(2241.1, 1422.7), (2290, 1440), (2340, 1428), (2406, 1445)])),
    ('rhun_khand', ('hand', [(2256.3, 1112.3), (2300, 1128), (2345, 1115), (2406, 1132)])),
    ('rhun_se', ('hand', [(2235.3, 870), (2255, 920), (2240, 985), (2262, 1050), (2256.3, 1112.3)])),
    ('rhun_ne', ('hand', [(2326.5, 710.1), (2360, 712), (2406, 712)])),
    ('rhun_w', ('hand', [(1990, 932.3), (1975, 980), (1988, 1030), (1972, 1085), (1975, 1133.5)])),
    ('dorwinion_s', ('poly', [(2068.0, 850), (2074, 850), (2080.3, 850)])),
    ('hills_rhun', ('range_at', (2030, 860))),
    ('rhun_forest', ('forest_at', (2290, 650), {'to_water': 7})),
    # ---------- Erebor, Dale, the Iron Hills ----------
    ('erebor', ('range_at', (1612, 317))),
    ('eotheod_e', ('poly', [(1545.2, 289.6), (1545.1, 275), (1545, 259.7)])),
    ('thranduil_ne', ('hand', [(1547.5, 326), (1562, 333), (1580, 336), (1598, 342), (1613.4, 349.2)])),
    ('thranduil_se', ('poly', [(1603.2, 418.8), (1605.5, 416.5), (1607.5, 413.9)])),
    ('dale_s', ('hand', [(1615.5, 368), (1670, 398), (1740, 408), (1800, 438), (1850, 440), (1895, 450)])),
    ('dale_e', ('hand', [(1765, 263), (1758, 285), (1761, 305), (1762.1, 324.3)])),
    ('iron_hills', ('range_at', (1900, 330))),
    ('ih_e', ('hand', [(2060, 261.5), (2066, 285), (2062, 308), (2057.6, 327.4)])),
    ('ih_e2', ('hand', [(2057.6, 327.4), (2070, 380), (2062, 440), (2075, 500), (2066, 560), (2072, 610), (2052, 661)])),
    # the Celduin is the forest's edge from the Long Lake down; below, Dale holds both banks
    ('celduin_edge', ('river', 723, (1606.4, 382.2), (1621.4, 438.7))),
    ('dale_south', ('hand', [(1596, 570), (1650, 583), (1720, 591), (1790, 594), (1855, 594), (1899.4, 570.9)])),
    ('celduin_low', ('river', 4106)),
    ('carnen', ('river', 4107)),
    # ---------- Rhovanion, the Brown Lands, Dagorlad ----------
    ('rhov_e', ('hand', [(1990, 670), (1981, 702), (1990, 740), (1983, 775), (1990, 812.4)])),
    ('rhov_mid', ('hand', [(1627.1, 700), (1700, 722), (1780, 718), (1860, 738), (1930, 733), (1990, 740)])),
    ('brown_e', ('hand', [(1600, 761.3), (1615, 815), (1607, 870), (1625, 925), (1632, 950), (1628, 985), (1640, 1020)])),
    ('brown_mid', ('hand', [(1397.4, 948), (1450, 958), (1510, 944), (1570, 956), (1632, 950)])),
    ('dead_n', ('hand', [(1543.4, 1022.5), (1570, 1030), (1598, 1035)])),
    ('dead_e', ('hand', [(1598, 1035), (1601, 1060), (1606, 1090), (1611.3, 1115.7)])),
    ('dagorlad_n', ('hand', [(1598, 1035), (1640, 1020), (1690, 1010), (1735, 1005)])),
    ('dagorlad_e', ('hand', [(1735, 1005), (1728, 1045), (1742, 1090), (1738, 1139.3)])),
    ('nindalf_e', ('hand', [(1490, 1092), (1505, 1130), (1522, 1160), (1545, 1179)])),
]

SNAP = {}


PROV = {}
for pid, name, realm, seeds in _P:
    assert pid not in PROV, pid
    assert realm in REALMS, realm
    PROV[pid] = dict(name=name, realm=realm, seeds=seeds)

FREE = {'n_belegaer', 'w_belegaer', 'belegaer', 's_belegaer'}
for pid in FREE:
    PROV[pid]['free'] = True

# Towns, cities and fortresses the base map marks: each is a small disc of its own at district level.
# (name, centre of the map's symbol, kind[, provinces the disc may take in, the first owning it])
# A disc stays inside the province its centre is in, unless the entry names provinces.
CITIES = [
    ('Grey Havens', (402.5, 511.0), 'Haven', ['mithlond', 'gulf_of_lhun']), ('Weathertop', (884.0, 487.0), 'Ruins'), ('Michel Delving', (580.0, 502.4), 'Town'),
    ('Annúminas', (620.8, 387.7), 'Ruins'), ('Hobbiton', (634.8, 489.9), 'Village'),
    ('Bucklebury', (688.5, 501.9), 'Village'), ('Bree', (781.5, 500.4), 'Town'), ('Fornost', (750.3, 369.0), 'Ruins'),
    ('Tharbad', (880.0, 733.4), 'Ruins', ['gwathlo_vale', 'minhiriath', 'swanfleet', 'enedwaith']),
    ('Lond Daer Enedh', (694.4, 940.1), 'Ruins'), ('Carn Dûm', (953.1, 167.1), 'Ruins', ['north_angmar', 'mountains_of_angmar']),
    ('Rivendell', (1169.5, 475.4), 'Refuge'), ('Isengard', (1051.0, 990.0), 'Fortress'),
    ("Helm's Deep", (1086.5, 1080.9), 'Fortress'), ('Edoras', (1196.4, 1123.1), 'Town'),
    ('Dunharrow', (1193.0, 1137.1), 'Refuge'), ('Erech', (1186.4, 1220.5), 'Town'),
    ('Calembel', (1254.1, 1287.9), 'Town'), ('Ethring', (1281.4, 1297.9), 'Town'),
    ('Edhellond', (1181.7, 1355.3), 'Ruins', ['belfalas', 'anfalas']), ('Dol Amroth', (1146.6, 1402.6), 'City'),
    ('Linhir', (1328.1, 1423.9), 'Town'), ('Pelargir', (1481.0, 1439.8), 'City'),
    ('Minas Tirith', (1538.0, 1276.0), 'City'), ('Cair Andros', (1538.0, 1221.0), 'Fortress'),
    ('Osgiliath', (1563.0, 1279.1), 'Ruins', ['pelennor', 'north_ithilien', 'south_ithilien']),
    ('Minas Morgul', (1606.0, 1274.0), 'Fortress'), ('Cirith Ungol', (1635.7, 1267.5), 'Tower', ['morgai', 'ephel_duath', 'imlad_morgul']),
    ('Morannon', (1627.0, 1117.4), 'Gate', ['udun', 'dagorlad']), ('Durthang', (1619.7, 1165.7), 'Fortress'),
    ('Isenmouthe', (1655.0, 1159.9), 'Gate', ['udun', 'gorgoroth', 'w_lithui']), ('Barad-dûr', (1762.5, 1195.5), 'Fortress'),
    ('Caras Galadhon', (1268.0, 775.0), 'City'), ('Dol Guldur', (1414.0, 744.0), 'Fortress'),
    ("Beorn's House", (1351.3, 435.0), 'House'),
    ('Rhosgobel', (1385.3, 442.7), 'House', ['carrock', 'northern_mirkwood']),
    ('Halls of Thranduil', (1561.8, 354.2), 'Halls'), ('Dale', (1614.5, 340.1), 'City'),
    ('Esgaroth', (1611.4, 360.4), 'Town', ['dale', 'long_lake']),
]
CITY_RADIUS = 6.0
# a city whose map symbol is bigger than a dot gets a disc that shows round the symbol
CITY_RADII = {'Minas Tirith': 14, 'Minas Morgul': 14, 'Barad-dûr': 14, 'Dol Guldur': 14, 'Isengard': 13,
              'Dol Amroth': 9.5, 'Grey Havens': 9, 'Fornost': 9, "Beorn's House": 9, 'Annúminas': 8.5,
              'Carn Dûm': 8.5, 'Edhellond': 7.5}

# District names: a point names whichever district it falls in (earlier entries win). Places from the books,
# set where the base map letters them or where the books put them; a city's own name belongs to its disc.
HINTS = [
    # Lindon, Ered Luin
    (246, 482, 'Forlond'), (310, 583, 'Harlond'), (205, 205, 'Cape of Forlindon'),
    (330, 175, 'Ruins of Belegost'), (420, 700, 'Ruins of Nogrod'), (410, 420, "Thorin's Halls"),
    # The Shire: the Westfarthing
    (641, 496, 'Bywater'), (612, 503, 'Waymeet'), (605, 525, 'Tookland'), (594, 469, 'Rushock Bog'),
    (586, 449, 'Needlehole'), (556, 472, 'Little Delving'), (583, 512, 'White Downs'), (548, 528, 'Far Downs'),
    # the Northfarthing, the Eastfarthing, the Southfarthing, Buckland
    (640, 430, 'Oatbarton'), (655, 452, 'Bindbole Wood'), (580, 420, 'North Moors'),
    (662, 463, 'Scary'), (656, 494, 'Frogmorton'), (678, 506, 'The Marish'), (652, 521, 'Woody End'),
    (628, 527, 'Green Hill Country'), (590, 566, 'Pincup'), (640, 585, 'Longbottom'), (703, 551, 'Overbourn Marshes'),
    (688, 489, 'Newbury'), (686, 514, 'Haysend'),
    # Bree-land, Arthedain, Cardolan
    (792, 499, 'Staddle'), (806, 497, 'Combe'), (814, 476, 'Archet'),
    (790, 560, 'Andrath'), (716, 610, 'Sarn Ford'),
    # Rhudaur, Angmar, the Misty Mountains
    (1039, 502, 'Last Bridge'), (1150, 510, 'Ford of Bruinen'), (1135, 345, 'Ettendales'),
    (1250, 462, 'High Pass'), (1235, 450, 'Goblin-town'), (1258, 438, "Eagles' Eyrie"),
    # Eregion, Moria, Dunland, Enedwaith
    (1100, 696, 'West-gate of Moria'), (1149, 664, 'Redhorn Gate'), (1168, 693, 'Kheled-zâram'),
    (1028, 722, 'Ost-in-Edhil'), (1155, 640, 'Caradhras'), (1185, 690, 'Zirakzigil'), (1170, 735, 'Fanuidhol'),
    (1040, 1060, 'Fords of Isen'), (1063, 1035, 'Gap of Rohan'), (1075, 950, 'Methedras'),
    # Rohan
    (1088, 1066, 'Deeping-coomb'), (1075, 1110, 'Thrihyrne'),
    (1290, 1170, 'Aldburg'), (1340, 1200, 'Mering Stream'), (1365, 1217, 'Halifirien'),
    # Gondor
    (1200, 1195, 'Dwimorberg'), (1221, 1222, "Tarlang's Neck"), (1300, 1395, 'Dor-en-Ernil'),
    (1560, 1335, 'Emyn Arnen'), (1592, 1203, 'Henneth Annûn'), (1568, 1243, 'Field of Cormallen'),
    (1491, 1322, 'Crossings of Erui'), (1591, 1486, 'Crossings of Poros'), (1517, 1247, 'Amon Dîn'),
    (1480, 1258, 'Stonewain Valley'), (1387, 1222, 'Calenhad'), (1415, 1232, 'Min-Rimmon'), (1447, 1244, 'Nardol'),
    (1479, 1234, 'Eilenach'), (1513, 1280, 'Mindolluin'), (840, 1365, 'Mouth of Lefnui'), (1543, 1631, 'Harad Road'),
    # Rhovanion
    (1282, 286, 'Framsburg'), (1322, 438, 'Ford of Carrock'), (1354, 479, 'Old Ford'),
    (1320, 630, 'Loeg Ningloron'), (1384, 900, 'North Undeep'), (1420, 945, 'South Undeep'),
    (1423, 1095, 'Tol Brandir'), (1446, 1074, 'Amon Lhaw'), (1413, 1064, 'Sarn Gebir'),
    (1480, 375, 'Enchanted River'), (1520, 455, 'Old Forest Road'),
    # Mordor
    (1700, 1210, 'Orodruin'),
]


# Woods and hills with names of their own: a district mostly inside one is named after it
# (or '<province> Woods/Highlands' when the feature spreads over several provinces).
FEATURE_NAMES = [
    ('forest', (1470, 1240), 'Drúadan Forest'), ('forest', (1315, 1205), 'Firien Wood'),
    ('forest', (1250, 770), 'Golden Wood'), ('forest', (1183, 918), 'Fangorn'), ('forest', (1090, 465), 'Trollshaws'),
    ('forest', (795, 482), 'Chetwood'), ('forest', (695.6, 520), 'Old Forest'), ('forest', (650, 522), 'Woody End'),
    ('forest', (506, 868), 'Eryn Vorn'), ('forest', (2290, 650), 'Forest of Rhûn'),
    ('range', (1113, 1152), 'White Mountains'), ('range', (327, 276), 'Blue Mountains'),
    ('range', (374, 623), 'Blue Mountains'), ('range', (2030, 860), 'Hills of Rhûn'),
    ('range', (1900, 330), 'Iron Hills'), ('range', (1470, 1060), 'Emyn Muil'), ('range', (950, 1310), 'Pinnath Gelin'),
    ('range', (800, 340), 'North Downs'), ('range', (869, 452), 'Weather Hills'), ('range', (1549, 417), 'Mountains of Mirkwood'),
    ('range', (545, 520), 'Far Downs'), ('range', (760, 1300), 'Andrast'),
]

# Seas (not lakes): their districts are named after the coast they lie off,
# or by SEA_NAMES where '<province> Waters' would read badly.
SEA_NAMES = {'baranduin_mouths': 'Baranduin Estuary', 'cape_forochel': 'Waters of the Cape', 'ethir_anduin': 'Ethir Shoals',
             'mithlond': 'Firth of Lhûn', 'lond_daer': 'Lond Daer Roads', 'andrast': 'Andrast Waters'}
SEAS = {'belegaer', 'bay_belfalas', 'gulf_lhun', 'ice_bay'}

# Manual district seeds for provinces that should not be split automatically.
DISTRICTS = {}

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
