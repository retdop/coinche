from copy import deepcopy
from card import Card
import random


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


class Coinche(GameState):
	""" A state of the coinche game
		Atout : Pique = 1, Carreau = 2, Coeur = 3, Trèfle = 4
	"""

	def __init__(self, verbose):
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
		self.random_deal()
		self.verbose = verbose
		self.move_history = []

	def clone(self):
		""" Create a deep clone of this game state.
		"""
		st = Coinche(verbose=False)
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
		# TODO shuffle cards according to some proba distribution based on prior moves
		# deal the unseen cards to the other players
		random.shuffle(unseen_cards)
		for p in range(st.number_of_players):
			if p != observer:
				# deal cards to player p
				# Store the size of player p's hand
				num_cards = len(self.player_hands[p])
				# Give player p the first num_cards unseen cards
				st.player_hands[p] = unseen_cards[:num_cards]
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
		if not (len(self.player_hands[self.player_to_move])):
			score += 10  # 10 de der
		return score

	def random_deal(self):
		""" Reset the game state for the beginning of a new round, and deal the cards.
		"""
		self.current_round += 1
		self.player_to_move = random.randint(0, 3)
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

	def spec_deal(self):
		""" Reset the game state for the beginning of a new round, and deal the cards according to specific deal
		"""
		self.current_round += 1
		self.player_to_move = 0

		# updates cards and scores
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
		self.moves_history.append(move)

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
	# self.random_deal()

	def get_moves(self):
		""" Get all possible moves from this state.
		"""
		hand = self.player_hands[self.player_to_move]
		if not len(self.current_cards):
			# print(1, hand)
			return hand
		else:
			(leader, lead_card) = self.current_cards[0]

			atout_played = [card for (player, card) in self.current_cards if card.suit == self.atout]
			sorted_atout_played = sorted(atout_played, key=lambda x: x.value(self.atout))

			cards_in_suit = [card for card in hand if card.suit == lead_card.suit]
			cards_in_atout = [card for card in hand if card.suit == self.atout]
			if cards_in_suit:
				# print(2, cards_in_suit)
				return cards_in_suit
			elif cards_in_atout:
				# Can't follow suit, so can play only atout
				# print(3, cards_in_suit)
				if not (len(sorted_atout_played)):
					return cards_in_atout
				better_atout_cards = [card for card in cards_in_atout
									  if card.value(self.atout) > sorted_atout_played[-1].value(self.atout)]
				if len(better_atout_cards):
					return better_atout_cards
				else:
					return cards_in_atout
			else:
				# Can't follow suit or play atout, so can play anything
				# print(4, cards_in_suit)
				return hand

	def get_result(self, player):
		""" Get the game result from the viewpoint of player.
		"""
		# return 0 if (self.knockedOut[player]) else 1
		return self.current_scores[player % 2] / 162.

	# return self.current_scores[player % 2] > self.current_scores[(player + 1) % 2]

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
		result += "\n | Player to move : %i " % self.player_to_move
		for p in range(4):
			result += "\n | P%i: " % p
			result += ", ".join(str(card) for card in self.player_hands[p])
		result += "\n | Current cards: %s" % ", ".join(str(card) for card in self.current_cards)
		result += "\n | Current cards score: %s" % self.score()
		result += "\n | Atout: %s" % self.atout
		result += "\n | Scores: %s" % self.scores
		result += "\n | Current scores: %s" % self.current_scores

		return result
