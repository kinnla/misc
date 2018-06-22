"""
This program reverse-engineers quotes from betting sites
and computes a list of top bets according to the kicktipp-rules
quotes can be found at www.bet365.com
samles below for Nigeria vs. Island, Fri Jun 22nd, 2018, 4:26 pm
"""

import sys

# dictionary of the quotes for exact result bets
# to be edited for the given game 
BETTING_QUOTES = {
	(1,0) : 7.5,
	(2,0) : 15,
	(2,1) : 13,
	(3,0) : 41,
	(3,1) : 34,
	(3,2) : 51,
	(4,0) : 81,
	(4,1) : 81,
	(4,2) : 151,
	(4,3) : 351,
	(5,0) : 501,
	(5,1) : 351,
	(0,0) : 6.5,
	(1,1) : 6.5,
	(2,2) : 21,
	(3,3) : 101,
	(0,1) : 6.5,
	(0,2) : 12,
	(1,2) : 12,
	(0,3) : 29,
	(1,3) : 29,
	(2,3) : 51,
	(0,4) : 67,
	(1,4) : 67,
	(2,4) : 126,
	(3,4) : 351,
	(0,5) : 251,
	(1,5) : 251,
	(2,5) : 501
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
	prob = {bet: 1.0/quote for bet, quote in BETTING_QUOTES.items()}
	p_sum = sum(prob.values())
	prob = {bet: p / p_sum for bet, p in prob.items()}

	# compute the average points for each bet 
	averages = {bet: sum([get_points(result, bet) * p for result, p in prob.items()]) for bet in prob}

	# print the bets from best to worst
	for bet, av in sorted(averages.items(), key=lambda x: x[1], reverse = True):
		print('{}:{} -- {av}'.format(bet[0], bet[1], av=round(av, 2)))


if __name__ == "__main__":
    main(sys.argv)
