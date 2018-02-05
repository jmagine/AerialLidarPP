
runsitl:
	docker run -it -v logs:/home/logs -p 5760:5760 -p 5501:5501 tritonuas/plane.rascal
uploadmission:
	mavproxy.py --master=tcp:127.0.0.1:5760 --cmd="wp load test_mission.txt; arm throttle; mode auto;"
