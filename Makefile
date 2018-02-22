TIFDIR=images
REPORTDIR=summary
ORIGDIR=paths
SHAPEDIR=gen/shapes
PATHDIR=gen/paths
LOGDIR=gen/flightlogs
BUFFER=5

ALTGEN=python pathplan/make_shapes.py
SHAPEGEN=python pathplan/make_shapes.py
PATHGEN=python pathplan/path_planner.py 
FLIGHTGEN=python pathplan/sitl.py 5760
PARSEBIN=python pathplan/parse_bin.py
REPORTGEN=python pathplan/eval_path.py

%.report: $(TIFDIR)/%.tif $(LOGDIR)/%.flight.json $(PATHDIR)/%.path.json
	$(REPORTGEN) $^

$(LOGDIR)/%.flight.json: $(PATHDIR)/%.path.json killsitl startsitl
	echo "STARTED FLIGHT TARGET"
	$(FLIGHTGEN) $<
	mkdir -p $(LOGDIR)/$<
	cp logs/*.BIN $(LOGDIR)/$<
	rm -rf logs terrain eeprom.bin
	$(PARSEBIN) $(LOGDIR)/$<

$(PATHDIR)/%.path.json: $(ORIGDIR)/%.json $(SHAPEDIR)/%.shapes $(SHAPEDIR)/%.alt.json
	$(PATHGEN) $^ $@ $(BUFFER)

$(SHAPEDIR)/%.shapes: $(TIFDIR)/%.tif
	$(SHAPEGEN) $^ $(SHAPEDIR)

$(SHAPEDIR)/%.alt.json: $(TIFDIR)/%.tif
	$(ALTGEN) $^ $(SHAPEDIR)
	


killsitl:
	kill -9 $(shell lsof -t -i:5760)

startsitl:
	~/.dronekit/sitl/copter-3.3/apm --wipe --home=32.884271,-117.235120,584,149 --model=quad &
