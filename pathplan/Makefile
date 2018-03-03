startsitl:
	~/.dronekit/sitl/copter-3.3/apm --wipe --home=32.884271,-117.235120,584,149 --model=quad &
killsitl:
	kill -9 $(shell lsof -t -i:5760)
	
genucsd: 
	python path_planner.py --proj ucsd-test.json ucsd-dsm.tif 5

genucsdnotiff: 
	python path_planner.py --gen --proj ucsd-test.json ucsd-dsm.tif 5

benchmarkucsd: killsitl startsitl 
	python sitl.py 5760 results-ucsd-test.json
	cp logs/1.BIN bin/ucsd.BIN
	python eval_path.py ucsd.BIN ucsd-test.json ucsd.shapes ucsd.alt.json

benchmarkall: benchmarkucsd

clean:
