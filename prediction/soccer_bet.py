"""
This program reverse-engineers quotes from betting sites
and computes a list of top bets according to the kicktipp-rules
quotes can be found at www.bet365.com
samles below for Nigeria vs. Island, Fri Jun 22nd, 2018, 4:26 pm
"""

import sys

#TENDENCY_QUOTES = (4.5, 2.7, 2.3)

# dictionary of the quotes for exact result bets
# to be edited for the given game 
EXACT_QUOTES = {
	(1,0) : 41,
	(2,0) : 81,
	(2,1) : 41,
	(3,0) : 351,
	(3,1) : 126,
	(3,2) : 101,
	# (4,0) : 151,
	# (4,1) : 151,
	# (4,2) : 201,
	# (4,3) : 501,
	# (5,0) : 451,
	# (5,1) : 351,
	# (5,2) : 501,

	(0,0) : 17,
	(1,1) : 15,
	(2,2) : 34,
	(3,3) : 101,

	(0,1) : 8.5,
	(0,2) : 7,
	(1,2) : 10,
	(0,3) : 7.5,
	(1,3) : 12,
	(2,3) : 34,
	(0,4) : 11,
	(1,4) : 17,
	(2,4) : 41,
	(3,4) : 126,
	(0,5) : 19,
	(1,5) : 29,
	(2,5) : 67,
	(3,5) : 251,
	(1,6) : 51,
	(0,6) : 41,
	(2,6) : 126,
	(3,6) : 501,
	(0,7) : 67,
	(1,7) : 101,
	(2,7) : 301,
	(0,8) : 151,
	(1,8) : 251,
	(0,9) : 501,
}

def get_points(result, bet):
	"""Get the points for a bet based on the actual result."""
	
	x1,y1 = result
	x2,y2 = bet

	if result == bet: return 4	        # correct result
	if x1==y1 and x2==y2: return 2      # draw
	if x1-y1 == x2-y2: return 3         # correct goal difference
	if (x1-y1) * (x2-y2) > 0: return 2  # correct tendency
	return 0                            # all wrong


def main(argv):

	# compute prob and correct the error (profit margin)
	prob = {bet: 1.0/quote for bet, quote in EXACT_QUOTES.items()}
	p_sum = sum(prob.values())
	prob = {bet: p / p_sum for bet, p in prob.items()}

	# compute the average points for each bet 
	averages = {bet: sum([get_points(result, bet) * p for result, p in prob.items()]) for bet in prob}

	# print the bets from best to worst
	for bet, av in sorted(averages.items(), key=lambda x: x[1], reverse = True):
		print('{}:{} -- {av}'.format(bet[0], bet[1], av=round(av, 2)))


if __name__ == "__main__":
    main(sys.argv)
