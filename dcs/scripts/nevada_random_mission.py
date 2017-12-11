import dcs
import random
import argparse
import os
import sys
from typing import List, Tuple


class BasicScenario:
    def __init__(self, hide=True):
        self.hide = hide
        self.m = dcs.Mission(terrain=dcs.terrain.Nevada())

        self.red_airports = []  # type: List[dcs.terrain.Airport]
        self.blue_airports = []  # type: List[dcs.terrain.Airport]
        self.setup_airports()

    def dynamic_weather(self, baricsystem: str):
        if baricsystem == "dyncyclone":
            self.m.weather.dynamic_weather(dcs.weather.Weather.BaricSystem.Cyclone, 2)
        elif baricsystem == "dynanti":
            self.m.weather.dynamic_weather(dcs.weather.Weather.BaricSystem.AntiCyclone, 2)
        elif baricsystem == "dynnone":
            self.m.weather.dynamic_weather(dcs.weather.Weather.BaricSystem.None_, 2)
        else:
            self.m.random_weather = True

    def daytime(self, period):
        self.m.random_date()
        self.m.random_daytime(period)

    def setup_airports(self):
        nevada = self.m.terrain  # type: dcs.terrain.Nevada
        self.blue_airports = nevada.default_blue_airports()
        for a in self.blue_airports:
            self.setup_airport(a, "blue", [])

    def setup_airport(self, airport: dcs.terrain.Airport, side: str, air_def_units: List[dcs.unittype.VehicleType]):
        airport.set_coalition(side)
        return airport

    def add_civil_airtraffic(self, planes=(10, 20), helicopters=(0, 10), hidden=True):
        p_count = random.randrange(planes[0], planes[1])
        h_count = random.randrange(helicopters[0], helicopters[1])

        c_count = 1

        def civil_flight(countries, airports):
            country_str = countries[random.randrange(0, len(countries))]
            country = self.m.country(country_str)

            airport = airports[random.randrange(0, len(airports))]

            transports = [x for x in country.planes if x.task_default == dcs.task.Transport]
            ptype = random.choice(transports)

            slots = airport.free_parking_slot(ptype)

            x = random.randrange(dcs.terrain.Caucasus.bounds.bottom+100*1000, dcs.terrain.Caucasus.bounds.top-100*1000)
            y = random.randrange(dcs.terrain.Caucasus.bounds.left+600*1000, dcs.terrain.Caucasus.bounds.right-130*1000)

            pos = dcs.mapping.Point(x, y)
            name = "Civil " + str(c_count)
            rand = random.random()
            if 0.3 < rand < 0.5 and slots:
                pg = self.m.flight_group_from_airport(
                    country, name, ptype, airport,
                    start_type=random.choice([dcs.mission.StartType.Cold, dcs.mission.StartType.Warm]))
                pg.add_runway_waypoint(airport, distance=random.randrange(6000, 8000, 100))
                pg.add_waypoint(pos, random.randrange(5000, 8000, 100), 400)
            elif 0.5 < rand and slots:
                pg = self.m.flight_group_from_airport(country, name, ptype, airport)
                pg.uncontrolled = True
            else:
                bound = dcs.mapping.Rectangle(dcs.terrain.Caucasus.bounds.top-100*1000,
                                              dcs.terrain.Caucasus.bounds.left+200*1000,
                                              dcs.terrain.Caucasus.bounds.bottom+100*1000,
                                              dcs.terrain.Caucasus.bounds.right-130*1000)
                point = bound.random_point()

                pg = self.m.flight_group_inflight(
                    country, name, ptype, point, random.randrange(5000, 8000, 100), 400
                )
                tmp = pg.add_waypoint(dcs.mapping.Point(0, 0), pg.points[0].alt)
                wp = pg.add_runway_waypoint(airport, distance=random.randrange(6000, 8000, 100))
                heading = wp.position.heading_between_point(point)
                tmp.position = wp.position.point_from_heading(heading, 30*1000)
                pg.land_at(airport)
            pg.set_frequency(240)
            return pg

        def heli_transport_flight(countries, airports: List[dcs.terrain.Airport]):
            country_str = countries[random.randrange(0, len(countries))]
            country = self.m.country(country_str)

            transports = [x for x in country.helicopters
                          if x.task_default == dcs.task.Transport]
            htype = random.choice(transports)

            start_airport = random.choice(airports)
            rand = random.random()
            name = "Helicopter Transport " + str(c_count)
            if 0.7 < rand:
                bound = dcs.mapping.Rectangle.from_point(start_airport.position, 100*1000)
                pos = bound.random_point()
                hg = self.m.flight_group_inflight(country, name, htype, pos, random.randrange(800, 1500, 100), 200)
                hg.add_runway_waypoint(start_airport)
                hg.land_at(start_airport)
            elif 0.4 < rand < 0.7:
                hg = self.m.flight_group_from_airport(country, name, htype, start_airport)
                hg.uncontrolled = True
            else:
                dest_airport = None
                while True:
                    dest_airport = airports[random.randrange(0, len(airports))]
                    if dest_airport != start_airport:
                        break

                hg = self.m.flight_group_from_airport(
                    country, name, htype, start_airport, start_type=random.choice(list(dcs.mission.StartType))
                )
                hg.add_runway_waypoint(start_airport)
                hg.add_runway_waypoint(dest_airport)
                hg.land_at(dest_airport)
            return hg

        # red
        # red_countries = [dcs.countries.Russia.name]
        # for i in range(0, int(p_count / 2)):
        #     cf = civil_flight(red_countries, self.red_airports)
        #     cf.hidden = hidden
        #     cf.points[0].tasks.append(dcs.task.SetInvisibleCommand())
        #     c_count += 1
        #
        # for i in range(0, int(h_count / 2)):
        #     hf = heli_transport_flight(red_countries, self.red_airports)
        #     hf.hidden = hidden
        #     hf.points[0].tasks.append(dcs.task.SetInvisibleCommand())
        #     c_count += 1

        # blue
        blue_countries = [dcs.countries.USA.name, dcs.countries.Ukraine.name, dcs.countries.Georgia.name]
        for i in range(0, int(p_count / 2)):
            cf = civil_flight(blue_countries, self.blue_airports)
            cf.hidden = hidden
            cf.points[0].tasks.append(dcs.task.SetInvisibleCommand())
            c_count += 1

        for i in range(0, int(h_count / 2)):
            hf = heli_transport_flight(blue_countries, self.blue_airports)
            hf.hidden = hidden
            hf.points[0].tasks.append(dcs.task.SetInvisibleCommand())
            c_count += 1

    def add_uncontrolled_military_planes(self, airports: List[dcs.terrain.Airport],
                                         planes: List[Tuple[str, dcs.unittype.FlyingType, int]], hidden=True):

        g_idx = 1
        while planes:
            country, ptype, group_size = planes.pop()

            while True:
                airport = random.choice(airports)

                slots = airport.free_parking_slots(ptype)
                if len(slots) >= group_size:
                    break

            c = self.m.country(country)
            pg = self.m.flight_group_from_airport(c, ptype.id + " Flight #" + str(g_idx),
                                                  ptype, airport, parking_slots=slots, group_size=group_size)
            pg.uncontrolled = True
            pg.hidden = hidden
            g_idx += 1

    def place_players(self, start, aircraft_types: List[Tuple[str, str]],
                      airports: List[dcs.terrain.Airport],
                      group_size,
                      maintask,
                      placement_rect=None) -> List[dcs.unitgroup.FlyingGroup]:

        aircraft_groups = []  # type: List[dcs.unitgroup.FlyingGroup]
        name = "Airmaster "
        c = 1
        for _type in aircraft_types:
            country = self.m.country(_type[0])
            aircraft_type = _type[1]
            aircraft_type = dict(dcs.planes.plane_map, **dcs.helicopters.helicopter_map)[aircraft_type]

            airport = airports[random.randrange(0, len(airports))]
            if start == "inflight":
                rp = placement_rect.random_point() if placement_rect else dcs.mapping.Rectangle.from_point(
                        airport.position, 20*1000).random_point()
                altitude = random.randrange(300, 1000, 100) if aircraft_type.helicopter else random.randrange(2000, 5000, 100)
                pg = self.m.flight_group_inflight(
                    country, name + str(c), aircraft_type, rp, altitude,
                    maintask=maintask, group_size=group_size)
            else:
                pg = self.m.flight_group_from_airport(
                    country, name + str(c), aircraft_type, airport,
                    maintask=maintask, start_type=dcs.mission.StartType.from_string(start), group_size=group_size
                )
                pg.add_runway_waypoint(airport)
            aircraft_groups.append(pg)

            for u in pg.units:
                u.set_client()
            c += 1

        if group_size == 1:
            aircraft_groups[0].units[0].set_player()

        return aircraft_groups

    def save(self, filename, stats):
        self.m.save(filename)
        if stats:
            self.m.print_stats(self.m.stats())


class Refueling(BasicScenario):
    def __init__(self, aircraft_types: List[Tuple[str, str]], playercount: int, start: str, unhide):
        super(Refueling, self).__init__()

        self.add_civil_airtraffic(hidden=not unhide)

        nevada = self.m.terrain  # type: dcs.terrain.Nevada

        usa = self.m.country(dcs.countries.USA.name)

        nellis = nevada.nellis_afb()
        tonopah = nevada.tonopah_airport()
        creech = nevada.creech_afb()

        blue_military = [nellis, tonopah]

        planes = [
            (dcs.countries.USA.name, dcs.countries.USA.Plane.F_16C_bl_52d, 4),
            (dcs.countries.USA.name, dcs.countries.USA.Plane.F_15E, 2),
            (dcs.countries.USA.name, dcs.countries.USA.Plane.F_A_18C, 4),
            (dcs.countries.Georgia.name, dcs.countries.Georgia.Plane.Su_25T, 4)
        ]

        self.add_uncontrolled_military_planes(blue_military, planes, False)

        awacs_frequency = 130
        tanker_frequency = 140
        orbit_rect = dcs.mapping.Rectangle(
            int(creech.position.x + 120*1000), int(creech.position.y - 100 * 1000), int(creech.position.x), int(creech.position.y))

        pos, heading, race_dist = Refueling.random_orbit(orbit_rect)
        awacs = self.m.awacs_flight(
            usa,
            "AWACS",
            plane_type=dcs.planes.E_3A,
            airport=None,
            position=pos,
            race_distance=race_dist, heading=heading,
            altitude=random.randrange(4000, 5500, 100), frequency=awacs_frequency)

        self.m.escort_flight(usa, "AWACS Escort", dcs.countries.USA.Plane.F_15E, None, awacs, group_size=2)

        pos, heading, race_dist = Refueling.random_orbit(orbit_rect)
        refuel_net = self.m.refuel_flight(
            usa,
            "Tanker KC_130",
            dcs.planes.KC_130,
            airport=None,
            position=pos,
            race_distance=race_dist, heading=heading,
            altitude=random.randrange(4000, 5500, 100), speed=750, frequency=tanker_frequency)

        pos, heading, race_dist = Refueling.random_orbit(orbit_rect)
        refuel_rod = self.m.refuel_flight(
            usa,
            "Tanker KC_135",
            dcs.planes.KC_135,
            airport=None,
            position=pos,
            race_distance=race_dist, heading=heading,
            altitude=random.randrange(4000, 5500, 100), frequency=tanker_frequency)

        player_groups = self.place_players(start, aircraft_types, blue_military,
                                           placement_rect=orbit_rect,
                                           group_size=playercount, maintask=None)

        if start == "inflight":
            fuel_percent = 0.2
        else:
            fuel_percent = 0.3

        airport = None  # type: dcs.terrain.Airport
        pg = None  # type: dcs.unitgroup.FlyingGroup

        for pg in player_groups:
            airport = self.m.terrain.airport_by_id(pg.points[0].airdrome_id)
            if not airport:
                airport = random.choice(blue_military)

            for u in pg.units:
                u.fuel *= fuel_percent

            if pg.units[0].unit_type in [dcs.planes.A_10C]:
                pg.add_waypoint(refuel_rod.points[1].position, 4000)
            else:
                pg.add_waypoint(refuel_net.points[1].position, 4000)

            pg.add_runway_waypoint(airport)
            pg.land_at(airport)
            pg.load_loadout("Combat Air Patrol")

        goal = dcs.goals.Goal("home and alive")
        goal.rules.append(dcs.condition.UnitAlive(pg.units[0].id))
        tz = self.m.triggers.add_triggerzone(airport.position, 1000, name="home")
        goal.rules.append((dcs.condition.UnitInZone(pg.units[0].id, tz.id)))
        self.m.goals.add_offline(goal)

        self.m.set_sortie_text("Refuel your plane")
        self.m.set_description_text("""Random generated refueling test mission.
{count} {type} are/is prepared for a refueling training mission.""".format(
            count=playercount, type=", ".join([x[1] for x in aircraft_types])))
        self.m.set_description_bluetask_text("""Find your tanker and do a full refuel.
Afterwards land at your designated homebase.

AWACS is reachable on {awacs_freq} Mhz VHF-AM and Tankers are reachable on {tanker_freq} Mhz VHF-AM.
KC-135 Tanker has TACAN 10X activated.""".format(awacs_freq=awacs_frequency, tanker_freq=tanker_frequency))

    @staticmethod
    def random_orbit(rect: dcs.mapping.Rectangle):
        x1 = random.randrange(rect.bottom, rect.top)
        sy = rect.left
        y1 = random.randrange(sy, rect.right)
        heading = 90 if y1 < (sy + (rect.right - sy) / 2) else 270
        heading = random.randrange(heading - 20, heading + 20)
        race_dist = random.randrange(80*1000, 120*1000)
        return dcs.mapping.Point(x1, y1), heading, race_dist


def main():

    types = [
        (dcs.countries.USA.name, dcs.planes.A_10C.id),
        (dcs.countries.USA.name, dcs.planes.M_2000C.id),
        (dcs.countries.USA.name, dcs.helicopters.Ka_50.id),
        (dcs.countries.USA.name, dcs.planes.AV_8B_N_A.id)
    ]
    aircraft_types = [x[1] for x in types]
    parser = argparse.ArgumentParser(description="Nevada random DCS mission generator")

    parser.add_argument("-a", "--aircrafttype", default=types[0][1],
                        choices=aircraft_types,
                        help="Player aircraft type")
    parser.add_argument("-p", "--playercount", default=1, type=int)
    parser.add_argument("-s", "--start", default="inflight", choices=["inflight", "runway", "warm", "cold"])
    parser.add_argument("-t", "--missiontype", default="main", choices=["main", "CAS", "CAP", "refuel"])
    parser.add_argument("-d", "--daytime", choices=["random", "day", "night", "dusk", "dawn", "noon"], default="random")
    parser.add_argument("-w", "--weather", choices=["dynamic", "dyncyclone", "dynanti", "dynone", "clear"], default="dynamic")
    parser.add_argument("-u", "--unhide", action="store_true", default=False, help="Show enemy pre mission")
    parser.add_argument("--show-stats", action="store_true", default=False, help="Show generated missions stats")
    parser.add_argument("-o", "--output", help="Name and path of the generated mission",
                        default=os.path.join(os.path.expanduser("~"), "Saved Games\\DCS.openalpha\\Missions\\random.miz"))

    args = parser.parse_args()
    missiontype = args.missiontype
    if args.aircrafttype in [
        dcs.helicopters.Ka_50.id,
        dcs.planes.A_10C.id,
        dcs.planes.AV_8B_N_A] and args.missiontype == "main":
        missiontype = "CAS"
    if args.aircrafttype in [dcs.planes.M_2000C.id] and args.missiontype == "main":
        missiontype = "CAP"
    if args.aircrafttype == dcs.planes.A_10C.id:
        if args.missiontype not in ["CAS", "refuel"]:
            missiontype = "CAS"

    if missiontype == "refuel":
        supported = [dcs.planes.A_10C.id, dcs.planes.M_2000C.id]
        types = [x for x in types if x[1] in supported] if args.playercount > 1 else [x for x in types if x[1] == args.aircrafttype]
        s = Refueling(types, args.playercount, args.start, args.unhide)
    elif missiontype == "CAS":
        types = types if args.playercount > 1 else [x for x in types if x[1] == args.aircrafttype]
        s = CAS(types, args.playercount, args.start, args.unhide)
    elif missiontype == "CAP":
        supported = [dcs.planes.M_2000C.id, dcs.planes.MiG_21Bis]
        types = [x for x in types if x[1] in supported] if args.playercount > 1 else [x for x in types if x[1] == args.aircrafttype]
        s = CAP(types, args.playercount, args.start, args.unhide)
    else:
        raise NotImplementedError(missiontype + " not implemented")

    s.daytime(args.daytime)
    if args.weather == "dynamic":
        s.dynamic_weather(args.weather)
    s.save(args.output, args.show_stats)

    print("Mission created: " + args.output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
