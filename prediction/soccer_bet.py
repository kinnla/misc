import sys

MAX_GOALS = 6

def get_points(actual_result, bet):
	
	# check for exact prediction
	if actual_result == bet:
		return 4
	
	x1,y1 = actual_result
	x2,y2 = bet
	
	# check for draw prediction
	if x1==y1 and x2==y2:
		return 2

	# check for goal difference
	if x1-y1 == x2-y2:
		return 3

	# check for tendency
	if (x1-y1) * (x2-y2) > 0:
		return 2

	# no points at all
	return 0

def main(argv):

	# list of lists, storing the quotes for exact results
	# quotes for a specific game can be achieved from www.bet365.com
	# samles below are for Nigeria v Island, Fri Jun 22nd, 2018, 4:26 pm
	quotes = [[0 for x in range(MAX_GOALS)] for y in range(MAX_GOALS)]

	# lists of lists, storing the probability for each result to happen
	probabilities = [[0 for x in range(MAX_GOALS)] for y in range(MAX_GOALS)]

	# lists of lists, storing the probability for each result to happen
	average = [[0 for x in range(MAX_GOALS)] for y in range(MAX_GOALS)]

	# 1st team wins
	quotes[1][0] = 7.5
	quotes[2][0] = 15
	quotes[2][1] = 13
	quotes[3][0] = 41
	quotes[3][1] = 34
	quotes[3][2] = 51
	quotes[4][0] = 81
	quotes[4][1] = 81
	quotes[4][2] = 151
	quotes[4][3] = 351
	quotes[5][0] = 501
	quotes[5][1] = 351

	# draw
	quotes[0][0] = 6.5
	quotes[1][1] = 6.5
	quotes[2][2] = 21
	quotes[3][3] = 101

	# 2nd team wins
	quotes[0][1] = 6.5
	quotes[0][2] = 12
	quotes[1][2] = 12
	quotes[0][3] = 29
	quotes[1][3] = 29
	quotes[2][3] = 51
	quotes[0][4] = 67
	quotes[1][4] = 67
	quotes[2][4] = 126
	quotes[3][4] = 351
	quotes[0][5] = 251
	quotes[1][5] = 251
	quotes[2][5] = 501

	# convert to reciprocal values, so we have probabilities
	# also sum up the probabilities
	probability_sum = 0
	for x in range(MAX_GOALS):
		for y in range(MAX_GOALS):
			if quotes[x][y] > 0:
				probabilities[x][y] = 1./quotes[x][y]
				probability_sum += probabilities[x][y]

	# error correction (profit margin) of the probabilities
	for x in range(MAX_GOALS):
		for y in range(MAX_GOALS):
			probabilities[x][y] /= probability_sum 

	# compute average
	for x1 in range(MAX_GOALS):
		for y1 in range(MAX_GOALS):
			for x2 in range(MAX_GOALS):
				for y2 in range(MAX_GOALS):
					average[x2][y2] += get_points((x1,y1),(x2,y2)) * probabilities[x1][y1]

	# find the best average
	for x in range(MAX_GOALS):
		for y in range(MAX_GOALS):
			print("{x}:{y} -- {av}".format(x=x,y=y,av=round(average[x][y],2)))

if __name__ == "__main__":
    main(sys.argv)
