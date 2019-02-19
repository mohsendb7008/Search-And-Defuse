# -*- coding: utf-8 -*-

# python imports
import random
from math import *

# chillin imports
from chillin_client import RealtimeAI

# project imports
from ks.models import (World, Police, Terrorist, Bomb, Position, Constants,
                       ESoundIntensity, ECell, EAgentStatus)
from ks.commands import DefuseBomb, PlantBomb, Move, ECommandDirection

# my imports
from graph import Graph
from sound import Sound

class AI(RealtimeAI):

    def __init__(self, world):
        super(AI, self).__init__(world)
        self.done = False

    def initialize(self):

        self.DIRECTIONS = [
            ECommandDirection.Up,
            ECommandDirection.Right,
            ECommandDirection.Down,
            ECommandDirection.Left,
        ]

        self.DIR_TO_POS = {
            ECommandDirection.Up:    (+0, -1),
            ECommandDirection.Right: (+1, +0),
            ECommandDirection.Down:  (+0, +1),
            ECommandDirection.Left:  (-1, +0),
        }

        self.POS_TO_DIR = {
            (+0, -1): ECommandDirection.Up,
            (+1, +0): ECommandDirection.Right,
            (+0, +1): ECommandDirection.Down,
            (-1, +0): ECommandDirection.Left
        }

        self.BOMBSITES_ECELL = [
            ECell.SmallBombSite,
            ECell.MediumBombSite,
            ECell.LargeBombSite,
            ECell.VastBombSite,
        ]

        self.ESOUND_INTENSITIES = [
            ESoundIntensity.Strong,
            ESoundIntensity.Normal,
            ESoundIntensity.Weak
        ]


        if self.my_side == "Police":

            # Path to be followed for defusing a bomb:
            self.path = {}
            self.police_bomb_site = {}

            # Sorting all bomb site places:
            self.bomb_sites = []
            for i in range(self.world.height):
                for j in range(self.world.width):
                    if self.world.board[i][j] in self.BOMBSITES_ECELL:
                        self.bomb_sites.append((i+j, i, j))
            self.bomb_sites.sort()
            
            print("All map bomb sites:")
            print(self.bomb_sites)

            ''' Testing sound class
            self.world.sound_board = [[[] for j in range(self.world.width)] for i in range(self.world.height)]

            Sound(self.world, self.bomb_sites).fill()

            for i in range(self.world.height):
                for j in range(self.world.width):
                    l = self.world.sound_board[i][j]
                    a, b, c = l.count(ESoundIntensity.Strong), l.count(ESoundIntensity.Normal), l.count(ESoundIntensity.Weak)
                    value, values = a*100+b*10+c, [100, 101, 110, 111]
                    print("G" if value == 111 else "-" if self.world.board[i][j] == ECell.Empty else "-", end=' ')
                print()
            '''

            # Allocating bomb sites to polices:
            self.police_bomb_sites = {}
            P, B = len(self.world.polices), len(self.bomb_sites)
            for police in self.world.polices:
                allocation_len = B//P if B%P==0 else B//P +1 if police.id < B%P else B//P
                allocation_list = [self.bomb_sites[-1]]
                choice_list = [(self._mdistance(t, allocation_list[0]), t[1], t[2]) for t in self.bomb_sites]
                choice_list.sort()
                allocation_list = choice_list[:allocation_len]
                for bombsite in allocation_list:
                    self.bomb_sites.remove((bombsite[1]+bombsite[2], bombsite[1], bombsite[2]))
                self.police_bomb_sites[police.id] = allocation_list
    
            print("Map bomb site to polices allocation:")
            print(self.police_bomb_sites)

            ''' Dummy Allocation :)
            n, m = len(self.bomb_sites), len(self.world.polices)
            index, len_ = 0, ceil(n / m)
            for police_index in range(len(self.world.polices)-2):
                self.police_bomb_sites[self.world.polices[police_index].id] = self.bomb_sites[index: index+len_]
                index += len_
            remaining = self.bomb_sites[index:]
            self.police_bomb_sites[self.world.polices[len(self.world.polices)-2].id] = remaining[:len(remaining)//2]
            self.police_bomb_sites[self.world.polices[len(self.world.polices)-1].id] = remaining[len(remaining)//2:]'''        

            # Each police should has a sound board due to it's allocated bobmsite areas:
            self.police_sound_boards = {}
            # Let' each police circulate around an area that cell inside the area have all sound types
            self.police_circulating_areas = {}
            for police_id, bombsites in self.police_bomb_sites.items():
                print("Agent %d sound board:" %(police_id))
                sound_board = Sound(self.world, [(site[1], site[2]) for site in bombsites]).fill()
                self.police_sound_boards[police_id] = sound_board
                self.police_circulating_areas[police_id] = []
                covered_bombsites = []
                for i in range(self.world.height):
                    for j in range(self.world.width):
                        l = sound_board[i][j]
                        a, b, c, site_pos = 0, 0, 0, None
                        for sound in l:
                            if sound[0] == ESoundIntensity.Strong:
                                a += 1
                                site_pos = sound[1], sound[2]
                            elif sound[0] == ESoundIntensity.Normal:
                                b += 1
                            else:
                                c += 1
                        value, values = a*100+b*10+c, [100, 101, 110, 111]
                        print("G" if value in values else "-" if self.world.board[i][j] == ECell.Empty else "-", end=' ')
                        if self.world.board[i][j] == ECell.Empty and a == 1 and site_pos not in covered_bombsites:
                            self.police_circulating_areas[police_id].append((i+j, i, j))
                            covered_bombsites.append(site_pos)
                    print()
                self.police_circulating_areas[police_id].sort()
                
            print("Polices circulating areas:")
            print(self.police_circulating_areas)

            self.police_circulate_index = {}
            self.police_circulate_iter = {}
            for police_id, areas in self.police_circulating_areas.items():
                self.police_circulate_index[police_id] = len(areas)-1
                self.police_circulate_iter[police_id] = 1

            # Path to be followed by hearing an specific bomb sound:
            self.path2 = {}

            # Path to be followed for circulating between bomb sites:
            self.path3 = {}
            self.current_bomb_sound_list = {}

            self.police_strategies = [
                self.first_police_strategy,
                self.second_police_strategy,
                self.third_police_strategy,
                self.fourth_police_strategy,
                self.fifth_police_strategy,
                self.sixth_police_strategy,
                self.seventh_police_strategy
            ]
        
        else:

            # Path to be followed for planting a bomb:
            self.path = {}
            self.terrorist_bomb_site = {}

            # Making free bombsites list:
            self.free_bomb_sites = []
            for i in range(self.world.height):
                for j in range(self.world.width):
                    if self.world.board[i][j] in self.BOMBSITES_ECELL:
                        self.free_bomb_sites.append((i, j))
            
            print("All map bomb sites:")
            print(self.free_bomb_sites)

            self.terrorist_strategies = [
                self.first_terrorist_strategy,
                self.second_terrorist_strategy,
                self.third_terrorist_strategy,
                self.fourth_terrorist_strategy
            ] 

            '''# Test graph bfs:
            print("* ---------- ---------- ---------- *")
            g = Graph(self.world, (10, 17))
            print(g.bfs((2, 21)))
            print("* ---------- ---------- ---------- *")'''

        '''self.pos_to_index = {}
        self.index_to_pos = {}
        self.not_wall_cells = 0
        for i in range(self.world.height):
            for j in range(self.world.width):
                if self.world.board[i][j] != ECell.Wall:
                    print(i, j)
                    print("--")
                    self.pos_to_index[(i, j)] = self.not_wall_cells
                    self.index_to_pos[self.not_wall_cells] = (i, j)
                    self.not_wall_cells += 1
        #print(self.not_wall_cells)
        #print("----------")

        self.g = Graph(self.not_wall_cells)
        for i in range(self.world.height):
            for j in range(self.world.width):
                if self.world.board[i][j] == ECell.Empty:
                    if self.world.board[i-1][j] != ECell.Wall:
                        self.g.add_edge(self.pos_to_index[(i, j)], self.pos_to_index[(i-1, j)], 1)
                    if self.world.board[i+1][j] != ECell.Wall:
                        self.g.add_edge(self.pos_to_index[(i, j)], self.pos_to_index[(i+1, j)], 1)
                    if self.world.board[i][j-1] != ECell.Wall:
                        self.g.add_edge(self.pos_to_index[(i, j)], self.pos_to_index[(i, j-1)], 1)
                    if self.world.board[i][j+1] != ECell.Wall:
                        self.g.add_edge(self.pos_to_index[(i, j)], self.pos_to_index[(i, j+1)], 1)                    
        self.g.floyd_warshall()'''
                    
    def decide(self):
        '''Stupid strategy
        my_agents = self.world.polices if self.my_side == 'Police' else self.world.terrorists
        for agent in my_agents:
            if agent.status == EAgentStatus.Dead:
                continue

            doing_bomb_operation = agent.defusion_remaining_time != -1 if self.my_side == 'Police' else agent.planting_remaining_time != -1

            if doing_bomb_operation:
                self._agent_print(agent.id, 'Continue Bomb Operation')
                continue

            bombsite_direction = self._find_bombsite_direction(agent)
            if bombsite_direction == None:
                self._agent_print(agent.id, 'Random Move')
                self.move(agent.id, random.choice(self._empty_directions(agent.position)))
            else:
                self._agent_print(agent.id, 'Start Bomb Operation')
                if self.my_side == 'Police':
                    self.defuse(agent.id, bombsite_direction)
                else:
                    self.plant(agent.id, bombsite_direction)'''

        if self.my_side == "Terrorist":
            # Updating free bomb sites:
            for i in range(self.world.height):
                for j in range(self.world.width):
                    if self.world.board[i][j] in self.BOMBSITES_ECELL and (i, j) not in self.free_bomb_sites and not self._has_bomb((i, j)):
                        print("Bombsite (%d, %d) freed." %(i, j))
                        self.free_bomb_sites.append((i, j))
        
        my_agents = self.world.polices if self.my_side == 'Police' else self.world.terrorists

        for agent in my_agents:
            if agent.status is EAgentStatus.Dead:
                continue
            print("Agent %d position (%d, %d)" %(agent.id, agent.position.y, agent.position.x))
            if self.my_side == 'Police':
                for strategy in self.police_strategies:
                    if strategy(agent):
                        break
            else:
                for strategy in self.terrorist_strategies:
                    if strategy(agent):
                        break
        
    
    def plant(self, agent_id, bombsite_direction):
        self.send_command(PlantBomb(id=agent_id, direction=bombsite_direction))

    def _plant(self, agent_id:int, end_pos:Position, start_pos:Position):
        sub = self._sub_pos(end_pos, start_pos)
        if sub in self.POS_TO_DIR:
            self.plant(agent_id, self.POS_TO_DIR[sub])
            return True
        return False

    def defuse(self, agent_id, bombsite_direction):
        self.send_command(DefuseBomb(id=agent_id, direction=bombsite_direction))
    
    def _defuse(self, agent_id:int, end_pos:Position, start_pos:Position):
        sub = self._sub_pos(end_pos, start_pos)
        if sub in self.POS_TO_DIR:
            self.defuse(agent_id, self.POS_TO_DIR[sub])
            return True
        return False

    def move(self, agent_id, move_direction):
        self.send_command(Move(id=agent_id, direction=move_direction))
    
    def _move(self, agent_id:int, end_pos:Position, start_pos:Position):
        sub = self._sub_pos(end_pos, start_pos)
        if sub in self.POS_TO_DIR:
            self.move(agent_id, self.POS_TO_DIR[sub])
            return True
        return False

    
    def first_police_strategy(self, agent:Police):
        # When a police is defusing a bomb, we let him complete his operation:)
        return agent.defusion_remaining_time != -1
    
    def second_police_strategy(self, agent:Police):
         # Let's continue the path:
        if agent.id in self.path:
        # Walk to bomb or defuse it    
            if self.path[agent.id]:
                if self._move(agent.id, Position(self.path[agent.id][0][1], self.path[agent.id][0][0]), agent.position):
                    self.path[agent.id].pop(0)
                else:
                    del self.path[agent.id]
                    return False
            else:
                bomb = self.police_bomb_site[agent.id]
                if self._defuse(agent.id, Position(bomb[1], bomb[0]), agent.position):
                    del self.path[agent.id]
            return True
        return False

    def third_police_strategy(self, agent:Police):
        # Check each police vision to detect a bomb defusion:
        if self.world.bombs:
            for bomb in self.world.bombs:
                if bomb.defuser_id != -1:
                    continue
                distance = self._distance(agent.position, bomb.position)
                if distance <= self.world.constants.police_vision_distance:
                    # Checking wether bomb is going to explode when police arrives
                    g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos())
                    path = g.bfs((bomb.position.y, bomb.position.x))
                    if path is None:
                        return False
                    self.police_bomb_site[agent.id] = (bomb.position.y, bomb.position.x)
                    self.path[agent.id] = path
                    if len(self.path[agent.id]) * 0.5 + self.world.constants.bomb_defusion_time <= bomb.explosion_remaining_time:
                        # Walk to bomb or defuse it    
                        if self.path[agent.id]:
                            if self._move(agent.id, Position(self.path[agent.id][0][1], self.path[agent.id][0][0]), agent.position):
                                self.path[agent.id].pop(0)
                            else:
                                del self.path[agent.id]
                                return False
                        else:
                            if self._defuse(agent.id, bomb.position, agent.position):
                                del self.path[agent.id]
                        if agent.id in self.path2:
                            del self.path2[agent.id] 
                        if agent.id in self.path3:
                            del self.path3[agent.id]
                        return True
                    else:
                        del self.path[agent.id]
        return False
    
    def fourth_police_strategy(self, agent:Police):
        # Let's continue the path2:
        if agent.id in self.path2: 
            if self.path2[agent.id]:
                if self._move(agent.id, Position(self.path2[agent.id][0][1], self.path2[agent.id][0][0]), agent.position):
                    self.path2[agent.id].pop(0)
                    return True
                else:
                    del self.path2[agent.id]
            else:
                del self.path2[agent.id]
        return False
    
    def fifth_police_strategy(self, agent:Police):
        sounds = self.police_sound_boards[agent.id][agent.position.y][agent.position.x]
        a, b, c, strong_pos, normal_pos, weak_pos, dest = 0, 0, 0, None, None, None, None
        for sound in sounds:
            if sound[0] == ESoundIntensity.Strong:
                a += 1
                strong_pos = sound[1], sound[2]
            elif sound[1] == ESoundIntensity.Normal:
                b += 1
                normal_pos = sound[1], sound[2]
            else:
                c += 1
                weak_pos = sound[1], sound[2]
        
        print("Agent %d hearing: %s" %(agent.id, agent.bomb_sounds))
        
        if a==1 and ESoundIntensity.Strong in agent.bomb_sounds:
            print("Strong sound bomb found: (%d, %d)" %(strong_pos[0], strong_pos[1]))
            dest = strong_pos
        elif b==1 and ESoundIntensity.Normal in agent.bomb_sounds:
            print("Normal sound bomb found: (%d, %d)" %(normal_pos[0], normal_pos[1]))
            dest = normal_pos
        elif c==1 and ESoundIntensity.Weak in agent.bomb_sounds:
            print("Weak sound bomb found: (%d, %d)" %(weak_pos[0], weak_pos[1]))
            dest = weak_pos
        if dest is None:
            return False
        
        g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos())
        path = g.bfs(dest, False)
        if path is None:
                return False
        self.path2[agent.id] = path
        if self.path2[agent.id]:
            if self._move(agent.id, Position(self.path2[agent.id][0][1], self.path2[agent.id][0][0]), agent.position):
                self.path2[agent.id].pop(0)
            else:
                del self.path2[agent.id]
                return False
        else:
                del self.path2[agent.id]
                return False
        if agent.id in self.path3:
            del self.path3[agent.id]
        return True
        
    def sixth_police_strategy(self, agent:Police):
        # Let's continue the path3:
        if agent.id in self.path3:
            if not self.path3[agent.id]:
                del self.path3[agent.id]
                return False
            '''
            if agent.id in self.current_bomb_sound_list:
                print("Agent %d is hearing: " %(agent.id), end='')
                print(self.current_bomb_sound_list[agent.id], " --> ", agent.bomb_sounds)
            '''
            # if self._sounds_a_good_way(self.current_bomb_sound_list[agent.id], agent.bomb_sounds):
                # self.current_bomb_sound_list[agent.id] = agent.bomb_sounds
                # print("Agent %d is moving to (%d, %d)" %(agent.id, self.path3[agent.id][0][1], self.path3[agent.id][0][0]))
            if self._move(agent.id, Position(self.path3[agent.id][0][1], self.path3[agent.id][0][0]), agent.position):
                self.path3[agent.id].pop(0)
                return True
            else:
                del self.path3[agent.id]
        return False
        
    def seventh_police_strategy(self, agent:Police):
        # Let's find a path from agent's position to one of its circulating areas:
        '''
        print("Changing agent %d bomb site: (%d, %d) --> " %(agent.id ,self.police_circulating_areas[agent.id][0][1], self.police_circulating_areas[agent.id][0][2]), end='')
        self.police_circulating_areas[agent.id].append(self.police_circulating_areas[agent.id].pop(0))
        print("(%d, %d)" %(self.police_circulating_areas[agent.id][0][1], self.police_circulating_areas[agent.id][0][2]))
        '''
        # self.current_bomb_sound_list[agent.id] = agent.bomb_sounds
        g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos())
        _index = self.police_circulate_index[agent.id]
        dest = self.police_circulating_areas[agent.id][_index]
        if _index in [0, len(self.police_circulating_areas[agent.id])-1]:
            self.police_circulate_iter[agent.id] *= -1
        self.police_circulate_index[agent.id] += self.police_circulate_iter[agent.id]
        print("Source : ", agent.position.y, agent.position.x)
        print("Destination : ", dest[1], dest[2])
        path = g.bfs((dest[1], dest[2]), False)
        if path is None:
            return False
        self.path3[agent.id] = path
        print(self.path3[agent.id])
        if self.path3[agent.id]:
            if self._move(agent.id, Position(self.path3[agent.id][0][1], self.path3[agent.id][0][0]), agent.position):
                self.path3[agent.id].pop(0)
                return True
            else:
                del self.path3[agent.id]
        else:
            del self.path3[agent.id]
        return False
    
    def first_terrorist_strategy(self, agent:Terrorist):
        # If there's a police near, change direction and run(watch out for police inside path)
        black_polices_pos = []
        for police in self.world.polices:
            if self._distance(police.position, agent.position) <= self.world.constants.terrorist_vision_distance:
                black_polices_pos.append((police.position.y, police.position.x))
        if black_polices_pos:
            if agent.id in self.path:
                del self.path[agent.id]
            return self.fourth_terrorist_strategy(agent, black_polices_pos)
        return False

    def second_terrorist_strategy(self, agent:Terrorist):
        # When a terrorist is planting a bomb and there is no police anroud, we let him complete his operation:)
        return agent.planting_remaining_time != -1
    
    def third_terrorist_strategy(self, agent:Terrorist):
        # Continue to your path or plant a bomb
        if agent.id in self.path:
            if self.path[agent.id]:
                try:
                    path = self.path[agent.id]
                    self.move(agent.id, self.POS_TO_DIR[self._sub_pos(Position(path[0][1], path[0][0]), agent.position)])
                    print("Agent %d is moving: (%d, %d) --> (%d, %d)" %(agent.id, agent.position.y, agent.position.x, path[0][0], path[0][1]))
                    path.pop(0)
                except KeyError as e:
                    del self.path[agent.id]
                    return False    
            else:
                try:
                    # Hey terrorist, you are adjacent to a bombsite... Hurry up and plant!
                    dest = self.terrorist_bomb_site[agent.id]
                    self.plant(agent.id, self.POS_TO_DIR[self._sub_pos(Position(dest[1], dest[0]), agent.position)])
                    print("Agent %d is planting a bomb!" %agent.id)
                    del self.terrorist_bomb_site[agent.id]
                    del self.path[agent.id]
                except KeyError as e:
                    del self.path[agent.id]
                    return False
            return True
        return False
    
    def fourth_terrorist_strategy(self, agent:Terrorist, black_polices_pos=[]):

        if agent.id in self.terrorist_bomb_site:
            dest = self.terrorist_bomb_site[agent.id]
        else:
            # Let's find a path to nearest free bomb site for this misreable terrorist:
            bombsite_index, min_distance = -1, float("inf")
            for index, bombsite in enumerate(self.free_bomb_sites):
                distance = self._distance(agent.position, Position(bombsite[1], bombsite[0]))
                if distance < min_distance:
                    bombsite_index, min_distance = index, distance
            if bombsite_index != -1:
                # There exists a bombsite!
                dest = self.free_bomb_sites[bombsite_index]
                print("Terrorist with id %d wants bombsite (%d, %d)" %(agent.id, dest[0], dest[1]))
                self.terrorist_bomb_site[agent.id] = dest
                self.free_bomb_sites.pop(bombsite_index)
    
        black_pos = self._calculate_black_pos()
        black_pos.extend(black_polices_pos)
        g = Graph(self.world, (agent.position.y, agent.position.x), black_pos)
        path = g.bfs(dest)
        if path:
            # Move!
            self.move(agent.id, self.POS_TO_DIR[self._sub_pos(Position(path[0][1], path[0][0]), agent.position)])
            path.pop(0)    
            self.path[agent.id] = path
        else:
            try:
                # Hey terrorist, you are adjacent to a bombsite... Hurry up and plant!
                self.plant(agent.id, self.POS_TO_DIR[self._sub_pos(Position(dest[1], dest[0]), agent.position)])
                del self.terrorist_bomb_site[agent.id]
            except KeyError as e:
                # Your way is closed:) please wait.
                return False
            return True
        return False
    
    def _empty_directions(self, position):
        empty_directions = []
        for direction in self.DIRECTIONS:
            pos = self._sum_pos_tuples((position.x, position.y), self.DIR_TO_POS[direction])
            if self.world.board[pos[1]][pos[0]] == ECell.Empty:
                empty_directions.append(direction)
        return empty_directions

    def _find_bombsite_direction(self, agent):
        for direction in self.DIRECTIONS:
            pos = self._sum_pos_tuples((agent.position.x, agent.position.y), self.DIR_TO_POS[direction])
            if self.world.board[pos[1]][pos[0]] in self.BOMBSITES_ECELL:
                has_bomb = self._has_bomb(pos)
                if (self.my_side == 'Police' and has_bomb) or (self.my_side == 'Terrorist' and not has_bomb):
                    return direction
        return None

    def _has_bomb(self, position):
        for bomb in self.world.bombs:
            if position[1] == bomb.position.x and position[0] == bomb.position.y:
                return True
        return False

    def _sum_pos_tuples(self, t1, t2):
        return (t1[0] + t2[0], t1[1] + t2[1])

    def _agent_print(self, agent_id, text):
        print('Agent[{}]: {}'.format(agent_id, text))

    def _sub_pos(self, t1:Position, t2:Position):
        return (t1.x - t2.x, t1.y - t2.y)

    def _index(self, x:int, y:int):
        return x * self.world.height + y

    def _pos(self, index:int):
        return Position(index // self.world.height, index % self.world.height)

    def _distance(self, first:Position, second:Position):
        return abs(first.x - second.x) + abs(first.y - second.y)

    def _sounds_a_good_way(self, bomb_sounds_before:list, bomb_sounds_after:list):
        if len(bomb_sounds_before) == 0 and len(bomb_sounds_after) == 0:
            return True
        for intensity in self.ESOUND_INTENSITIES:
            before_count = bomb_sounds_before.count(intensity)
            after_count = bomb_sounds_after.count(intensity)
            if before_count != 0 or after_count != 0:
                return before_count <= after_count
        return False
    
    def _calculate_black_pos(self):
        black_pos = []
        my_agents = self.world.polices if self.my_side == 'Police' else self.world.terrorists
        for agent in my_agents:
            if agent.status is not EAgentStatus.Dead:
                black_pos.append((agent.position.y, agent.position.x))
        return black_pos

    def _mdistance(self, t1, t2):
        return abs(t1[1]-t2[1]) + abs(t1[2]-t2[2])

        

