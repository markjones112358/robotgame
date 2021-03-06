# Simplebot by ramk13
# Open source bot with really simple rules
# Feel free to use this as the starting point for a bot
# Please give credit if you do though...

# Moves out of spawn, attacks adjacent enemies
# Chases dying enemies, Attacks towards enemies two steps away
# Flees if in danger, and only moves to safe spots
# No two teammates should move into the same square
# Some teammates may move into stationary teammates

# Uses sets instead of lists for bot data structures
# This makes union/intersection a lot easier (credit to WALL-E for this idea)

# Ways to improve:
#   Instead of using pop() to attack in an arbitrary direction, pick intelligently
#   Instead of just moving to the closest enemies move to the closest weak enemies
#   In some cases it's worth moving into an enemies attack to be aggressive
#   Try to trap enemies bots in spawn
#   Allow bots in trouble to move first and push other bots
#       (requires all moves to be decided on the first act call)
#   When fleeing look for the safest direction

import rg
import numpy as np
import math
import pdb
#import matplotlib.pyplot as plt

turn_number = -1
attack_damage = 10

filenames = [] # For plotting

# set of all spawn locations
spawn = {(7,1),(8,1),(9,1),(10,1),(11,1),(5,2),(6,2),(12,2),(13,2),(3,3),(4,3),(14,3),(15,3),(3,4),(15,4),(2,5),(16,5),(2,6),(16,6),(1,7),(17,7),(1,8),(17,8),(1,9),(17,9),(1,10),(17,10),(1,11),(17,11),(2,12),(16,12),(2,13),(16,13),(3,14),(15,14),(3,15),(4,15),(14,15),(15,15),(5,16),(6,16),(12,16),(13,16),(7,17),(8,17),(9,17),(10,17),(11,17)}
# set of all obstacle locations
obstacle = {(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0),(10,0),(11,0),(12,0),(13,0),(14,0),(15,0),(16,0),(17,0),(18,0),(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(12,1),(13,1),(14,1),(15,1),(16,1),(17,1),(18,1),(0,2),(1,2),(2,2),(3,2),(4,2),(14,2),(15,2),(16,2),(17,2),(18,2),(0,3),(1,3),(2,3),(16,3),(17,3),(18,3),(0,4),(1,4),(2,4),(16,4),(17,4),(18,4),(0,5),(1,5),(17,5),(18,5),(0,6),(1,6),(17,6),(18,6),(0,7),(18,7),(0,8),(18,8),(0,9),(18,9),(0,10),(18,10),(0,11),(18,11),(0,12),(1,12),(17,12),(18,12),(0,13),(1,13),(17,13),(18,13),(0,14),(1,14),(2,14),(16,14),(17,14),(18,14),(0,15),(1,15),(2,15),(16,15),(17,15),(18,15),(0,16),(1,16),(2,16),(3,16),(4,16),(14,16),(15,16),(16,16),(17,16),(18,16),(0,17),(1,17),(2,17),(3,17),(4,17),(5,17),(6,17),(12,17),(13,17),(14,17),(15,17),(16,17),(17,17),(18,17),(0,18),(1,18),(2,18),(3,18),(4,18),(5,18),(6,18),(7,18),(8,18),(9,18),(10,18),(11,18),(12,18),(13,18),(14,18),(15,18),(16,18),(17,18),(18,18)}
center = rg.CENTER_POINT
move_count = 0

board = np.zeros((19,19))

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class Robot:
    def act(self, game):


        # Used to make the code a little more readable
        robots = game.robots

        # Use turn_number to tell if this is the first robot called this turn
        # If so, then clear the list of taken moves
        # The list of taken moves is used to prevent bots from running into each other
        global turn_number, taken_moves, move_count, center, logicfield, movements

        if game.turn != turn_number:
            turn_number = game.turn
            taken_moves = set()



        # If moving save the location we are moving to
        def moving(me,to):
            taken_moves.add(to)
            movements[me[0]][me[1]] = 0
            movements[to[0]][to[1]] = 2
            return ['move', to]

        # If staying save the location that we are at
        def staying(act,loc=center):
            movements[bot[0]][bot[1]] = 2
            taken_moves.add(bot)
            return [act, loc]

        # Function to find bot with the least health
        def minhp (bots):
            return min(bots,key=lambda x:robots[x].hp)


        # Setup basic sets of robots
        me = self.location
        friendlies = set([bot for bot in robots if robots[bot].player_id==self.player_id])
        enemies = set(robots)-friendlies
        adjacent = around(me)


        # Move towards the closest enemies unless leaving spawn or fleeing
        if enemies:
            closest_enemy = mindist(enemies,me)
        else:
            closest_enemy = center

        # adjacent squares with an enemies (enemies is one step away)
        adjacent_enemies = adjacent & enemies

        # adjacent squares with an enemies next to that square
        # excludes square if a teammate is in the square
        # (enemies is two steps away)
        adjacent_enemies2 = set(filter(lambda k:around(k) & enemies, adjacent)) - friendlies

        # set of squares that are safe to move to
        # spawn is bad, and moving into an enemies is bad
        # if an enemies is two steps away it might be attacking towards us
        # excludes teammates to prevent collisions
        safemove = adjacent-adjacent_enemies-adjacent_enemies2-spawn-friendlies-taken_moves
        semisafemove = adjacent-adjacent_enemies-spawn-friendlies-taken_moves
        safemove_withspawn = adjacent-adjacent_enemies-adjacent_enemies2-friendlies-taken_moves

        move = []

        if taken_moves == set():

            for friend in friendlies:
                movements[friend[0]][friend[1]] = 1

            dangerfield = np.zeros((19,19))      # Where the danger is
            supportfield = np.zeros((19,19))     # Where my friends are
            penaltyfield = np.zeros((19,19))     # Where it would be stupid to move
            spawnfield = np.zeros((19,19))       # Where the spawns happen
            innerfield = np.zeros((19,19))       # Slope toward the center
            #logicfield = np.zeros((19,19))       # Result of combining the others
            mask = np.zeros((19,19))             # Where the obsticles are


            # Map out the danger field from the enemies
            for enemy in enemies:
                enemy_health = robots[enemy].hp
                dangerfield[enemy[0]][enemy[1]] += enemy_health * 2
                for distance in [ x+1 for x in range(int(math.ceil(enemy_health/attack_damage)))]:
                    for x,y in squares_dist(enemy, distance):
                        if within_bounds((x,y)):
                            dangerfield[x][y] += int(math.ceil(enemy_health / distance))

            # Map out the spawn field
            for x,y in spawn:
                for a,b in around((x,y)):
                    if within_bounds((a,b)):
                        spawnfield[a][b] += 25
            for x,y in spawn:
                spawnfield[x][y] = 100

            # Map out the innerfield
            for distance in range(1,13):
                for x,y in squares_dist(center, distance):
                    if within_bounds((x,y)):
                        innerfield[x][y] = distance

            # Map out the mask
            for x,y in obstacle:
                mask[x][y] = 100


            fields = [dangerfield, spawnfield, innerfield]
            weight = [0.26, 0.333, 0.8]

            # Normalise fields
            for field in fields:
                field = normalise(field)

            for i, field in enumerate(fields):
                logicfield += field * weight[i]

            # Normalise logicfield
            logicfield = normalise(logicfield)
            logicfield += mask

            #logicfield = blur(logicfield)
            #logicfield += mask
#            filename = 'plot' + str(turn_number) + '.pdf'
#            filenames.append(filename)
#            plot_field(logicfield,filename)


        move = []

        options = move_options(me, logicfield, movements)
        options = sorted(options, key=lambda x: x['logic'])
        for option in options:
            if option['status'] == 'free':
                move = moving(me, option['pos'])
                break;


#        print(options)

#        safest_move = safest_adjacent(me, logicfield, movements)
#        move_gain = 0
#        if safest_move is None:
#            move_gain = 0.0
#            instinct = 'stay'
#        else:
#            move_gain = fieldval(me, logicfield)-fieldval(safest_move, logicfield)
#            instinct = 'move'
#
#        if instinct == 'move':
#            move = moving(me,safest_move)
#        else:
#            move = staying('guard')
#
#        print_field(movements)

#        if safest_move is None:
#            safest_move = list(around(me))[0]
#
#        move = moving(safest_move)
#
#        gain_move = fieldval(me, logicfield)-fieldval(safest_move, logicfield)
#
#        if gain_move <= 0:
#            move = staying('guard')
#        else:
#            move = moving(safest_move)
#
#        next_pos = move[1]
#        next_adj = set(around(next_pos)) - set(me)
#        if next_adj & enemies:
#            move = staying('attack', next_pos)

#        imminent_danger = set(around(me)) & enemies

#        if imminent_danger:
#            move_danger = set(around(next_pos)) & enemies
#            if move_danger:
#                move = staying('attack', imminent_danger.pop())

#        move_count += 1
#        if move_count == (len(friendlies)):
#            #print('Danger')
#            #print_field(dangerfield)
#            #print('Support')
#            #print_field(supportfield)
#            #print('Penalty')
#            #print_field(penaltyfield)
#            #print('Spawn')
#            #print_field(spawnfield)
#            #print('Inner')
#            #print_field(innerfield)
#            #print('Mask')
#            #print_field(mask)
#            #print('The output field')
#            #print_field(logicfield)
#            #filename = 'plot' + str(turn_number) + '.pdf'
#            #filenames.append(filename)
#            #plot_field(logicfield, filename)
#            #move_count = 0
#            #np.savetxt('field.txt', logicfield, fmt='%0.0d',delimiter=',')
#            #print(logicfield)
#            pass
#        if turn_number == 99:
#            combine_pdfs(filenames,'out.pdf')

        return move


