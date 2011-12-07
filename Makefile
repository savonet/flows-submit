DB = liqflows.db

test:
	./test_flows.liq

db:
	cat create_db | sqlite3 $(DB)

redb:
	rm -f $(DB)
	$(MAKE) db

db_perms:
	ssh root@dolebrai.net "cd /home/smimram/savonet/flows; chgrp www-data $(DB); chmod 664 $(DB)"

upload:
	scp liqflows.py dolebrai.net:/home/smimram/savonet/flows