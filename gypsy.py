

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
#   Instead of just moving to the closest enemy move to the closest weak enemy
#   In some cases it's worth moving into an enemy attack to be aggressive
#   Try to trap enemy bots in spawn
#   Allow bots in trouble to move first and push other bots
#       (requires all moves to be decided on the first act call)
#   When fleeing look for the safest direction

import rg

turn_number = -1
attack_damage = 10

# set of all spawn locations
spawn = {(7,1),(8,1),(9,1),(10,1),(11,1),(5,2),(6,2),(12,2),(13,2),(3,3),(4,3),(14,3),(15,3),(3,4),(15,4),(2,5),(16,5),(2,6),(16,6),(1,7),(17,7),(1,8),(17,8),(1,9),(17,9),(1,10),(17,10),(1,11),(17,11),(2,12),(16,12),(2,13),(16,13),(3,14),(15,14),(3,15),(4,15),(14,15),(15,15),(5,16),(6,16),(12,16),(13,16),(7,17),(8,17),(9,17),(10,17),(11,17)}
# set of all obstacle locations
obstacle = {(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0),(7,0),(8,0),(9,0),(10,0),(11,0),(12,0),(13,0),(14,0),(15,0),(16,0),(17,0),(18,0),(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(12,1),(13,1),(14,1),(15,1),(16,1),(17,1),(18,1),(0,2),(1,2),(2,2),(3,2),(4,2),(14,2),(15,2),(16,2),(17,2),(18,2),(0,3),(1,3),(2,3),(16,3),(17,3),(18,3),(0,4),(1,4),(2,4),(16,4),(17,4),(18,4),(0,5),(1,5),(17,5),(18,5),(0,6),(1,6),(17,6),(18,6),(0,7),(18,7),(0,8),(18,8),(0,9),(18,9),(0,10),(18,10),(0,11),(18,11),(0,12),(1,12),(17,12),(18,12),(0,13),(1,13),(17,13),(18,13),(0,14),(1,14),(2,14),(16,14),(17,14),(18,14),(0,15),(1,15),(2,15),(16,15),(17,15),(18,15),(0,16),(1,16),(2,16),(3,16),(4,16),(14,16),(15,16),(16,16),(17,16),(18,16),(0,17),(1,17),(2,17),(3,17),(4,17),(5,17),(6,17),(12,17),(13,17),(14,17),(15,17),(16,17),(17,17),(18,17),(0,18),(1,18),(2,18),(3,18),(4,18),(5,18),(6,18),(7,18),(8,18),(9,18),(10,18),(11,18),(12,18),(13,18),(14,18),(15,18),(16,18),(17,18),(18,18)}
center = rg.CENTER_POINT

# function to find the locations around a spot
# removes obstacle locations from output
def around((x,y)):
    offsets = ((0, 1), (1, 0), (0, -1), (-1, 0))
    return set([(x + dx, y + dy) for dx, dy in offsets])-obstacle

# Function to find the closest bot to a specific location by diagonal distance
# Also used to pick the direction closest to the movement goal
def mindist (bots, loc):
    return min(bots,key=lambda x:rg.dist(x, loc))

class Robot:
    def act(self, game):

        # Used to make the code a little more readable
        robots = game.robots

        # Use turn_number to tell if this is the first robot called this turn
        # If so, then clear the list of taken moves
        # The list of taken moves is used to prevent bots from running into each other
        global turn_number, taken_moves
        if game.turn != turn_number:
            turn_number = game.turn
            taken_moves = set()

        # If moving save the location we are moving to
        def moving(loc):
            taken_moves.add(loc)
            return ['move', loc]

        # If staying save the location that we are at
        def staying(act,loc=center):
            taken_moves.add(bot)
            return [act, loc]

        # Function to find bot with the least health
        def minhp (bots):
            return min(bots,key=lambda x:robots[x].hp)


        # Setup basic sets of robots
        me = self.location
        team = set([bot for bot in robots if robots[bot].player_id==self.player_id])

        enemy = set(robots)-team
        adjacent = around(me)


        # adjacent squares with an enemy (enemy is one step away)
        adjacent_enemy = adjacent & enemy

        # adjacent squares with an enemy next to that square
        # excludes square if a teammate is in the square
        # (enemy is two steps away)
        adjacent_enemy2 = set(filter(lambda k:around(k) & enemy, adjacent)) - team

        # set of squares that are safe to move to
        # spawn is bad, and moving into an enemy is bad
        # if an enemy is two steps away it might be attacking towards us
        # excludes teammates to prevent collisions
        safemove = adjacent-adjacent_enemy-adjacent_enemy2-spawn-team-taken_moves
        semisafemove = adjacent-adjacent_enemy-spawn-team-taken_moves
        safemove_withspawn = adjacent-adjacent_enemy-adjacent_enemy2-team-taken_moves

        # Move towards the closest enemy unless leaving spawn or fleeing
        if enemy:
            closest_enemy = mindist(enemy,me)
        else:
            closest_enemy = center


        move = []

        if me in spawn:
            if safemove:
                # Try to get out of spawn...
                move = moving(mindist(safemove,center))
            elif semisafemove:
                # ...even if we have to run into an attacked square
                move = moving(mindist(semisafemove,center))
            elif turn_number%10==0:
                # if it's the spawn turn and we can't leave, suicide
                move = staying('suicide')
            elif safemove_withspawn:
                # can't get out where we are, so lets move around to try to get out
                move = moving(mindist(safemove_withspawn,center))
            elif adjacent_enemy:
                # we're stuck, so we might as well attack
                move = staying('attack',minhp(adjacent_enemy))
        elif adjacent_enemy:
            if attack_damage*len(adjacent_enemy)>=self.hp:
                # nowhere safe to go, so might as well hit the enemy while dying
                move = staying('suicide')
            elif len(adjacent_enemy)>1:
                # there is more than one enemy around us, so let's avoid fighting
                if safemove:
                    move = moving(mindist(safemove,center))
                elif semisafemove:
                    move = moving(mindist(semisafemove,center))

            # No reason to run, so let's attack the weakest neighbor
            # If the enemy would die by collision, let's chase instead
            # This puts pressure on weak bots
            if not move:
                target = minhp(adjacent_enemy)
                if robots[target].hp<5:
                    move = moving(target)
                else:
                    move = staying('attack',target)

        elif adjacent_enemy2 and me not in taken_moves:

            # _____
            # __.X_ <- Enemy
            # __O._ <- Me
            # _____ And nobody else going to move into either square

            # _____
            # _X.O_ <- Enemy, Me
            # _____ And nobody else going to move into the square

            # check to see if someone wants to move into this square
            # if not and there's an enemy two steps away, attack towards
            # pop() chooses an arbitrary direction

            # Find out if this enemy is already engaged, if so join in
            for position_attack in adjacent_enemy2:
                numHelping = 0
                for z in around(position_at):
                    if z in team:
                        numHelping += 1

                numAttacking = 0

                if attack:
                    move = moving(target_enemy)
                else:
                    move = staying('attack',target_enemy)

        if not move:
            # There's no one next to us, so lets go find someone to attack
            if safemove:
                move = moving(mindist(safemove,closest_enemy))
            else:
                # Nowhere safe to move, no one nearby, so let's sit tight
                move = staying('guard')

        return move


