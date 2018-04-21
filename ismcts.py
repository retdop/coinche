# This is a very simple Python 2.7 implementation of the Information Set Monte Carlo Tree Search algorithm.
# The function ismcts(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a 
# state.GetRandomMove() or state.DoRandomRollout() function.
# 
# An example GameState classes for Knockout Whist is included to give some idea of how you
# can write your own GameState to use ismcts in your hidden information game.
# 
# Written by Peter Cowling, Edward Powley, Daniel Whitehouse (University of York, UK) September 2012 - August 2013.
# 
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
# 
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai
# Also read the article accompanying this code at ***URL HERE***

from math import *
import random
from copy import deepcopy


class GameState:
	""" A state of the game, i.e. the game board. These are the only functions which are
		absolutely necessary to implement ismcts in any imperfect information game,
		although they could be enhanced and made quicker, for example by using a 
		GetRandomMove() function to generate a random move during rollout.
		By convention the players are numbered 1, 2, ..., self.number_of_players.
	"""

	def __init__(self):
		self.number_of_players = 4
		self.player_to_move = 1

	def get_next_player(self, p):
		""" Return the player to the left of the specified player
		"""
		return (p % self.number_of_players) + 1

	def clone(self):
		""" Create a deep clone of this game state.
		"""
		st = GameState()
		st.player_to_move = self.player_to_move
		return st

	def clone_and_randomize(self, observer):
		""" Create a deep clone of this game state, randomizing any information not visible to the specified observer player.
		"""
		return self.clone()

	def do_move(self, move):
		""" update a state by carrying out the given move.
			Must update player_to_move.
		"""
		self.player_to_move = self.get_next_player(self.player_to_move)

	def get_moves(self):
		""" Get all possible moves from this state.
		"""
		raise NotImplementedError

	def get_result(self, player):
		""" Get the game result from the viewpoint of player. 
		"""
		raise NotImplementedError

	def __repr__(self):
		""" Don't need this - but good style.
		"""
		pass


atout_values = {
	11: 20,
	9: 14,
	14: 11,
	10: 10,
	13: 4,
	12: 3,
	8: 0,
	7: 0
}
non_atout_values = {
	14: 11,
	10: 10,
	13: 4,
	12: 3,
	11: 2,
	9: 0,
	8: 0,
	7: 0
}


class Card:
	""" A playing card, with rank and suit.
		rank must be an integer between 7 and 14 inclusive (Jack=11, Queen=12, King=13, Ace=14)
		suit must be a string of length 1, one of '♠' (Pique), '♦' (Carreau), '♥' (Coeur) or '♣' (Trèfle)
	"""

	def __init__(self, rank, suit):
		if rank not in range(7, 14 + 1):
			raise Exception("Invalid rank")
		if suit not in ['♠', '♦', '♥', '♣']:
			raise Exception("Invalid suit")
		self.rank = rank
		self.suit = suit

	def value(self, atout):
		if self.suit == atout:
			return atout_values[self.rank]
		else:
			return non_atout_values[self.rank]

	def __repr__(self):
		return "??23456789XJDRA"[self.rank] + self.suit

	def __eq__(self, other):
		return self.rank == other.rank and self.suit == other.suit

	def __ne__(self, other):
		return self.rank != other.rank or self.suit != other.suit


class Coinche(GameState):
	""" A state of the coinche game
		Atout : Pique = 1, Carreau = 2, Coeur = 3, Trèfle = 4
	"""

	def __init__(self, verb):
		""" Initialise the game state. n is the number of players (from 2 to 7).
		"""
		super().__init__()
		self.number_of_players = 4
		self.player_to_move = 0
		self.player_hands = {p: [] for p in range(self.number_of_players)}
		self.atout = None
		self.current_cards = []
		self.current_round = 0
		self.current_scores = [0, 0]
		self.scores = [0, 0]
		self.deal()
		self.verbose = verb

	def clone(self):
		""" Create a deep clone of this game state.
		"""
		st = Coinche(verb=False)
		st.player_to_move = self.player_to_move
		st.player_hands = deepcopy(self.player_hands)
		st.atout = self.atout
		st.current_cards = deepcopy(self.current_cards)
		st.current_round = self.current_round
		st.current_scores = deepcopy(self.current_scores)
		st.scores = deepcopy(self.scores)
		return st

	def clone_and_randomize(self, observer):
		""" Create a deep clone of this game state, randomizing any information not visible to the specified observer player.
		"""
		st = self.clone()

		# The observer can see his own hand and the cards in the current trick,
		# and can remember the cards played in previous tricks
		# The observer can't see cards in other players hands
		unseen_cards = []
		for p in range(self.number_of_players):
			if p != observer:
				unseen_cards += st.player_hands[p]
		# seen_cards = [card for card in st.get_card_deck() if card not in unseen_cards]

		# deal the unseen cards to the other players
		random.shuffle(unseen_cards)
		for p in range(st.number_of_players):
			if p != observer:
				# deal cards to player p
				# Store the size of player p's hand
				num_cards = len(self.player_hands[p])
				# Give player p the first num_cards unseen cards
				st.player_hands[p] = unseen_cards[: num_cards]
				# Remove those cards from unseen_cards
				unseen_cards = unseen_cards[num_cards:]

		return st

	@staticmethod
	def get_card_deck():
		""" Construct a standard deck of 32 = 4 * 8 cards.
		"""
		return [Card(rank, suit) for rank in range(7, 14 + 1) for suit in ['♠', '♦', '♥', '♣']]

	@staticmethod
	def sort_hand(hand):
		""" Sorts hand according to order '♠', '♦', '♥', '♣' for visibility
		"""
		sorted_hand = []
		for suit in ['♠', '♦', '♥', '♣']:
			sorted_hand += [card for card in hand if card.suit == suit]
		return sorted_hand

	def score(self):
		"""
			Calculates the total scores of the four cards
		"""
		score = 0
		for (player, card) in self.current_cards:
			score += card.value(self.atout)
		if not(len(self.player_hands[self.player_to_move])):
			score += 10  # 10 de der
		return score

	def deal(self):
		""" Reset the game state for the beginning of a new round, and deal the cards.
		"""
		# self.discards = []
		# self.currentTrick = []
		# self.tricksTaken = {p: 0 for p in range(self.number_of_players)}
		self.current_round += 1
		self.player_to_move = 0
		self.current_cards = []
		self.scores[0] += self.current_scores[0]
		self.scores[1] += self.current_scores[1]
		# print(self.scores)
		self.current_scores = [0, 0]
		
		# Construct a deck, shuffle it, and deal it to the players
		deck = self.get_card_deck()
		random.shuffle(deck)
		for p in range(self.number_of_players):
			self.player_hands[p] = self.sort_hand(deck[:8])
			deck = deck[8:]

		# Choose the trump suit for this round
		self.atout = random.choice(['♠', '♦', '♥', '♣'])

	def get_next_player(self, p):
		""" Return the player to the left of the specified player
		"""
		return (p + 1) % self.number_of_players

	def do_move(self, move):
		""" update a state by carrying out the given move.
			Must update player_to_move.
		"""
		# if self.verbose:
		# 	print('----------------------')
		# 	print('New move for root board')
		# 	print(move)
		# 	print(self.current_cards)
		# print('new move', move, 'by', self.player_to_move)
		# Store the played card in the current trick
		# print(len(self.current_cards))
		if len(self.current_cards) < 4:
			self.current_cards.append((self.player_to_move, move))
		else:
			self.current_cards = [(self.player_to_move, move)]

		# Remove the card from the player's hand
		self.player_hands[self.player_to_move].remove(move)

		# Find the next player
		self.player_to_move = self.get_next_player(self.player_to_move)
		# print('next player', self.player_to_move)
		# If the next player has already played in this trick, then the trick is over
		# print('yoooo', self.current_cards)
		if len(self.current_cards) > 3:

			trick_winner = self.get_trick_winner()
			# update the game state
			self.player_to_move = trick_winner
			# print(trick_winner)
			# print('yo', self.current_cards, self.player_to_move, trick_winner)
			self.current_scores[trick_winner % 2] += self.score()
			self.current_cards = []
		# If the next player's hand is empty, this round is over
		# print(self.player_hands[self.player_to_move])
		# if not self.player_hands[self.player_to_move]:
		# print('Round finished')
		# self.deal()

	def get_moves(self):
		""" Get all possible moves from this state.
		"""
		hand = self.player_hands[self.player_to_move]
		if not len(self.current_cards):
			# print(1, hand)
			return hand
		else:
			(leader, lead_card) = self.current_cards[0]
			# Must follow suit if it is possible to do so
			cards_in_suit = [card for card in hand if card.suit == lead_card.suit]
			cards_in_atout = [card for card in hand if card.suit == self.atout]
			if cards_in_suit:
				# print(2, cards_in_suit)
				return cards_in_suit
			elif cards_in_atout:
				# Can't follow suit, so can play only atout
				# print(3, cards_in_suit)
				return cards_in_atout
			else:
				# Can't follow suit or play atout, so can play anything
				# print(4, cards_in_suit)
				return hand

	def get_result(self, player):
		""" Get the game result from the viewpoint of player. 
		"""
		# return 0 if (self.knockedOut[player]) else 1
		return self.current_scores[player % 2]

	def get_trick_winner(self):
		""" Sort the four cards
		"""
		(leader, lead_card) = self.current_cards[0]
		atout_plays = [(player, card) for (player, card) in self.current_cards if card.suit == self.atout]
		suited_plays = [(player, card) for (player, card) in self.current_cards if card.suit == lead_card.suit]

		if atout_plays:
			sorted_plays = sorted(atout_plays, key=lambda move: move[1].value(self.atout))
		else:
			sorted_plays = sorted(suited_plays, key=lambda move: move[1].value(self.atout))
		trick_winner = sorted_plays[-1][0]
		return trick_winner

	def __repr__(self):
		""" Return a human-readable representation of the state
		"""
		result = "Round %i" % self.current_round
		result += " | Player to move : %i " % self.player_to_move
		for p in range(4):
			result += "\n | P%i: " % p
			result += ",".join(str(card) for card in self.player_hands[p])
		result += " | Current cards: %s" % self.current_cards
		result += " | Atout: %s" % self.atout
		result += " | Scores: %s" % self.scores
		result += " | Current scores: %s" % self.current_scores
		# result += ",".join(("%i:%s" % (player, card)) for (player, card) in self.currentTrick)
		# result += "]"

		return result


class Node:
	""" A node in the game tree. Note wins is always from the viewpoint of player_just_moved.
	"""

	def __init__(self, move=None, parent=None, player_just_moved=None):
		self.move = move  # the move that got us to this node - "None" for the root node
		self.parentNode = parent  # "None" for the root node
		self.child_nodes = []
		self.wins = 0
		self.visits = 0
		self.avails = 1
		self.player_just_moved = player_just_moved  # the only part of the state that the Node needs later

	def get_untried_moves(self, legal_moves):
		""" Return the elements of legal_moves for which this node does not have children.
		"""

		# Find all moves for which this node *does* have children
		tried_moves = [child.move for child in self.child_nodes]

		# Return all moves that are legal but have not been tried yet
		return [move for move in legal_moves if move not in tried_moves]

	def ucb_select_child(self, legal_moves, exploration=0.7):
		""" Use the UCB1 formula to select a child node, filtered by the given list of legal moves.
			exploration is a constant balancing between
			exploitation and exploration, with default value 0.7 (approximately sqrt(2) / 2)
		"""

		# Filter the list of children by the list of legal moves
		legal_children = [child for child in self.child_nodes if child.move in legal_moves]

		# Get the child with the highest UCB score
		s = max(legal_children,
				key=lambda c: float(c.wins) / float(c.visits) + exploration * sqrt(log(c.avails) / float(c.visits)))

		# update availability counts -- it is easier to do this now than during backpropagation
		for child in legal_children:
			child.avails += 1

		# Return the child selected above
		return s

	def add_child(self, m, p):
		""" Add a new child node for the move m.
			Return the added child node
		"""
		n = Node(move=m, parent=self, player_just_moved=p)
		self.child_nodes.append(n)
		return n

	def update(self, terminal_state):
		""" update this node - increment the visit count by one, and increase the win count by the
		result of terminal_state for self.player_just_moved.
		"""
		self.visits += 1
		if self.player_just_moved is not None:
			self.wins += terminal_state.get_result(self.player_just_moved)

	def __repr__(self):
		return "[M:%s W/V/A: %4i/%4i/%4i]" % (self.move, self.wins, self.visits, self.avails)

	def tree_to_string(self, indent):
		""" Represent the tree as a string, for debugging purposes.
		"""
		s = self.indent_string(indent) + str(self)
		for c in self.child_nodes:
			s += c.tree_to_string(indent + 1)
		return s

	@staticmethod
	def indent_string(indent):
		s = "\n"
		for i in range(1, indent + 1):
			s += "| "
		return s

	def children_to_string(self):
		s = ""
		for c in self.child_nodes:
			s += str(c) + "\n"
		return s


def ismcts(rootstate, itermax, verbose=False):
	""" Conduct an ismcts search for itermax iterations starting from rootstate.
		Return the best move from the rootstate.
	"""

	rootnode = Node()

	for i in range(itermax):
		# print(i)
		node = rootnode

		# Determinize
		state = rootstate.clone_and_randomize(rootstate.player_to_move)

		# Select
		while state.get_moves() != [] and node.get_untried_moves(
				state.get_moves()) == []:  # node is fully expanded and non-terminal
			node = node.ucb_select_child(state.get_moves())
			# print('select')
			state.do_move(node.move)
		# print('000', state.get_moves())
		# Expand
		untried_moves = node.get_untried_moves(state.get_moves())
		if untried_moves:  # if we can expand (i.e. state/node is non-terminal)
			m = random.choice(untried_moves)
			player = state.player_to_move
			# print('untried_moves')
			state.do_move(m)
			node = node.add_child(m, player)  # add child and descend tree

		# Simulate
		while state.get_moves():  # while state is non-terminal
			# print('move simulation')
			# print(state.current_cards)
			state.do_move(random.choice(state.get_moves()))

		# Backpropagate
		while node is not None:  # backpropagate from the expanded node and work back to the root node
			node.update(state)
			node = node.parentNode

	# Output some information about the tree - can be omitted
	if verbose:
		print(rootnode.tree_to_string(0))
	else:
		print(rootnode.children_to_string())

	return max(rootnode.child_nodes, key=lambda c: c.visits).move  # return the move that was most visited


def play_game():
	""" Play a sample game between four ismcts players.
	"""
	state = Coinche(verb=True)

	while state.get_moves():
		print(state)
		# Use different numbers of iterations (simulations, tree nodes) for different players
		if state.player_to_move == 1:
			m = ismcts(rootstate=state, itermax=10, verbose=True)
		else:
			m = ismcts(rootstate=state, itermax=10, verbose=True)
		print("Best Move: " + str(m) + "\n")
		state.do_move(m)

	for p in range(state.number_of_players):
		print("Player " + str(p), state.get_result(p))


if __name__ == "__main__":
	play_game()
