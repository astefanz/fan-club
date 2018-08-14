with open('generated.py', 'w') as f:

	arrayRow = 0
	arrayColumn = 0

	moduleIndex = 0

	for modularRow in range(12):
		
		for modularColumn in range(12):
			
			f.write(
				"\n\t(\n\t\t"\
				"{},\n\t\t"\
				"{},\n\t\t"\
				"{},\n\t\t"\
				"3,\n\t\t"\
				"3,\n\t\t"\
				"18,\n\t\t"\
				"''\n\t),".format(moduleIndex, modularRow*3, modularColumn*3)
			)

			moduleIndex += 1
		
		

