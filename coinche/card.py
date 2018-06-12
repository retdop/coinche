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

suits = ['♠', '♦', '♥', '♣']
ranks = list(range(7, 14 + 1))


class Card:
	""" A playing card, with rank and suit.
		rank must be an integer between 7 and 14 inclusive (Jack=11, Queen=12, King=13, Ace=14)
		suit must be a string of length 1, one of '♠' (Pique), '♦' (Carreau), '♥' (Coeur) or '♣' (Trèfle)
	"""

	def __init__(self, rank, suit):
		if rank not in ranks:
			raise Exception("Invalid rank")
		if suit not in suits:
			raise Exception("Invalid suit")
		self.rank = rank
		self.suit = suit
		self.index = len(ranks) * suits.index(self.suit) + ranks.index(self.rank)

	def value(self, atout):
		if self.suit == atout:
			return atout_values[self.rank]
		else:
			return non_atout_values[self.rank]

	def __repr__(self):
		return "???????789XJDRA"[self.rank] + self.suit

	def __eq__(self, other):
		return self.rank == other.rank and self.suit == other.suit

	def __ne__(self, other):
		return self.rank != other.rank or self.suit != other.suit

