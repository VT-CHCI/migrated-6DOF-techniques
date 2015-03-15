def inBounds (selection, match, offset):
	matches = False
	
	if (selection[0] < match[0] + offset) and (selection[0] > match[0] - offset) and (selection[1] < match[1] + offset) and (selection[1] > match[1] - offset) and (selection[2] < match[2] + offset) and (selection[2] > match[2] - offset):
		matches = True
		
	return matches
	