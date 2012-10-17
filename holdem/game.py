from holdem.different import *
from copy import deepcopy

class Game(object):
    """
    Implementation of game abstraction.
    """
    def __init__(self, table):
        self.table = table
        self.players = table.players
        self.diler = table.diler
        self.banks = []
        self.sbl = table.sbl
        self.bbl = table.bbl
        self.sits = table.sits
        self.but_pos = table.but_pos
        self.game_info = {
            'cards': [], # Contains list of cards opened by diler
                        # for each round.
            'moves': [], # Contains list of rounds. Each round - list of laps.
                        # Each lap - list of moves.
            'sbl': self.sbl, # Small blind value
            'bbl': self.bbl, # Big blind value
            'but_pos': self.but_pos, # Button position
             # Info about bankrolls before game started
            'bankrolls': dict([(player.plid, player.bankroll)\
                               for player in self.players])
            }
   
    def play_game(self):
        """Implementation of game flow"""
        # Sort players accroding to button position
        func = lambda player: player.sit if player.sit > self.but_pos \
                                            else player.sit + len(self.sits)
        players.sort(key = func)
        # Give each player two cards
        for player in self.players:
            player.cards = self.diler.give_two_cards()

        current_bank = {'value': 0, 'player_ids': None}
        # Start a rounds of bets
        for round_no in range(4):
            self.game_info['moves'].append([[]])
            self.game_info['cards'].append([])
            if round_no == 1:
                self.game_info['cards'][round_no] = self.diler.give_three_cards()
            elif round_no == 2 or round_no == 3:
                self.game_info['cards'][round_no] = self.diler.give_card()
            lap_no = 0
    
            # Show cards handed out by diler
            self.table.display_cards(self.game_info)

            if len([player for player in self.players \
                                if player.bankroll != 0) < 2:
                continue

            while True:
                self.game_info['moves'][round_no].append([[]])
                allins = []
                allin_ids = set([])
                for player in self.players:
                    if player.plid not in allin_ids:
                        move = player.make_move(self.game_info)
                    else: 
                        continue
                    # Show player's move
                    self.table.display_move(self.game_info)
                    self.game_info['moves'][round_no][lap_no].append(move)
                    bet = move['decision'].value
                    player.bankroll -= bet
                    if move.dec_type == DecisionType.FOLD:
                        self.players.remove(player)
                        continue
                    # Handling a case when player went all-in
                    if player.bankroll == 0:
                        current_bank['player_ids'] = \
                            [player.plid for player in self.players]
                        self.banks[round_no].append(deepcopy(current_bank))
                        current_bank = {'value': 0, 'player_ids': None}
                        allins.append(bet)
                        allin_ids.add(player.plid)
                    # Handle multiple banks situation (one or more allins) 
                    if len(allins) > 0:
                        diff = 0
                        for i, allin in enumerate(allins):
                            diff = allin - diff
                            self.banks[round_no][i]['value'] += diff 
                            bet -= diff
                                
                    current_bank['value'] += bet

                # Checking end of round condition
                if self.__round_finished__(self.game_info, len(allins)):
                    break
                lap_no += 1
                self.game_info[round_no]['laps'].append([])
    
            # Checking end of game condition
            if len(self.players) == 1:
                break

        # Finalize current bank and add it to banks list
        current_bank['player_ids'] = \
            [player.plid for player in self.players]
        self.banks[round_no].append(deepcopy(current_bank))
        
        # Determine winners
        winner_ids = self.__determine_winners__()

        for round_no in range(3):
            for bank in self.banks[round_no]:
                # Filter out players that haven't finished a game
                bank['player_ids'] = list(set(bank['player_ids']) & \
                                       set(winner_ids))
                
                # Share bank among winners
                for player_id in bank['player_ids']:
                    self.__player_by_id__(player_id).bankroll \
                        += bank['value'] / len(bank['player_ids'])

    def __player_by_id__(self, plid):
        """
        Returns a player instance given it's id.
        """
        return filter(lambda pl: True if pl.plid = plid \
                                        else False, self.players)[0] 

    def __determine_winners__(self):
        """
        Returns a list of winners ids.
        """
        cards_on_table = []
        # Form a list of cards handed out by diler
        for cards in self.game_info['cards']
            cards_on_table.extend(cards)
        # Making list of tuples with players ids and their best combinations
        pl_combs = [(pl.plid, self.diler.best_comb(cards_on_table + pl.cards)) \
                    for pl in self.players]
        # Defining sorting function for list of tuples mentioned above
        sort_func = lambda comb1, comb2: \
                        self.diler.compare_combs(comb1[1], comb2[1])
        # Sort list of tuples mentioned above, preparing to determine winners
        pl_combs.sort(cmp = sort_func, reverse = True)
        winners_ids = []
        # Determing winners ids
        for comb in pl_combs:
            if self.diler.compare_combs(comb[1], combs[0][1]) == 0:
                winners_ids.append(comb[0])
        

    def __round_finished__(self, lap, allins_cnt):
        """
        Returns true if all players made equal bets, false otherwise.
        """
        flap = self.__remove_folds__(lap)
        # Returns False if some players haven't made their bets 
        if len(flap) < len(self.players) - allins_cnt:
            return False 

        first_move = flap[0]
        for move in flap:
            if move['decision'].value != first_move['decision'].value:
                return False
        return True
            
    def __remove_folds__(self, lap):
        """
        Removes moves with "fold" type from moves list.
        Returns resulting lap info.
        """
        clap = deepcopy(lap)
        for move in clap:
            if move['decision'].des_type == DecisionType.FOLD:
                clap.remove(move)
        return clap 